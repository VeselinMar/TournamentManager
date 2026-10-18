"""Seeding, knockout results, corrections and manual overrides."""
import pytest

from tournamentapp.competition import (
    CompetitionError, apply_knockout_result, compute_seeds, refresh_knockout,
    refresh_match_result, schedule_groups_knockout, set_slot_team,
)
from tournamentapp.models import Match, MatchEvent, MatchSlot, Player, Team
from tournamentapp.utils import recalculate_match_points

from .conftest import GAME, PAUSE, START, THREE_GROUPS_OF_THREE, TWO_GROUPS_OF_FIVE


@pytest.fixture
def cup(build_tournament, play_group_stage):
    """Two groups of five, scheduled and with the group stage played."""
    tournament = build_tournament(TWO_GROUPS_OF_FIVE, third_place_match=True)
    schedule_groups_knockout(tournament, START, GAME, PAUSE)
    play_group_stage(tournament)
    refresh_knockout(tournament)
    return tournament


def _names(match):
    return (match.home_team.name if match.home_team else None,
            match.away_team.name if match.away_team else None)


@pytest.mark.django_db
def test_bracket_waits_for_the_whole_group_stage(build_tournament, ko):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE)
    schedule_groups_knockout(tournament, START, GAME, PAUSE)
    first = tournament.matches.filter(stage=Match.STAGE_GROUP).first()
    recalculate_match_points(first, 1, 0)

    refresh_knockout(tournament)

    assert _names(ko(tournament, 4, 1)) == (None, None)


@pytest.mark.django_db
def test_semi_finals_cross_groups(cup, ko):
    # A1 (GD +100) is the best winner, B2 (+58) the best runner-up.
    # Seed 1 vs seed 4 would be A1 vs A2, so the runners-up are swapped.
    assert _names(ko(cup, 4, 1)) == ("A1", "B2")
    assert _names(ko(cup, 4, 2)) == ("B1", "A2")


@pytest.mark.django_db
def test_winners_and_losers_advance(cup, ko):
    apply_knockout_result(ko(cup, 4, 1), 2, 1)
    apply_knockout_result(ko(cup, 4, 2), 1, 1, home_penalties=3, away_penalties=4)

    sf2 = ko(cup, 4, 2)
    assert sf2.winner.name == "A2" and sf2.decided_by == Match.DECIDED_PENALTIES
    assert _names(ko(cup, 2)) == ("A1", "A2")
    assert _names(ko(cup, 2, third_place=True)) == ("B2", "B1")


@pytest.mark.django_db
def test_knockout_draw_needs_penalties(cup, ko):
    with pytest.raises(CompetitionError, match="penalty"):
        apply_knockout_result(ko(cup, 4, 1), 1, 1)
    with pytest.raises(CompetitionError, match="cannot end level"):
        apply_knockout_result(ko(cup, 4, 1), 1, 1, home_penalties=4, away_penalties=4)
    with pytest.raises(CompetitionError, match="only taken when the match ends in a draw"):
        apply_knockout_result(ko(cup, 4, 1), 2, 1, home_penalties=4, away_penalties=3)
    assert ko(cup, 4, 1).is_finished is False


@pytest.mark.django_db
def test_extra_time_only_when_enabled(cup, ko):
    with pytest.raises(CompetitionError, match="extra time is disabled"):
        apply_knockout_result(ko(cup, 4, 1), 2, 1, extra_time=True)

    cup.knockout_draw_resolution = 'extra_time'
    cup.save()
    apply_knockout_result(ko(cup, 4, 1), 2, 1, extra_time=True)
    assert ko(cup, 4, 1).decided_by == Match.DECIDED_EXTRA_TIME


@pytest.mark.django_db
def test_knockout_results_do_not_add_group_points(cup, ko, points_table):
    group_a = cup.groups.get(name="A")
    before = points_table(cup, group=group_a)
    apply_knockout_result(ko(cup, 4, 1), 5, 0)
    assert points_table(cup, group=group_a) == before


@pytest.mark.django_db
def test_corrected_group_result_updates_unplayed_knockout(cup, ko):
    a1_vs_a2 = Match.objects.get(
        tournament=cup, stage=Match.STAGE_GROUP,
        home_team__name__in=["A1", "A2"], away_team__name__in=["A1", "A2"],
    )
    a2_home = a1_vs_a2.home_team.name == "A2"
    recalculate_match_points(a1_vs_a2, 9 if a2_home else 0, 0 if a2_home else 9)

    conflicts = refresh_knockout(cup)

    assert conflicts == []
    semi_teams = {_names(ko(cup, 4, 1)), _names(ko(cup, 4, 2))}
    winners = {pair[0] for pair in semi_teams}
    assert "A2" in winners and "A1" not in winners


