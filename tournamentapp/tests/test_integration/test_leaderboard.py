from django.test import TestCase, Client
from django.urls import reverse
from tournamentapp.models import Team, Player, Match, MatchEvent, Field
from django.utils import timezone
from datetime import timedelta

class LeaderboardIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Teams
        self.team1 = Team.objects.create(name="Team 1", tournament_points=6)
        self.team2 = Team.objects.create(name="Team 2", tournament_points=6)
        self.team3 = Team.objects.create(name="Team 3", tournament_points=3)

        # Create Field
        self.field = Field.objects.create(name="Field A")

        # Create Player with goals
        self.player = Player.objects.create(name="Player A", team=self.team1, goals=5)

        # Create Match between tied teams for tie-breaker
        self.match = Match.objects.create(
            home_team=self.team1,
            away_team=self.team2,
            start_time=timezone.now() - timedelta(days=1),
            is_finished=True,
            field=self.field
        )

        # Add goals (tie-breaker logic: Team 1 scores more in head-to-head)
        MatchEvent.objects.create(match=self.match, event_type='goal', team=self.team1)
        MatchEvent.objects.create(match=self.match, event_type='goal', team=self.team1)
        MatchEvent.objects.create(match=self.match, event_type='goal', team=self.team2)

    def test_leaderboard_view_loads(self):
        response = self.client.get(reverse('leaderboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Player A")
        self.assertContains(response, "Team 1")
        self.assertContains(response, "Team 2")
        self.assertContains(response, "Team 3")

    def test_top_scorers_listed(self):
        response = self.client.get(reverse('leaderboard'))
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()
        self.assertIn("Player A", content)
        self.assertIn("5 goal", content)

    def test_team_leaderboard_order_by_tiebreaker(self):
        response = self.client.get(reverse('leaderboard'))
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()
        first_occurrence = content.find("Team 1")
        second_occurrence = content.find("Team 2")
        self.assertTrue(first_occurrence != -1 and second_occurrence != -1)
        self.assertLess(first_occurrence, second_occurrence, msg="Team 1 should appear before Team 2 due to tie-breaker")

