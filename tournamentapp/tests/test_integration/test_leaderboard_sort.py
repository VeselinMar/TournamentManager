from django.test import TestCase, Client
from django.urls import reverse
from tournamentapp.models import Team, Player, Match, GoalEvent, MatchEvent, Field
from django.utils import timezone
from datetime import timedelta

class TeamLeaderboardIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.team1 = Team.objects.create(name="Team 1", tournament_points=6)
        self.team2 = Team.objects.create(name="Team 2", tournament_points=6)

        self.match = Match.objects.create(
            home_team=self.team1,
            away_team=self.team2,
            start_time=timezone.now() - timedelta(days=1),
            is_finished=True,
            field=Field.objects.create(name="Field A")
        )

        # Add goals for tie-breaker
        MatchEvent.objects.create(match=self.match, event_type='goal', team=self.team1)
        MatchEvent.objects.create(match=self.match, event_type='goal', team=self.team1)
        MatchEvent.objects.create(match=self.match, event_type='goal', team=self.team2)

    def test_team_leaderboard_order(self):
        response = self.client.get(reverse('team-leaderboard'))
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()
        first_occurrence = content.find("Team 1")
        second_occurrence = content.find("Team 2")
        self.assertLess(first_occurrence, second_occurrence)  # Team 1 should be ranked higher
