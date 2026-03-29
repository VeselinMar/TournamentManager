from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import datetime
from django.shortcuts import get_object_or_404
from django.db.models import Q
from tournamentapp.models import Tournament, Match
from .serializers import ScheduleSerializer, LeaderboardSerializer, TournamentMetaSerializer
from tournamentapp.utils import build_timeline, get_team_standings, get_top_scorers


class ScheduleAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug__iexact=slug)
        timeline, field_names = build_timeline(tournament)

        rows = []
        for row in timeline:
            rows.append({
                "time": row["time"],
                "matches": [
                    {
                        "id": m.pk,
                        "home_team": m.home_team.name,
                        "away_team": m.away_team.name,
                        "field": m.field.name,
                        "start_time": m.start_time.isoformat(),
                        "home_score": m.home_score,
                        "away_score": m.away_score,
                        "is_finished": m.is_finished,
                    } if m else None
                    for m in row["matches"]
                ]
            })

        current_matches = Match.objects.filter(
            tournament=tournament,
            is_finished=False,
        ).select_related('field', 'home_team', 'away_team')

        return Response({
            "field_names": field_names,
            "timeline": rows,
            "current_matches": [
                {
                    "id": m.pk,
                    "home_team": m.home_team.name,
                    "away_team": m.away_team.name,
                    "field": m.field.name,
                    "home_score": m.home_score,
                    "away_score": m.away_score,
                }
                for m in current_matches
            ]
        })
        
class LeaderboardAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug)

        if not tournament.show_leaderboard:
            return Response(
                {'detail': 'Leaderboard is not public for this tournament.'},
                status=status.HTTP_404_NOT_FOUND
            )
        finished_matches = Match.objects.filter(
            tournament=tournament,
            is_finished=True
        ).select_relater("home_team", "away_team")

        teams = get_team_standings(tournament)
        top_scorers = get_top_scorers(tournament)

        standings = []
        for team in teams:
            finished = Match.objects.filter(
                tournament=tournament,
                is_finished=True
            ).filter(
                Q(home_team=team) | Q(away_team=team)
            )

            wins = draws = losses = goals_for = goals_against = 0
            for m in finished:
                is_home = m.home_team_id == team.id
                gf = m.home_score if is_home else m.away_score
                ga = m.away_score if is_home else m.home_score
                goals_for += gf
                goals_against += ga
                if gf > ga:
                    wins += 1
                elif gf == ga:
                    draws += 1
                else:
                    losses += 1

            standings.append({
                'team_name': team.name,
                'points': team.tournament_points,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'goals_for': goals_for,
                'goals_against': goals_against,
                'goal_difference': goals_for - goals_against,
            })

        data = {
            'standings': standings,
            'top_scorers': [
                {
                    'player_name': p.name,
                    'team_name': p.team.name,
                    'goals': p.goal_count,
                }
                for p in top_scorers
            ]
        }

        serializer = LeaderboardSerializer(data)
        return Response(serializer.data)

class TournamentMetaAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        tournament = get_object_or_404(Tournament, slug=slug).prefetch_related("sponsors").get(slug=slug)
        serializer = TournamentMetaSerializer(tournament)
        return Response(serializer.data)