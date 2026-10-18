"""Qualification plan, seeding labels and bracket structure."""
import pytest

from tournamentapp.competition import (
    CompetitionError, bracket_order, qualifier_plan, random_draw, set_group_count,
)
from tournamentapp.models import Group, Team, Tournament

from .conftest import THREE_GROUPS_OF_THREE, TWO_GROUPS_OF_FIVE


def test_bracket_order_keeps_top_seeds_apart():
    assert bracket_order(2) == [1, 2]
    assert bracket_order(4) == [1, 4, 2, 3]
    assert bracket_order(8) == [1, 8, 4, 5, 2, 7, 3, 6]


@pytest.mark.django_db
def test_plan_two_groups_top_two(build_tournament):
    plan = qualifier_plan(build_tournament(TWO_GROUPS_OF_FIVE))
    assert (plan.total, plan.bracket_size, plan.byes) == (4, 4, 0)
    assert plan.seed_labels == ["Group winner #1", "Group winner #2", "Runner-up #1", "Runner-up #2"]


@pytest.mark.django_db
def test_plan_with_byes(build_tournament):
    plan = qualifier_plan(build_tournament(THREE_GROUPS_OF_THREE))
    assert (plan.total, plan.bracket_size, plan.byes) == (6, 8, 2)


@pytest.mark.django_db
def test_plan_with_best_placed_qualifiers(build_tournament):
    plan = qualifier_plan(build_tournament(THREE_GROUPS_OF_THREE, best_placed_qualifiers=2))
    assert (plan.total, plan.bracket_size, plan.byes) == (8, 8, 0)
    assert plan.seed_labels[-2:] == ["Best 3rd-placed #1", "Best 3rd-placed #2"]


@pytest.mark.django_db
def test_plan_single_group_uses_places(build_tournament):
    plan = qualifier_plan(build_tournament({'A': {'T1': 4, 'T2': 3, 'T3': 2, 'T4': 1}}, qualifiers_per_group=4))
    assert plan.seed_labels == ["1st place", "2nd place", "3rd place", "4th place"]


@pytest.mark.django_db
@pytest.mark.parametrize("groups, options, message", [
    ({}, {}, "Create at least one group"),
    ({'A': {'T1': 1}, 'B': {'T2': 1, 'T3': 1}}, {}, "at least 2 teams"),
    ({'A': {'T1': 1, 'T2': 1}}, {'qualifiers_per_group': 3}, "smallest group has only 2"),
    ({'A': {'T1': 1, 'T2': 1}}, {'qualifiers_per_group': 1}, "At least 2 teams must qualify"),
    ({'A': {'T1': 1, 'T2': 1, 'T3': 1}}, {'qualifiers_per_group': 3, 'best_placed_qualifiers': 1}, "at most 0"),
])
def test_plan_validation(build_tournament, groups, options, message):
    tournament = build_tournament(groups, **options)
    with pytest.raises(CompetitionError, match=message):
        qualifier_plan(tournament)


@pytest.mark.django_db
def test_plan_rejects_unassigned_teams(build_tournament):
    tournament = build_tournament(TWO_GROUPS_OF_FIVE)
    Team.objects.create(name="Late entry", tournament=tournament)
    with pytest.raises(CompetitionError, match="not assigned"):
        qualifier_plan(tournament)


@pytest.mark.django_db
def test_set_group_count_creates_and_removes_groups(tournament):
    teams = [Team.objects.create(name=f"T{i}", tournament=tournament) for i in range(6)]
    set_group_count(tournament, 3)
    assert [g.name for g in tournament.groups.all()] == ["A", "B", "C"]

    group_c = tournament.groups.get(name="C")
    teams[0].group = group_c
    teams[0].save()

    set_group_count(tournament, 2)
    assert [g.name for g in tournament.groups.all()] == ["A", "B"]
    teams[0].refresh_from_db()
    assert teams[0].group is None


@pytest.mark.django_db
def test_random_draw_is_balanced(tournament):
    for i in range(10):
        Team.objects.create(name=f"T{i}", tournament=tournament)
    set_group_count(tournament, 3)

    random_draw(tournament)

    sizes = sorted(g.teams.count() for g in tournament.groups.all())
    assert sizes == [3, 3, 4]
    assert not tournament.teams.filter(group__isnull=True).exists()


@pytest.mark.django_db
def test_groups_are_locked_once_scheduled(tournament, match):
    with pytest.raises(CompetitionError, match="Reset the schedule"):
        set_group_count(tournament, 2)
    with pytest.raises(CompetitionError, match="Reset the schedule"):
        random_draw(tournament)
