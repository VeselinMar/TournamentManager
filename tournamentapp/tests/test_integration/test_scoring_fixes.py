"""Regression tests for score entry, live event removal and suspensions."""
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from tournamentapp.models import Match, MatchEvent, Player, Team
from tournamentapp.utils import match_points, recalculate_match_points


# ---------------------------------------------------------------------------
# Removing an event from a live match
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_removing_event_in_live_match_keeps_match_open(auth_client, tournament, match):
    scorer = Player.objects.create(name="Scorer", team=match.home_team)
    keep = MatchEvent.objects.create(match=match, team=match.home_team, player=scorer, event_type="goal")
    mistake = MatchEvent.objects.create(match=match, team=match.home_team, player=scorer, event_type="goal")

    response = auth_client.delete(reverse("delete-match-event", args=[tournament.pk, mistake.pk]))

    assert response.status_code == 200
    assert response.json()["home_score"] == 1
    match.refresh_from_db()
    match.home_team.refresh_from_db()
    match.away_team.refresh_from_db()
    assert match.is_finished is False
    assert (match.home_score, match.away_score) == (1, 0)
    assert match.home_team.tournament_points == 0
    assert match.away_team.tournament_points == 0
    assert MatchEvent.objects.filter(pk=keep.pk).exists()


@pytest.mark.django_db
def test_removing_own_goal_in_live_match_updates_opponent_score(auth_client, tournament, match):
    defender = Player.objects.create(name="Defender", team=match.home_team)
    own_goal = MatchEvent.objects.create(match=match, team=match.home_team, player=defender, event_type="own_goal")
    match.away_score = 1
    match.save()

    auth_client.delete(reverse("delete-match-event", args=[tournament.pk, own_goal.pk]))

    match.refresh_from_db()
    assert (match.home_score, match.away_score) == (0, 0)
    assert match.is_finished is False


# ---------------------------------------------------------------------------
# Manual score entry (MatchEditView / MatchEditForm)
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_manual_score_entry_finishes_match_with_configured_points(auth_client, tournament, match):
    tournament.points_for_win = 2
    tournament.points_for_loss = 1
    tournament.save()

    response = auth_client.post(
        reverse("match-edit", args=[tournament.pk, match.pk]),
        {"home_score": 3, "away_score": 1},
    )

    assert response.status_code == 302
    match.refresh_from_db()
    match.home_team.refresh_from_db()
    match.away_team.refresh_from_db()
    assert match.is_finished is True
    assert (match.home_score, match.away_score) == (3, 1)
    assert match.home_team.tournament_points == 2
    assert match.away_team.tournament_points == 1


@pytest.mark.django_db
def test_correcting_manual_score_reverses_previous_points(auth_client, tournament, match):
    url = reverse("match-edit", args=[tournament.pk, match.pk])
    auth_client.post(url, {"home_score": 2, "away_score": 0})   # home win: 3 / 0
    auth_client.post(url, {"home_score": 1, "away_score": 1})   # corrected to a draw: 1 / 1

    match.home_team.refresh_from_db()
    match.away_team.refresh_from_db()
    assert match.home_team.tournament_points == 1
    assert match.away_team.tournament_points == 1


@pytest.mark.django_db
def test_manual_score_entry_rejects_other_users(client, other_user, tournament, match):
    client.force_login(other_user)

    response = client.post(
        reverse("match-edit", args=[tournament.pk, match.pk]),
        {"home_score": 5, "away_score": 0},
    )

    assert response.status_code == 404
    match.refresh_from_db()
    assert match.is_finished is False


@pytest.mark.django_db
def test_recalculate_match_points_reads_previous_result_from_database(tournament, match):
    recalculate_match_points(match, 0, 2)          # away win
    match.home_score, match.away_score = 9, 9      # stale in-memory values must be ignored
    recalculate_match_points(match, 2, 0)          # corrected to home win

    home = Team.objects.get(pk=match.home_team.pk)
    away = Team.objects.get(pk=match.away_team.pk)
    assert home.tournament_points == tournament.points_for_win
    assert away.tournament_points == tournament.points_for_loss


@pytest.mark.django_db
def test_match_points_helper(tournament):
    tournament.points_for_win, tournament.points_for_draw, tournament.points_for_loss = 3, 1, 0
    assert match_points(tournament, 2, 1) == (3, 0)
    assert match_points(tournament, 0, 4) == (0, 3)
    assert match_points(tournament, 2, 2) == (1, 1)


# ---------------------------------------------------------------------------
# Suspensions
# ---------------------------------------------------------------------------

def _add_card(match, player, card):
    return MatchEvent.objects.create(match=match, team=player.team, player=player, event_type=card)


@pytest.mark.django_db
def test_unmute_keeps_card_history(auth_client, tournament, match):
    player = Player.objects.create(name="Booked", team=match.home_team, is_muted=True)
    _add_card(match, player, "yellow_card")
    _add_card(match, player, "yellow_card")

    auth_client.post(reverse("toggle-player-mute", args=[tournament.pk, player.pk]))

    player.refresh_from_db()
    assert player.is_muted is False
    assert player.yellow_cards() == 2           # history kept for stats
    assert player.active_yellow_cards() == 0    # but no longer counts
    assert player.is_suspended() is False


@pytest.mark.django_db
def test_cards_after_unmute_count_from_zero(auth_client, tournament, field, match):
    tournament.yellow_cards_for_suspension = 2
    tournament.save()
    player = Player.objects.create(name="Booked", team=match.home_team, is_muted=True)
    _add_card(match, player, "yellow_card")
    _add_card(match, player, "yellow_card")
    player.unmute()

    next_match = Match.objects.create(
        tournament=tournament,
        home_team=match.home_team,
        away_team=match.away_team,
        field=field,
        start_time=timezone.now() + timedelta(hours=2),
    )
    url = reverse("add-match-event", args=[tournament.pk, next_match.pk])
    payload = {"event_type": "yellow_card", "team": "home", "team_id": match.home_team.pk, "player_id": player.pk}

    auth_client.post(url, payload)
    player.refresh_from_db()
    assert player.is_muted is False             # first new yellow only

    auth_client.post(url, payload)
    player.refresh_from_db()
    assert player.is_muted is True              # threshold reached again


@pytest.mark.django_db
def test_red_card_before_unmute_no_longer_suspends(tournament, match):
    player = Player.objects.create(name="Sent off", team=match.home_team, is_muted=True)
    _add_card(match, player, "red_card")

    player.unmute()

    assert player.red_cards() == 1
    assert player.is_suspended() is False


@pytest.mark.django_db
def test_live_score_is_stored_while_match_is_running(auth_client, tournament, match):
    scorer = Player.objects.create(name="Scorer", team=match.away_team)
    url = reverse("add-match-event", args=[tournament.pk, match.pk])

    auth_client.post(url, {
        "event_type": "goal", "team": "away",
        "team_id": match.away_team.pk, "player_id": scorer.pk,
    })

    match.refresh_from_db()
    assert (match.home_score, match.away_score) == (0, 1)
    assert match.is_finished is False