@pytest.mark.django_db
def test_started_knockout_match_is_not_changed_silently(cup, ko):
    semi = ko(cup, 4, 1)
    player = Player.objects.create(name="Scorer", team=semi.home_team)
    MatchEvent.objects.create(match=semi, team=semi.home_team, player=player, event_type='goal')

    a1_vs_a2 = Match.objects.get(
        tournament=cup, stage=Match.STAGE_GROUP,
        home_team__name__in=["A1", "A2"], away_team__name__in=["A1", "A2"],
    )
    a2_home = a1_vs_a2.home_team.name == "A2"
    recalculate_match_points(a1_vs_a2, 9 if a2_home else 0, 0 if a2_home else 9)

    conflicts = refresh_knockout(cup)

    assert conflicts and "already started" in conflicts[0]
    assert _names(ko(cup, 4, 1)) == ("A1", "B2")


@pytest.mark.django_db
def test_corrected_knockout_result_reopens_match_and_clears_next_round(cup, ko):
    semi = ko(cup, 4, 1)
    player = Player.objects.create(name="Scorer", team=semi.home_team)
    goal = MatchEvent.objects.create(match=semi, team=semi.home_team, player=player, event_type='goal')
    from tournamentapp.competition import finish_knockout_match
    finish_knockout_match(semi)
    assert _names(ko(cup, 2))[0] == "A1"

    goal.delete()
    refresh_match_result(ko(cup, 4, 1))

    semi = ko(cup, 4, 1)
    assert semi.is_finished is False and semi.winner is None
    assert _names(ko(cup, 2))[0] is None


@pytest.mark.django_db
def test_manual_override_survives_refresh_and_can_be_cleared(cup, ko):
    final = ko(cup, 2)
    b5 = Team.objects.get(tournament=cup, name="B5")

    set_slot_team(final, MatchSlot.HOME, b5)
    refresh_knockout(cup)
    assert _names(ko(cup, 2))[0] == "B5"

    apply_knockout_result(ko(cup, 4, 1), 1, 0)
    assert _names(ko(cup, 2))[0] == "B5"          # override wins over the result

    set_slot_team(ko(cup, 2), MatchSlot.HOME, None)
    assert _names(ko(cup, 2))[0] == "A1"          # back to automatic


@pytest.mark.django_db
def test_override_rules(cup, ko):
    semi = ko(cup, 4, 1)
    with pytest.raises(CompetitionError, match="against itself"):
        set_slot_team(semi, MatchSlot.HOME, semi.away_team)

    apply_knockout_result(semi, 1, 0)
    with pytest.raises(CompetitionError, match="already started"):
        set_slot_team(ko(cup, 4, 1), MatchSlot.HOME, Team.objects.get(tournament=cup, name="A5"))


@pytest.mark.django_db
def test_best_placed_qualifiers_compare_groups_fairly(build_tournament, play_group_stage):
    tournament = build_tournament(THREE_GROUPS_OF_THREE, best_placed_qualifiers=2)
    schedule_groups_knockout(tournament, START, GAME, PAUSE)
    play_group_stage(tournament)

    seeds = [team.name for team in compute_seeds(tournament)]

    # Third places: A3 GD -80, B3 -88, C3 -96 -> A3 and B3 go through
    assert len(seeds) == 8
    assert set(seeds[-2:]) == {"A3", "B3"} and "C3" not in seeds
    assert set(seeds[:3]) == {"A1", "B1", "C1"}


@pytest.mark.django_db
def test_byes_resolve_directly_into_semi_finals(build_tournament, play_group_stage, ko):
    tournament = build_tournament(THREE_GROUPS_OF_THREE)
    schedule_groups_knockout(tournament, START, GAME, PAUSE)
    play_group_stage(tournament)
    refresh_knockout(tournament)

    # Winners by GD per game: C1 (+84), B1 (+77), A1 (+70) -> C1 and B1 get byes.
    # Runners-up: C2 (+12), B2 (+11), A2 (+10). Seed 3 vs 6 would be A1 vs A2,
    # so A2 and B2 swap places.
    assert ko(tournament, 4, 1).home_team.name == "C1"
    assert ko(tournament, 4, 2).home_team.name == "B1"
    assert _names(ko(tournament, 8, 1)) == ("C2", "A2")
    assert _names(ko(tournament, 8, 2)) == ("A1", "B2")
