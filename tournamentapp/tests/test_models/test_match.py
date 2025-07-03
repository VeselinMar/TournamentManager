from django.test import TestCase
from tournamentapp.models import Player, Team, Field, Match, GoalEvent
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class MatchModelTests(TestCase):

    def setUp(self):
        self.team1 = Team.objects.create(name="Team A")
        self.team2 = Team.objects.create(name="Team B")
        self.field = Field.objects.create(name="Field 1")
        self.start_time = timezone.now() + timedelta(days=1)

        self.match = Match.objects.create(
            home_team=self.team1,
            away_team=self.team2,
            start_time=self.start_time,
            field=self.field
        )

        self.player1 = Player.objects.create(name="Player 1", team=self.team1)
        self.player2 = Player.objects.create(name="Player 2", team=self.team2)

    def test_create_match(self):
        self.assertEqual(self.match.home_team, self.team1)
        self.assertEqual(self.match.away_team, self.team2)
        self.assertEqual(self.match.field, self.field)
        self.assertEqual(self.match.home_score, 0)
        self.assertFalse(self.match.is_finished)

    def test_cannot_play_against_self(self):
        match = Match(
            home_team=self.team1,
            away_team=self.team1,
            start_time=self.start_time,
            field=self.field
        )
        with self.assertRaises(ValidationError):
            match.clean()

    def test_str_representation(self):
        self.assertEqual(str(self.match), "Team A vs Team B")

    def test_apply_result_home_win(self):
        GoalEvent.objects.create(match=self.match, team=self.team1, player=self.player1, minute=10)
        GoalEvent.objects.create(match=self.match, team=self.team1, player=self.player1, minute=20)
        GoalEvent.objects.create(match=self.match, team=self.team2, player=self.player2, minute=30)

        self.match.apply_result()
        self.match.refresh_from_db()
        self.team1.refresh_from_db()
        self.team2.refresh_from_db()

        self.assertEqual(self.match.home_score, 2)
        self.assertEqual(self.match.away_score, 1)
        self.assertEqual(self.team1.tournament_points, 3)
        self.assertEqual(self.team2.tournament_points, 0)
        self.assertTrue(self.match.is_finished)

    def test_apply_result_away_win(self):
        GoalEvent.objects.create(match=self.match, team=self.team1, player=self.player1, minute=5)
        GoalEvent.objects.create(match=self.match, team=self.team2, player=self.player2, minute=15)
        GoalEvent.objects.create(match=self.match, team=self.team2, player=self.player2, minute=25)
        GoalEvent.objects.create(match=self.match, team=self.team2, player=self.player2, minute=35)

        self.match.apply_result()
        self.match.refresh_from_db()
        self.team1.refresh_from_db()
        self.team2.refresh_from_db()

        self.assertEqual(self.match.home_score, 1)
        self.assertEqual(self.match.away_score, 3)
        self.assertEqual(self.team2.tournament_points, 3)
        self.assertEqual(self.team1.tournament_points, 0)
        self.assertTrue(self.match.is_finished)

    def test_apply_result_draw(self):
        GoalEvent.objects.create(match=self.match, team=self.team1, player=self.player1, minute=10)
        GoalEvent.objects.create(match=self.match, team=self.team2, player=self.player2, minute=12)

        self.match.apply_result()
        self.match.refresh_from_db()
        self.team1.refresh_from_db()
        self.team2.refresh_from_db()

        self.assertEqual(self.match.home_score, 1)
        self.assertEqual(self.match.away_score, 1)
        self.assertEqual(self.team1.tournament_points, 1)
        self.assertEqual(self.team2.tournament_points, 1)
        self.assertTrue(self.match.is_finished)

    def test_apply_result_only_once(self):
        GoalEvent.objects.create(match=self.match, team=self.team1, player=self.player1, minute=10)
        GoalEvent.objects.create(match=self.match, team=self.team2, player=self.player2, minute=10)

        self.match.apply_result()
        self.match.apply_result()

        self.match.refresh_from_db()
        self.team1.refresh_from_db()
        self.team2.refresh_from_db()

        self.assertEqual(self.team1.tournament_points, 1)
        self.assertEqual(self.team2.tournament_points, 1)
