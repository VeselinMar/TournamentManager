from rest_framework import serializers
from tournamentapp.models import Match, Field


class MatchSerializer(serializers.ModelSerializer):
    home_team = serializers.StringRelatedField()
    away_team = serializers.StringRelatedField()
    field = serializers.StringRelatedField()

    class Meta:
        model = Match
        fields = [
            'id', 'home_team', 'away_team', 'field',
            'start_time', 'home_score', 'away_score',
            'is_finished',
        ]


class TimelineRowSerializer(serializers.Serializer):
    time = serializers.CharField()
    matches = MatchSerializer(many=True, allow_null=True)


class ScheduleSerializer(serializers.Serializer):
    field_names = serializers.ListField(child=serializers.CharField())
    timeline = TimelineRowSerializer(many=True)

class TopScorerSerializer(serializers.Serializer):
    player_name = serializers.CharField()
    team_name = serializers.CharField()
    goals = serializers.IntegerField()


class TeamStandingSerializer(serializers.Serializer):
    team_name = serializers.CharField()
    points = serializers.IntegerField()
    wins = serializers.IntegerField()
    draws = serializers.IntegerField()
    losses = serializers.IntegerField()
    goals_for = serializers.IntegerField()
    goals_against = serializers.IntegerField()
    goal_difference = serializers.IntegerField()


class LeaderboardSerializer(serializers.Serializer):
    standings = TeamStandingSerializer(many=True)
    top_scorers = TopScorerSerializer(many=True)