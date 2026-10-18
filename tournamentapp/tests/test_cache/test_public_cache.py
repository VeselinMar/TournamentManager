"""
Public API caching: responses are cached per tournament data version and
every change that is visible on the public page must invalidate them.
"""
import io
import json
from datetime import datetime, timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from announcements.models import Announcement
from programme.models import SideEvent
from sponsors.models import SponsorBanner
from tournamentapp.cache import batched_invalidation, invalidate
from tournamentapp.models import Field, Match, MatchEvent, Player, Team, Tournament
from vendors.models import Vendor

BROWSER = "Mozilla/5.0 (X11; Linux x86_64) Chrome/129.0"


def api(client, name, tournament, **headers):
    return client.get(reverse(f"api-{name}", args=[tournament.slug]), **headers)


def data(client, name, tournament):
    response = api(client, name, tournament)
    assert response.status_code == 200, response.content
    return response.json()


def version(tournament):
    return Tournament.objects.values_list("cache_version", flat=True).get(pk=tournament.pk)


@pytest.fixture
def live(tournament, field, team):
    """A round robin with one finished and one upcoming match."""
    away = Team.objects.create(name="Team B", tournament=tournament)
    third = Team.objects.create(name="Team C", tournament=tournament)
    start = timezone.make_aware(datetime(2026, 6, 20, 10, 0))
    first = Match.objects.create(tournament=tournament, home_team=team, away_team=away, field=field,
                                 start_time=start, home_score=1, is_finished=True)
    second = Match.objects.create(tournament=tournament, home_team=away, away_team=third, field=field,
                                  start_time=start + timedelta(minutes=20))
    tournament.refresh_from_db()
    return {"first": first, "second": second, "away": away, "third": third}


# ---------------------------------------------------------------------------
# Serving from cache
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("endpoint", ["schedule", "leaderboard", "tournament-meta", "bracket"])
def test_cached_request_needs_a_single_query(client, tournament, live, endpoint, django_assert_num_queries):
    api(client, endpoint, tournament)                 # warm the cache
    with django_assert_num_queries(1):                # only the version lookup
        assert api(client, endpoint, tournament).status_code == 200


@pytest.mark.django_db
def test_unchanged_data_is_answered_with_304(client, tournament, live):
    first = api(client, "schedule", tournament)
    etag = first["ETag"]
    assert first["Cache-Control"] == "no-cache"

    second = api(client, "schedule", tournament, HTTP_IF_NONE_MATCH=etag)
    assert second.status_code == 304 and second.content == b""

    live["second"].home_score = 2
    live["second"].save()

    third = api(client, "schedule", tournament, HTTP_IF_NONE_MATCH=etag)
    assert third.status_code == 200 and third["ETag"] != etag


@pytest.mark.django_db
def test_etag_changes_with_each_deploy(client, tournament, live, settings):
    before = api(client, "schedule", tournament)["ETag"]
    settings.CODE_VERSION = "nextrelease"
    assert api(client, "schedule", tournament)["ETag"] != before


@pytest.mark.django_db
def test_endpoints_do_not_share_cache_entries(client, tournament, live):
    assert "field_names" in data(client, "schedule", tournament)
    assert "top_scorers" in data(client, "leaderboard", tournament)


# ---------------------------------------------------------------------------
# Invalidation through the organiser views
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_goal_updates_top_scorers(auth_client, client, tournament, live):
    match = live["second"]
    player = Player.objects.create(name="Striker", team=match.home_team)
    assert data(client, "leaderboard", tournament)["top_scorers"] == []

    auth_client.post(reverse("add-match-event", args=[tournament.pk, match.pk]), {
        "event_type": "goal", "team": "home", "team_id": match.home_team.pk, "player_id": player.pk,
    })

    assert [p["player_name"] for p in data(client, "leaderboard", tournament)["top_scorers"]] == ["Striker"]
    assert data(client, "schedule", tournament)["timeline"][1]["matches"][0]["home_score"] == 1


