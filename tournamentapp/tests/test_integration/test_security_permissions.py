"""Regression tests for ownership checks and input validation on organiser endpoints."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from sponsors.models import SponsorBanner
from tournamentapp.models import MatchEvent, Player, Tournament


def _png():
    buffer = io.BytesIO()
    Image.new("RGB", (60, 20), "red").save(buffer, "PNG")
    return SimpleUploadedFile("logo.png", buffer.getvalue(), content_type="image/png")


# ---------------------------------------------------------------------------
# add_player
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_add_player_rejects_non_owner(client, other_user, tournament, team):
    client.force_login(other_user)
    url = reverse("add-player", args=[tournament.pk, team.pk])

    response = client.post(url, {"player": "Intruder"})

    assert response.status_code == 404
    assert not Player.objects.filter(name="Intruder").exists()


@pytest.mark.django_db
def test_add_player_allows_owner(auth_client, tournament, team):
    url = reverse("add-player", args=[tournament.pk, team.pk])

    response = auth_client.post(url, {"player": "New Player"})

    assert response.status_code == 200
    assert team.players.filter(name="New Player").exists()


# ---------------------------------------------------------------------------
# Sponsor banners
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_sponsor_banner_ignores_tournament_in_request_body(client, other_user, tournament):
    """A user must not be able to attach a banner to someone else's tournament
    by tampering with a form field."""
    own_tournament = Tournament.objects.create(name="Own Cup", owner=other_user)
    client.force_login(other_user)

    client.post(
        reverse("sponsor-add", args=[own_tournament.pk]),
        {
            "tournament": tournament.pk,  # victim's tournament
            "name": "Spam",
            "link_url": "https://spam.example",
            "image": _png(),
        },
    )

    assert not SponsorBanner.objects.filter(tournament=tournament).exists()
    assert SponsorBanner.objects.filter(tournament=own_tournament, name="Spam").exists()


@pytest.mark.django_db
def test_sponsor_add_forbidden_for_non_owner(client, other_user, tournament):
    client.force_login(other_user)

    response = client.post(
        reverse("sponsor-add", args=[tournament.pk]),
        {"name": "Spam", "image": _png()},
    )

    assert response.status_code == 403
    assert not SponsorBanner.objects.exists()


@pytest.mark.django_db
def test_sponsor_pages_return_404_for_unknown_tournament(auth_client):
    assert auth_client.get(reverse("sponsor-add", args=[999999])).status_code == 404
    assert auth_client.get(reverse("sponsor-list", args=[999999])).status_code == 404


# ---------------------------------------------------------------------------
# create_match_event input validation
# ---------------------------------------------------------------------------

def _event_payload(match, player, **overrides):
    payload = {
        "event_type": "goal",
        "team": "home",
        "team_id": match.home_team.pk,
        "player_id": player.pk,
        "minute": 5,
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    "overrides",
    [
        {"event_type": "hacked"},
        {"team": "neutral"},
        {"minute": "abc"},
        {"minute": -3},
    ],
)
def test_create_match_event_rejects_invalid_input(auth_client, tournament, match, overrides):
    player = Player.objects.create(name="Home Player", team=match.home_team)
    url = reverse("add-match-event", args=[tournament.pk, match.pk])

    response = auth_client.post(url, _event_payload(match, player, **overrides))

    assert response.status_code == 400
    assert not MatchEvent.objects.exists()


@pytest.mark.django_db
def test_create_match_event_rejects_side_team_mismatch(auth_client, tournament, match):
    away_player = Player.objects.create(name="Away Player", team=match.away_team)
    url = reverse("add-match-event", args=[tournament.pk, match.pk])

    # Player and team_id say "away", but the side says "home"
    response = auth_client.post(
        url,
        _event_payload(match, away_player, team="home", team_id=match.away_team.pk),
    )

    assert response.status_code == 400
    assert not MatchEvent.objects.exists()


@pytest.mark.django_db
def test_create_match_event_rejects_player_from_other_team(auth_client, tournament, match):
    away_player = Player.objects.create(name="Away Player", team=match.away_team)
    url = reverse("add-match-event", args=[tournament.pk, match.pk])

    response = auth_client.post(url, _event_payload(match, away_player))

    assert response.status_code == 400
    assert not MatchEvent.objects.exists()


@pytest.mark.django_db
def test_create_match_event_defaults_missing_minute_to_zero(auth_client, tournament, match):
    """The live match page does not send a minute; this must keep working."""
    player = Player.objects.create(name="Home Player", team=match.home_team)
    url = reverse("add-match-event", args=[tournament.pk, match.pk])
    payload = _event_payload(match, player)
    payload.pop("minute")

    response = auth_client.post(url, payload)

    assert response.status_code == 200
    assert MatchEvent.objects.get().minute == 0
