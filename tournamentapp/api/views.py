from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from tournamentapp.models import Tournament, Match, Team, Player
from .serializers import ScheduleSerializer, LeaderboardSerializer, TournamentMetaSerializer
from tournamentapp.utils import build_timeline, get_team_standings, get_group_tables, get_top_scorers
from tournamentapp import competition
from .caching import cached_response


def serialize_match(m):
    """Public representation of a match. Unknown knockout teams show their placeholder."""
    return {
        "id": m.pk,
        "stage": m.stage,
        "group": m.group.name if m.group_id else None,
        "round": m.round,
        "round_label": m.round_label,
        "is_third_place": m.is_third_place,
        "bracket_position": m.bracket_position,
        "home_team": m.home_label,
        "away_team": m.away_label,
        "home_placeholder": m.home_team_id is None,
        "away_placeholder": m.away_team_id is None,
        "field": m.field.name,
        "start_time": m.start_time.isoformat(),
        "home_score": m.home_score,
        "away_score": m.away_score,
        "home_penalties": m.home_penalties,
        "away_penalties": m.away_penalties,
        "decided_by": m.decided_by or None,
        "winner": m.winner.name if m.winner_id else None,
        "is_finished": m.is_finished,
    }


class ScheduleAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug__iexact=slug)
        return cached_response(request, tournament, "schedule", lambda: self.build(tournament))

    @staticmethod
    def build(tournament):
        timeline, field_names = build_timeline(tournament)

        rows = [
            {
                "time": row["time"],
                "datetime": row["datetime"].isoformat(),
                "matches": [serialize_match(m) if m else None for m in row["matches"]],
            }
            for row in timeline
        ]

        current_matches = (
            Match.objects.filter(tournament=tournament, is_finished=False)
            .select_related('field', 'home_team', 'away_team', 'group', 'winner')
            .prefetch_related('slots')
        )

        return {
            "field_names": field_names,
            "timeline": rows,
            "current_matches": [serialize_match(m) for m in current_matches],
        }


def _standing_row(team, rank, qualifies=False):
    return {
        'rank': rank,
        'team_name': team.name,
        'points': team.points,
        'played': team.played,
        'wins': team.wins,
        'draws': team.draws,
        'losses': team.losses,
        'goals_for': team.goals_for,
        'goals_against': team.goals_against,
        'goal_difference': team.goal_difference,
        'qualifies': qualifies,
    }


class LeaderboardAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug)

        if not tournament.show_leaderboard:
            return Response(
                {'detail': 'Leaderboard is not public for this tournament.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return cached_response(request, tournament, "leaderboard", lambda: self.build(tournament))

    @staticmethod
    def build(tournament):
        tables = get_group_tables(tournament)
        top_scorers = get_top_scorers(tournament)
        per_group = tournament.qualifiers_per_group if tournament.uses_groups else 0

        groups = [
            {
                'name': group.name if group else None,
                'qualifiers': per_group,
                'standings': [
                    _standing_row(team, index + 1, qualifies=index < per_group)
                    for index, team in enumerate(teams)
                ],
            }
            for group, teams in tables
        ]

        data = {
            'format': tournament.format,
            # Single table for round robin; group tables live in `groups`
            'standings': groups[0]['standings'] if not tournament.uses_groups else [],
            'groups': groups,
            'best_placed_qualifiers': tournament.best_placed_qualifiers if tournament.uses_groups else 0,
            'top_scorers': [
                {
                    'player_name': p.name,
                    'team_name': p.team.name,
                    'goals': p.goal_count,
                }
                for p in top_scorers
            ]
        }

        return LeaderboardSerializer(data).data


class BracketAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug)
        return cached_response(request, tournament, "bracket", lambda: self.build(tournament))

    @staticmethod
    def build(tournament):
        rounds = competition.bracket_rounds(tournament) if tournament.uses_groups else []
        return {
            'format': tournament.format,
            'rounds': [
                {
                    'round': r['round'],
                    'label': r['label'],
                    'matches': [serialize_match(m) for m in r['matches']],
                }
                for r in rounds
            ],
        }


class TournamentMetaAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug)
        return cached_response(
            request, tournament, "meta", lambda: TournamentMetaSerializer(tournament).data
        )