@pytest.mark.django_db
def test_finishing_a_match_updates_schedule_and_standings(auth_client, client, tournament, live):
    match = live["second"]
    assert data(client, "schedule", tournament)["timeline"][1]["matches"][0]["is_finished"] is False

    auth_client.post(reverse("finish-match", args=[tournament.pk, match.pk]))

    assert data(client, "schedule", tournament)["timeline"][1]["matches"][0]["is_finished"] is True
    points = {r["team_name"]: r["points"] for r in data(client, "leaderboard", tournament)["standings"]}
    assert points["Team B"] == 1 and points["Team C"] == 1


@pytest.mark.django_db
def test_delay_propagation_updates_later_matches(auth_client, client, tournament, field, live):
    """QuerySet.update() sends no signals — the explicit invalidation must cover it."""
    times_before = [row["time"] for row in data(client, "schedule", tournament)["timeline"]]

    auth_client.post(reverse("edit-match", args=[tournament.pk, live["first"].pk]),
                     {"start_time": "10:30", "field": field.pk, "propagate": "on"})

    times_after = [row["time"] for row in data(client, "schedule", tournament)["timeline"]]
    assert times_before == ["10:00", "10:20"]
    assert times_after == ["10:30", "10:50"]


@pytest.mark.django_db
def test_generating_and_resetting_schedule(auth_client, client, tournament, field, team):
    """Schedule generation uses bulk_create (no signals)."""
    for i in range(3):
        Team.objects.create(name=f"Extra {i}", tournament=tournament)
    assert data(client, "schedule", tournament)["timeline"] == []

    auth_client.post(reverse("generate-tournament-schedule", args=[tournament.pk]), {
        "start_date": "2026-06-20", "start_time": "10:00", "game_duration": 15, "pause_duration": 5,
    })
    assert len(data(client, "schedule", tournament)["timeline"]) > 0

    auth_client.post(reverse("reset-schedule", args=[tournament.pk]))
    assert data(client, "schedule", tournament)["timeline"] == []


@pytest.mark.django_db
def test_renaming_team_field_and_player(auth_client, client, tournament, field, live):
    match = live["first"]
    scorer = Player.objects.create(name="Old Name", team=match.home_team)
    MatchEvent.objects.create(match=match, team=match.home_team, player=scorer, event_type="goal")
    data(client, "schedule", tournament), data(client, "leaderboard", tournament)

    auth_client.post(reverse("team-list", args=[tournament.pk]), {"team_id": live["third"].pk, "name": "Renamed FC"})
    auth_client.post(reverse("edit-field", args=[tournament.pk, field.pk]),
                     data=json.dumps({"name": "Center Court"}), content_type="application/json")
    auth_client.post(reverse("rename-player", args=[tournament.pk, scorer.pk]), {"name": "New Name"})

    schedule = data(client, "schedule", tournament)
    leaderboard = data(client, "leaderboard", tournament)
    assert schedule["field_names"] == ["Center Court"]
    assert "Renamed FC" in {r["team_name"] for r in leaderboard["standings"]}
    assert leaderboard["top_scorers"][0]["player_name"] == "New Name"


@pytest.mark.django_db
def test_tournament_settings_update_meta(auth_client, client, tournament):
    assert data(client, "tournament-meta", tournament)["name"] == tournament.name

    auth_client.post(reverse("tournament-edit", args=[tournament.pk]), {
        "name": tournament.name, "points_for_win": 3, "points_for_draw": 1,
        "yellow_cards_for_suspension": 2, "show_vendors": "on",
    })

    meta = data(client, "tournament-meta", tournament)
    assert meta["show_vendors"] is True and meta["show_leaderboard"] is False
    assert api(client, "leaderboard", tournament).status_code == 404


@pytest.mark.django_db
def test_sponsor_add_and_delete(auth_client, client, tournament):
    buffer = io.BytesIO()
    Image.new("RGB", (40, 20), "red").save(buffer, "PNG")
    assert data(client, "tournament-meta", tournament)["sponsors"] == []

    auth_client.post(reverse("sponsor-add", args=[tournament.pk]), {
        "name": "Bakery", "image": SimpleUploadedFile("b.png", buffer.getvalue(), content_type="image/png"),
    })
    sponsors = data(client, "tournament-meta", tournament)["sponsors"]
    assert [s["name"] for s in sponsors] == ["Bakery"]

    banner = SponsorBanner.objects.get(name="Bakery")
    auth_client.delete(reverse("sponsor-remove", args=[tournament.pk, banner.pk]))
    assert data(client, "tournament-meta", tournament)["sponsors"] == []


