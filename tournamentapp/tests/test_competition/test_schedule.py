"""Group + knockout schedule generation (single day)."""
from collections import Counter
from datetime import timedelta
from itertools import combinations

import pytest

from tournamentapp.competition import CompetitionError, schedule_groups_knockout
from tournamentapp.models import Match, MatchSlot

from .conftest import GAME, PAUSE, START, THREE_GROUPS_OF_THREE, TWO_GROUPS_OF_FIVE

SLOT = GAME + PAUSE


def _schedule(tournament, **kwargs):
    return schedule_groups_knockout(tournament, START, GAME, PAUSE, **kwargs)


def _group_matches(tournament):
    return list(tournament.matches.filter(stage=Match.STAGE_GROUP).select_related('home_team', 'away_team', 'field'))


def _knockout(tournament):
    return list(
        tournament.matches.filter(stage=Match.STAGE_KNOCKOUT)
        .select_related('field').prefetch_related('slots')
        .order_by('-round', 'is_third_place', 'bracket_position')
    )


@pytest.mark.django_db
def test_every_group_pairing_is_played_once_within_its_group(build_tournament):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE)
    _schedule(tournament)

    matches = _group_matches(tournament)
    assert len(matches) == 20
    pairings = Counter(frozenset((m.home_team.name, m.away_team.name)) for m in matches)
    for group, teams in TWO_GROUPS_OF_FIVE.items():
        for a, b in combinations(teams, 2):
            assert pairings[frozenset((a, b))] == 1
    assert all(m.group.name == m.home_team.name[0] == m.away_team.name[0] for m in matches)


@pytest.mark.django_db
def test_no_team_plays_in_consecutive_group_slots(build_tournament):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE)
    _schedule(tournament)

    by_time = {}
    for m in _group_matches(tournament):
        by_time.setdefault(m.start_time, set()).update({m.home_team_id, m.away_team_id})
    times = sorted(by_time)
    for earlier, later in zip(times, times[1:]):
        if later - earlier == SLOT:
            assert not by_time[earlier] & by_time[later]


@pytest.mark.django_db
def test_field_and_time_are_unique(build_tournament):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE, third_place_match=True)
    _schedule(tournament)
    keys = [(m.field_id, m.start_time) for m in tournament.matches.all()]
    assert len(keys) == len(set(keys))


@pytest.mark.django_db
def test_knockout_bracket_with_rest_and_final_on_first_field(build_tournament):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE, third_place_match=True)
    _schedule(tournament)

    last_group_start = max(m.start_time for m in _group_matches(tournament))
    semis, final, third = None, None, None
    knockout = _knockout(tournament)
    semis = [m for m in knockout if m.round == 4]
    final = next(m for m in knockout if m.round == 2 and not m.is_third_place)
    third = next(m for m in knockout if m.is_third_place)

    assert len(knockout) == 4 and len(semis) == 2
    # one free slot after the group stage and before the final
    assert all(sf.start_time >= last_group_start + 2 * SLOT for sf in semis)
    assert final.start_time >= max(sf.start_time for sf in semis) + 2 * SLOT
    # final on the first field, third place next to it
    first_field = tournament.fields.order_by('pk').first()
    assert final.field == first_field
    assert third.start_time == final.start_time and third.field != first_field


@pytest.mark.django_db
def test_knockout_placeholders(build_tournament):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE, third_place_match=True)
    _schedule(tournament)
    labels = {
        m.round_label: (m.home_label, m.away_label) for m in _knockout(tournament)
    }
    assert labels == {
        "Semi-final 1": ("Group winner #1", "Runner-up #2"),
        "Semi-final 2": ("Group winner #2", "Runner-up #1"),
        "Final": ("Winner SF 1", "Winner SF 2"),
        "Third place": ("Loser SF 1", "Loser SF 2"),
    }
    assert all(m.home_team is None and m.away_team is None for m in _knockout(tournament))


@pytest.mark.django_db
def test_single_field_plays_third_place_before_final(build_tournament):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE, fields=1, third_place_match=True)
    _schedule(tournament)
    knockout = _knockout(tournament)
    final = next(m for m in knockout if m.round == 2 and not m.is_third_place)
    third = next(m for m in knockout if m.is_third_place)
    assert third.start_time < final.start_time


@pytest.mark.django_db
def test_byes_send_top_seeds_straight_to_semi_finals(build_tournament):
    tournament = build_tournament(THREE_GROUPS_OF_THREE)
    _schedule(tournament)
    knockout = _knockout(tournament)

    quarter_finals = [m for m in knockout if m.round == 8]
    semis = {m.bracket_position: m for m in knockout if m.round == 4}
    assert len(quarter_finals) == 2
    assert (semis[1].home_label, semis[1].away_label) == ("Group winner #1", "Winner QF 1")
    assert (semis[2].home_label, semis[2].away_label) == ("Group winner #2", "Winner QF 2")
    seed_slot = semis[1].slots.get(side=MatchSlot.HOME)
    assert (seed_slot.source_type, seed_slot.seed) == (MatchSlot.SOURCE_SEED, 1)


@pytest.mark.django_db
def test_extra_time_lengthens_knockout_slots(build_tournament):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE, knockout_draw_resolution='extra_time', extra_time_duration=10)
    _schedule(tournament)
    knockout = _knockout(tournament)
    semi = next(m for m in knockout if m.round == 4)
    final = next(m for m in knockout if m.round == 2)
    # semi -> rest slot -> final, each knockout slot includes extra time
    assert final.start_time - semi.start_time == 2 * (SLOT + timedelta(minutes=10))


@pytest.mark.django_db
def test_break_before_knockout_is_added(build_tournament):
    plain = build_tournament(TWO_GROUPS_OF_FIVE)
    with_break = build_tournament(TWO_GROUPS_OF_FIVE)
    _schedule(plain)
    _schedule(with_break, break_before_knockout=timedelta(minutes=30))

    first_ko = lambda t: min(m.start_time for m in _knockout(t))
    assert first_ko(with_break) - first_ko(plain) == timedelta(minutes=30)


@pytest.mark.django_db
def test_schedule_requires_clean_slate_and_fields(build_tournament):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE)
    _schedule(tournament)
    with pytest.raises(CompetitionError, match="already has a schedule"):
        _schedule(tournament)

    no_fields = build_tournament(TWO_GROUPS_OF_FIVE, fields=0)
    with pytest.raises(CompetitionError, match="Add at least one field"):
        _schedule(no_fields)


@pytest.mark.django_db
def test_groups_knockout_is_shorter_than_round_robin(build_tournament):
    """10 teams: two groups + semis + final instead of 45 round-robin matches."""
    tournament = build_tournament(TWO_GROUPS_OF_FIVE)
    _schedule(tournament)
    last = tournament.matches.order_by('-start_time').first().start_time
    assert last - START <= timedelta(hours=5)
