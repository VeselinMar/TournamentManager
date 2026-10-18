"""Anonymous visitor and sponsor statistics."""
import io
from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from PIL import Image

from analytics.models import PageViewCount, SponsorDailyStats
from analytics.services import record_page_view, record_sponsor_click, tournament_report
from sponsors.models import SponsorBanner

BROWSER = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/129.0 Mobile Safari/537.36"


def _png():
    buffer = io.BytesIO()
    Image.new("RGB", (40, 20), "blue").save(buffer, "PNG")
    return SimpleUploadedFile("logo.png", buffer.getvalue(), content_type="image/png")


@pytest.fixture
def sponsors(tournament):
    return [
        SponsorBanner.objects.create(tournament=tournament, name="Pave", link_url="https://pave.example", image=_png()),
        SponsorBanner.objects.create(tournament=tournament, name="No Site", image=_png()),
    ]


def _track(client, tournament, section="schedule", agent=BROWSER, **extra):
    return client.post(
        reverse("api-track-view", args=[tournament.slug]),
        data={"section": section},
        content_type="application/json",
        HTTP_USER_AGENT=agent,
        **extra,
    )


# ---------------------------------------------------------------------------
# Beacon
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_view_counts_section_and_sponsor_impressions(client, tournament, sponsors):
    assert _track(client, tournament).status_code == 204
    _track(client, tournament)
    _track(client, tournament, section="bracket")

    views = {row.section: row.views for row in PageViewCount.objects.filter(tournament=tournament)}
    assert views == {"schedule": 2, "bracket": 1}
    assert {s.sponsor.name: s.impressions for s in SponsorDailyStats.objects.all()} == {"Pave": 3, "No Site": 3}


@pytest.mark.django_db
def test_unknown_section_is_rejected(client, tournament):
    response = _track(client, tournament, section="admin")
    assert response.status_code == 400
    assert not PageViewCount.objects.exists()


@pytest.mark.django_db
def test_unknown_tournament_is_404(client):
    response = client.post("/api/tournaments/nope/track/", {"section": "schedule"},
                           content_type="application/json", HTTP_USER_AGENT=BROWSER)
    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize("agent", ["", "Googlebot/2.1", "WhatsApp/2.23", "facebookexternalhit/1.1", "curl/8.4"])
def test_bots_and_previews_are_not_counted(client, tournament, sponsors, agent):
    assert _track(client, tournament, agent=agent).status_code == 204
    assert not PageViewCount.objects.exists()
    assert not SponsorDailyStats.objects.exists()


@pytest.mark.django_db
def test_logged_in_organiser_can_send_beacon_without_csrf(user, tournament):
    """The public page has no CSRF token; the beacon must still work for logged-in users."""
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(user)
    assert _track(csrf_client, tournament).status_code == 204
    assert PageViewCount.objects.get().views == 1


@pytest.mark.django_db
def test_nothing_personal_is_stored(client, tournament, sponsors):
    _track(client, tournament, REMOTE_ADDR="203.0.113.7")
    stored = [
        str(value)
        for model in (PageViewCount, SponsorDailyStats)
        for row in model.objects.values()
        for value in row.values()
    ]
    assert not any("203.0.113.7" in v or "Mozilla" in v for v in stored)


@pytest.mark.django_db
def test_beacon_is_rate_limited(client, tournament, settings):
    from django.core.cache import cache
    cache.clear()
    responses = [_track(client, tournament).status_code for _ in range(62)]
    cache.clear()
    assert responses.count(204) == 60 and responses[-1] == 429


# ---------------------------------------------------------------------------
# Sponsor clicks
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_click_counts_and_redirects(client, sponsors):
    pave = sponsors[0]
    response = client.get(reverse("sponsor-click", args=[pave.pk]), HTTP_USER_AGENT=BROWSER)

    assert response.status_code == 302
    assert response["Location"] == "https://pave.example"
    assert "no-cache" in response["Cache-Control"] or "max-age=0" in response["Cache-Control"]
    assert SponsorDailyStats.objects.get(sponsor=pave).clicks == 1


