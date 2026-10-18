"""Ranking of teams level on points (tie-break rules)."""
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from tournamentapp.models import Match, Team, Tournament
from tournamentapp.utils import get_team_standings, match_points


@pytest.fixture
def make_team(tournament):
    def _make(name):
        return Team.objects.create(name=name, tournament=tournament)
    return _make


@pytest.fixture
def play(tournament, field):
    """Create a finished match and award points the same way the app does."""
    counter = {"n": 0}

    def _play(home, away, home_goals, away_goals):
        counter["n"] += 1
        Match.objects.create(
            tournament=tournament, field=field,
            home_team=home, away_team=away,
            home_score=home_goals, away_score=away_goals,
            is_finished=True,
            start_time=timezone.now() + timedelta(minutes=counter["n"]),
        )
        home_pts, away_pts = match_points(tournament, home_goals, away_goals)
        Team.objects.filter(pk=home.pk).update(tournament_points=home.tournament_points + home_pts)
        Team.objects.filter(pk=away.pk).update(tournament_points=away.tournament_points + away_pts)
        home.refresh_from_db()
        away.refresh_from_db()
    return _play


def names(tournament):
    return [t.name for t in get_team_standings(tournament)]


def _alpha_beats_bravo_but_worse_goal_difference(make_team, play):
    """Alpha and Bravo finish on 3 points. Alpha won the direct match,
    Bravo has the better overall goal difference. Y finishes clear on 6."""
    a, b, y, z = make_team("Alpha"), make_team("Bravo"), make_team("Y"), make_team("Z")
    play(a, b, 1, 0)   # Alpha beat Bravo
    play(y, a, 5, 0)   # Alpha: GD -4
    play(b, z, 1, 0)   # Bravo: GD 0
    play(y, z, 1, 0)   # Y on 6 points, Z on 0
    return a, b

@pytest.mark.django_db
def test_overall_goal_difference_breaks_tie_when_teams_have_not_met(tournament, make_team, play):
    """The live Vienna case: Kappa (-8) was ranked above Zeta (-2) alphabetically."""
    kappa, zeta, x, y = make_team("Kappa"), make_team("Zeta"), make_team("X"), make_team("Y")
    play(x, kappa, 6, 0)
    play(kappa, y, 0, 0)
    play(zeta, y, 0, 0)
    play(x, zeta, 2, 0)

    order = [n for n in names(tournament) if n in ("Kappa", "Zeta")]
    assert order == ["Zeta", "Kappa"]


@pytest.mark.django_db
def test_goals_scored_breaks_tie_after_goal_difference(tournament, make_team, play):
    a, b, x = make_team("Alpha"), make_team("Bravo"), make_team("X")
    play(a, x, 1, 1)
    play(b, x, 3, 3)   # same points and GD as Alpha, more goals

    order = [n for n in names(tournament) if n in ("Alpha", "Bravo")]
    assert order == ["Bravo", "Alpha"]


@pytest.mark.django_db
def test_head_to_head_rule_ranks_direct_winner_first(tournament, make_team, play):
    a, b = _alpha_beats_bravo_but_worse_goal_difference(make_team, play)

    tournament.tiebreak_rule = Tournament.TIEBREAK_HEAD_TO_HEAD
    tournament.save()
    order = [n for n in names(tournament) if n in ("Alpha", "Bravo")]
    assert order == ["Alpha", "Bravo"]


@pytest.mark.django_db
def test_goal_difference_rule_ignores_head_to_head_until_later(tournament, make_team, play):
    a, b = _alpha_beats_bravo_but_worse_goal_difference(make_team, play)

    tournament.tiebreak_rule = Tournament.TIEBREAK_GOAL_DIFFERENCE
    tournament.save()
    order = [n for n in names(tournament) if n in ("Alpha", "Bravo")]
    assert order == ["Bravo", "Alpha"]


@pytest.mark.django_db
def test_head_to_head_uses_match_score_including_own_goals(tournament, make_team, play):
    """Score fields already include own goals; a win by own goal must count."""
    a, b, y, z = make_team("Alpha"), make_team("Bravo"), make_team("Y"), make_team("Z")
    play(b, a, 1, 0)   # Bravo won 1-0 (e.g. via an Alpha own goal)
    play(a, z, 2, 0)   # Alpha: 3 pts, GD +1
    play(y, b, 1, 0)   # Bravo: 3 pts, GD 0
    play(y, z, 1, 0)   # Y clear on 6

    order = [n for n in names(tournament) if n in ("Alpha", "Bravo")]
    assert order == ["Bravo", "Alpha"]


@pytest.mark.django_db
def test_three_way_tie_uses_mini_table(tournament, make_team, play):
    a, b, c = make_team("Alpha"), make_team("Bravo"), make_team("Charlie")
    play(a, b, 3, 0)
    play(b, c, 1, 0)
    play(c, a, 1, 0)   # everyone 3 pts; mini-table GD: A +2, B -2, C 0

    assert names(tournament) == ["Alpha", "Charlie", "Bravo"]


@pytest.mark.django_db
def test_name_is_final_case_insensitive_fallback(tournament, make_team):
    make_team("bravo")
    make_team("Alpha")
    make_team("charlie")

    assert names(tournament) == ["Alpha", "bravo", "charlie"]


@pytest.mark.django_db
def test_standings_expose_full_record(tournament, make_team, play):
    a, b = make_team("Alpha"), make_team("Bravo")
    play(a, b, 3, 1)
    play(b, a, 2, 2)

    alpha = get_team_standings(tournament)[0]
    assert (alpha.name, alpha.played, alpha.wins, alpha.draws, alpha.losses) == ("Alpha", 2, 1, 1, 0)
    assert (alpha.goals_for, alpha.goals_against, alpha.goal_difference) == (5, 3, 2)


@pytest.mark.django_db
def test_leaderboard_api_matches_standings(client, tournament, make_team, play):
    kappa, zeta, x = make_team("Kappa"), make_team("Zeta"), make_team("X")
    play(x, kappa, 6, 0)
    play(x, zeta, 2, 0)
    play(kappa, zeta, 0, 0)

    data = client.get(reverse("api-leaderboard", args=[tournament.slug])).json()

    rows = {r["team_name"]: r for r in data["standings"]}
    assert [r["team_name"] for r in data["standings"]] == ["X", "Zeta", "Kappa"]
    assert rows["Kappa"]["goal_difference"] == -6
    assert rows["Zeta"]["goal_difference"] == -2


@pytest.mark.django_db
def test_meta_api_exposes_tiebreak_rule(client, tournament):
    data = client.get(reverse("api-tournament-meta", args=[tournament.slug])).json()
    assert data["tiebreak_rule"] == Tournament.TIEBREAK_HEAD_TO_HEAD


@pytest.mark.django_db
def test_organiser_can_change_tiebreak_rule(auth_client, tournament):
    response = auth_client.post(
        reverse("tournament-edit", args=[tournament.pk]),
        {
            "name": tournament.name,
            "points_for_win": 3,
            "points_for_draw": 1,
            "yellow_cards_for_suspension": 2,
            "tiebreak_rule": Tournament.TIEBREAK_GOAL_DIFFERENCE,
            "show_leaderboard": "on",
        },
    )

    assert response.status_code == 302
    tournament.refresh_from_db()
    assert tournament.tiebreak_rule == Tournament.TIEBREAK_GOAL_DIFFERENCE
