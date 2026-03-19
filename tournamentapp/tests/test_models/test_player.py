from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from tournamentapp.models import Player, Team, MatchEvent, GoalEvent, Match, Tournament, Field
from accounts.models import AppUser


class PlayerModelTests(TestCase):
    def setUp(self):
        self.user = AppUser.objects.create(
            email="testuser@abv.bg",
            password="password123"
        )
        self.tournament = Tournament.objects.create(
            name="testtournament",
            owner=self.user
        )
        self.team = Team.objects.create(
            name="Test Team",
            tournament=self.tournament
        )
        self.away_team = Team.objects.create(
            name="Second Team",
            tournament=self.tournament
        )
        self.player = Player.objects.create(
            name="John Doe",
            team=self.team
        )
        self.field = Field.objects.create(
            name="Main Field",
            owner=self.user,
            tournament=self.tournament
        )
        self.match = Match.objects.create(
            home_team=self.team,
            away_team=self.away_team,
            start_time=timezone.now() + timedelta(days=1),
            field=self.field,
            tournament=self.tournament
        )

    def test_str_method(self):
        expected_str = f"Player: {self.player.name} (Team: {self.team.name})"
        self.assertEqual(str(self.player), expected_str)

    def test_goals(self):
        MatchEvent.objects.create(
            match=self.match, event_type='goal',
            minute=10, team=self.team, player=self.player
        )
        MatchEvent.objects.create(
            match=self.match, event_type='goal',
            minute=20, team=self.team, player=self.player
        )
        self.assertEqual(self.player.goals(), 2)

    def test_own_goals(self):
        MatchEvent.objects.create(
            match=self.match, event_type='own_goal',
            minute=10, team=self.team, player=self.player
        )
        self.assertEqual(self.player.own_goals(), 1)

    def test_yellow_cards(self):
        MatchEvent.objects.create(
            match=self.match, event_type='yellow_card',
            minute=10, team=self.team, player=self.player
        )
        MatchEvent.objects.create(
            match=self.match, event_type='yellow_card',
            minute=20, team=self.team, player=self.player
        )
        self.assertEqual(self.player.yellow_cards(), 2)

    def test_red_cards(self):
        MatchEvent.objects.create(
            match=self.match, event_type='red_card',
            minute=10, team=self.team, player=self.player
        )
        self.assertEqual(self.player.red_cards(), 1)

    def test_not_suspended_with_no_cards(self):
        self.assertFalse(self.player.is_suspended())

    def test_suspended_with_red_card(self):
        MatchEvent.objects.create(
            match=self.match, event_type='red_card',
            minute=10, team=self.team, player=self.player
        )
        self.assertTrue(self.player.is_suspended)

    def test_suspended_with_two_yellow_cards(self):
        MatchEvent.objects.create(
            match=self.match, event_type='yellow_card',
            minute=10, team=self.team, player=self.player
        )
        MatchEvent.objects.create(
            match=self.match, event_type='yellow_card',
            minute=20, team=self.team, player=self.player
        )
        self.assertTrue(self.player.is_suspended())

    def test_not_suspended_with_one_yellow_card(self):
        MatchEvent.objects.create(
            match=self.match, event_type='yellow_card',
            minute=10, team=self.team, player=self.player
        )
        self.assertFalse(self.player.is_suspended())

    def test_stats_scoped_to_tournament(self):
        """Goals in a different tournament should not affect this tournament's stats."""
        other_tournament = Tournament.objects.create(
            name="Other Tournament",
            owner=self.user
        )
        other_team = Team.objects.create(
            name="Other Team",
            tournament=other_tournament
        )
        other_away_team = Team.objects.create(
            name="Other Away Team",
            tournament=other_tournament
        )
        other_field = Field.objects.create(
            name="Other Field",
            owner=self.user,
            tournament=other_tournament
        )
        other_player = Player.objects.create(
            name="John Doe",
            team=other_team
        )
        other_match = Match.objects.create(
            home_team=other_team,
            away_team=other_away_team,
            start_time=timezone.now() + timedelta(days=1),
            field=other_field,
            tournament=other_tournament
        )
        MatchEvent.objects.create(
            match=other_match, event_type='goal',
            minute=10, team=other_team, player=other_player
        )
        self.assertEqual(self.player.goals(), 0)