@pytest.mark.django_db
def test_bot_click_redirects_without_counting(client, sponsors):
    response = client.get(reverse("sponsor-click", args=[sponsors[0].pk]), HTTP_USER_AGENT="Bingbot")
    assert response.status_code == 302
    assert not SponsorDailyStats.objects.exists()


@pytest.mark.django_db
def test_sponsor_without_website_has_no_redirect(client, sponsors):
    response = client.get(reverse("sponsor-click", args=[sponsors[1].pk]), HTTP_USER_AGENT=BROWSER)
    assert response.status_code == 404


@pytest.mark.django_db
def test_meta_api_links_sponsors_through_click_counter(client, tournament, sponsors):
    data = client.get(reverse("api-tournament-meta", args=[tournament.slug])).json()
    by_name = {s["name"]: s for s in data["sponsors"]}

    assert by_name["Pave"]["click_url"] == reverse("sponsor-click", args=[sponsors[0].pk])
    assert by_name["Pave"]["link_url"] == "https://pave.example"
    assert by_name["No Site"]["click_url"] is None


# ---------------------------------------------------------------------------
# Organiser report
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_report_totals(tournament, sponsors):
    day1, day2 = date(2026, 6, 20), date(2026, 6, 21)
    for _ in range(4):
        record_page_view(tournament, "schedule", date=day1)
    record_page_view(tournament, "leaderboard", date=day2)
    record_sponsor_click(sponsors[0], date=day1)

    report = tournament_report(tournament)

    assert report["total_views"] == 5
    assert report["by_section"][0] == {"section": "Schedule", "views": 4}
    assert [(row["date"], row["total"]) for row in report["by_day"]] == [(day1, 4), (day2, 1)]
    pave = next(r for r in report["sponsors"] if r.sponsor.name == "Pave")
    assert (pave.impressions, pave.clicks, pave.click_rate) == (5, 1, 20.0)


@pytest.mark.django_db
def test_stats_page_owner_only(auth_client, client, other_user, tournament, sponsors):
    record_page_view(tournament, "schedule")
    url = reverse("tournament-stats", args=[tournament.pk])

    response = auth_client.get(url)
    assert response.status_code == 200
    assert "Pave" in response.content.decode()

    client.force_login(other_user)
    assert client.get(url).status_code == 404
    assert client.get(reverse("tournament-stats-csv", args=[tournament.pk])).status_code == 404


@pytest.mark.django_db
def test_stats_page_empty_state(auth_client, tournament):
    response = auth_client.get(reverse("tournament-stats", args=[tournament.pk]))
    assert "No visits recorded yet" in response.content.decode()


@pytest.mark.django_db
def test_sponsor_csv(auth_client, tournament, sponsors):
    record_page_view(tournament, "schedule", date=date(2026, 6, 20))
    record_page_view(tournament, "schedule", date=date(2026, 6, 20))
    record_sponsor_click(sponsors[0], date=date(2026, 6, 20))

    response = auth_client.get(reverse("tournament-stats-csv", args=[tournament.pk]))

    assert response["Content-Type"].startswith("text/csv")
    assert "attachment" in response["Content-Disposition"]
    lines = response.content.decode("utf-8-sig").strip().splitlines()
    assert lines[0] == "Date,Sponsor,Logo shown (page views),Clicks,Click rate %"
    assert "2026-06-20,Pave,2,1,50.0" in lines
    assert "2026-06-20,No Site,2,0,0.0" in lines


@pytest.mark.django_db
def test_deleting_sponsor_removes_its_stats(tournament, sponsors):
    record_page_view(tournament, "schedule")
    sponsors[0].delete()
    assert SponsorDailyStats.objects.count() == 1


@pytest.mark.django_db
def test_dashboard_links_to_statistics(auth_client, tournament):
    response = auth_client.get(reverse("tournament-dashboard", args=[tournament.pk]))
    assert reverse("tournament-stats", args=[tournament.pk]) in response.content.decode()
