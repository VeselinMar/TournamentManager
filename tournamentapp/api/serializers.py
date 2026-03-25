from rest_framework import serializers
from tournamentapp.models import Match, Field, Tournament


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

class TournamentMetaSerializer(serializers.ModelSerializer):
    is_finished = serializers.BooleanField()
    sponsors = serializers.SerializerMethodField()

    class Meta:
        model = Tournament
        fields = [
            'name', 'slug', 'is_finished', 'tournament_date',
            'show_leaderboard', 'show_vendors', 'show_side_events', 'show_announcements',
            'sponsors'
        ]

    def get_sponsors(self, obj):
        return [
            {
                'name': s.name,
                'image_url': s.image.url if s.image else None,
                'link_url': s.link_url,
            }
            for s in obj.sponsors.all()
        ]