@pytest.mark.django_db
def test_vendors_side_events_and_announcements(client, tournament):
    now = timezone.now()
    assert data(client, "vendors", tournament) == []
    assert data(client, "side-events", tournament) == []
    assert data(client, "announcements", tournament) == []

    Vendor.objects.create(tournament=tournament, name="Grill", category="Food")
    SideEvent.objects.create(tournament=tournament, name="Kids zone", start_time=now, end_time=now)
    Announcement.objects.create(tournament=tournament, message="Final at 17:00",
                                starts_at=now, ends_at=now + timedelta(hours=1))

    assert [v["name"] for v in data(client, "vendors", tournament)] == ["Grill"]
    assert [e["name"] for e in data(client, "side-events", tournament)] == ["Kids zone"]
    assert [a["message"] for a in data(client, "announcements", tournament)] == ["Final at 17:00"]


@pytest.mark.django_db
def test_knockout_bracket_refresh(client, user):
    from tournamentapp.competition import refresh_knockout, schedule_groups_knockout
    from tournamentapp.models import Group
    from tournamentapp.utils import recalculate_match_points

    cup = Tournament.objects.create(name="Cup", owner=user, format=Tournament.GROUPS_KNOCKOUT,
                                    qualifiers_per_group=1)
    Field.objects.create(name="F1", tournament=cup, owner=user)
    for name in "AB":
        group = Group.objects.create(tournament=cup, name=name)
        for i in range(2):
            Team.objects.create(name=f"{name}{i}", tournament=cup, group=group)
    schedule_groups_knockout(cup, timezone.now(), timedelta(minutes=10), timedelta(minutes=5))
    final = data(client, "bracket", cup)["rounds"][0]["matches"][0]
    assert final["home_placeholder"] is True

    for match in cup.matches.filter(stage=Match.STAGE_GROUP):
        recalculate_match_points(match, 1, 0)
    refresh_knockout(cup)

    final = data(client, "bracket", cup)["rounds"][0]["matches"][0]
    assert final["home_placeholder"] is False


@pytest.mark.django_db
def test_page_view_tracking_does_not_invalidate(client, tournament, live):
    before = version(tournament)
    client.post(reverse("api-track-view", args=[tournament.slug]), {"section": "schedule"},
                content_type="application/json", HTTP_USER_AGENT=BROWSER)
    assert version(tournament) == before


# ---------------------------------------------------------------------------
# Version bookkeeping
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_stale_tournament_instance_cannot_roll_back_version(tournament):
    stale = Tournament.objects.get(pk=tournament.pk)
    invalidate(tournament.pk)
    invalidate(tournament.pk)
    bumped = version(tournament)

    stale.name = "Renamed"
    stale.save()                      # full save of an instance loaded earlier

    assert version(tournament) == bumped + 1   # its own change bumps; never goes back
    assert Tournament.objects.get(pk=tournament.pk).name == "Renamed"


@pytest.mark.django_db
def test_batch_bumps_once(tournament, field, team):
    before = version(tournament)
    with batched_invalidation():
        for i in range(5):
            Team.objects.create(name=f"Batch {i}", tournament=tournament)
        with batched_invalidation():
            Field.objects.create(name="Side", tournament=tournament, owner=tournament.owner)
        assert version(tournament) == before          # nothing until the outer block ends
    assert version(tournament) == before + 1


@pytest.mark.django_db
def test_batch_still_bumps_and_reraises_on_error(tournament):
    before = version(tournament)
    with pytest.raises(RuntimeError, match="boom"):
        with batched_invalidation():
            Team.objects.create(name="Half done", tournament=tournament)
            raise RuntimeError("boom")
    assert version(tournament) == before + 1


@pytest.mark.django_db
def test_other_tournaments_are_not_invalidated(tournament, other_user, live):
    other = Tournament.objects.create(name="Other", owner=other_user)
    before = version(other)
    live["second"].home_score = 3
    live["second"].save()
    assert version(other) == before
