"""Fixtures for Groups + Knockout tests."""
from datetime import datetime, timedelta

import pytest
from django.utils import timezone

from tournamentapp.models import Field, Group, Match, Team, Tournament
from tournamentapp.utils import recalculate_match_points

START = timezone.make_aware(datetime(2026, 6, 20, 10, 0))
GAME = timedelta(minutes=15)
PAUSE = timedelta(minutes=5)


@pytest.fixture
def build_tournament(user):
    """
    build_tournament({'A': {'A1': 50, ...}, 'B': {...}}, fields=2, **settings)

    Creates a Groups + Knockout tournament. Each team gets a strength;
    `play_group_stage` uses it to produce predictable results.
    """
    def _build(groups, fields=2, **settings):
        tournament = Tournament.objects.create(
            name=f"Cup {Tournament.objects.count() + 1}",
            owner=user,
            format=Tournament.GROUPS_KNOCKOUT,
            **settings,
        )
        tournament.strength = {}
        for order, (group_name, teams) in enumerate(groups.items()):
            group = Group.objects.create(tournament=tournament, name=group_name, order=order)
            for team_name, strength in teams.items():
                Team.objects.create(name=team_name, tournament=tournament, group=group)
                tournament.strength[team_name] = strength
        for index in range(fields):
            Field.objects.create(name=f"Field {index + 1}", tournament=tournament, owner=user)
        return tournament
    return _build


@pytest.fixture
def play_group_stage():
    """Finish every group match: the stronger team wins by the strength difference."""
    def _play(tournament, overrides=None):
        overrides = overrides or {}
        for match in tournament.matches.filter(stage=Match.STAGE_GROUP, is_finished=False):
            key = (match.home_team.name, match.away_team.name)
            if key in overrides:
                home, away = overrides[key]
            else:
                diff = tournament.strength[match.home_team.name] - tournament.strength[match.away_team.name]
                home, away = max(diff, 0), max(-diff, 0)
            recalculate_match_points(match, home, away)
    return _play


@pytest.fixture
def ko():
    """ko(tournament, round, position=1, third_place=False) -> knockout Match (fresh from DB)."""
    def _get(tournament, round_size, position=1, third_place=False):
        return (
            Match.objects.select_related('home_team', 'away_team', 'winner')
            .get(tournament=tournament, stage=Match.STAGE_KNOCKOUT, round=round_size,
                 bracket_position=position, is_third_place=third_place)
        )
    return _get


TWO_GROUPS_OF_FIVE = {
    'A': {'A1': 50, 'A2': 40, 'A3': 30, 'A4': 20, 'A5': 10},
    'B': {'B1': 45, 'B2': 37, 'B3': 25, 'B4': 15, 'B5': 5},
}
THREE_GROUPS_OF_THREE = {
    'A': {'A1': 60, 'A2': 40, 'A3': 10},
    'B': {'B1': 66, 'B2': 44, 'B3': 11},
    'C': {'C1': 72, 'C2': 48, 'C3': 12},
}
