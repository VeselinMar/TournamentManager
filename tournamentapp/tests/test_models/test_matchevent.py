from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

from tournamentapp.models import Team, Player, Match, Field, MatchEvent, GoalEvent, Tournament
from accounts.models import AppUser


class MatchEventTests(TestCase):

    def setUp(self):
        self.user = AppUser.objects.create(
            email="testuser@abv.bg",
            password="password123"
            )

        self.tournament = Tournament.objects.create(
            name="Musterment",
            owner=self.user
            )

        self.team1 = Team.objects.create(
            name="Team Alpha",
            tournament=self.tournament,
        )
        self.team2 = Team.objects.create(
            name="Team Beta",
            tournament=self.tournament,
        )
        self.field = Field.objects.create(
            name="Field A",
            tournament=self.tournament,
            owner=self.user
        )

        self.player1 = Player.objects.create(
            name="Player A", team=self.team1
        )
        self.player2 = Player.objects.create(
            name="Player B", team=self.team2
        )

        self.match = Match.objects.create(
            home_team=self.team1,
            away_team=self.team2,
            start_time=timezone.now() + timedelta(days=1),
            field=self.field,
            tournament = self.tournament
        )

    def test_create_general_event(self):
        event = MatchEvent.objects.create(
            match=self.match,
            event_type='yellow_card',
            team=self.team1,
            player=self.player1,
            minute=15
        )
        self.assertEqual(event.event_type, 'yellow_card')
        self.assertEqual(event.player, self.player1)
        self.assertEqual(event.match, self.match)
        self.assertEqual(event.minute, 15)

    def test_str_representation(self):
        event = MatchEvent.objects.create(
            match=self.match,
            event_type='yellow_card',
            team=self.team1,
            player=self.player1,
            minute=10
        )
        self.assertIn("Yellow Card", str(event))
        self.assertIn("Player A", str(event))
        self.assertIn("Team Alpha", str(event))

    def test_goal_event_proxy_creation(self):
        goal = GoalEvent.objects.create(
            match=self.match,
            team=self.team1,
            player=self.player1,
            minute=22
        )
        self.assertEqual(goal.event_type, 'goal')
        self.assertEqual(str(goal), f"GOAL: {self.player1} for {self.team1} in {self.match}")

    def test_goal_cannot_be_assigned_to_suspended_player(self):
        suspended = Player.objects.create(name="Suspended", team=self.team1, red_cards=1)
        suspended.save()
        self.assertFalse(suspended.is_allowed_to_play)
        with self.assertRaises(ValidationError):
            GoalEvent.objects.create(
                match=self.match,
                team=self.team1,
                player=suspended,
                minute=33
            )

    def test_goal_queryset_only_returns_goals(self):
        MatchEvent.objects.create(match=self.match, event_type='yellow_card', team=self.team1, player=self.player1)
        GoalEvent.objects.create(match=self.match, team=self.team1, player=self.player1)
        GoalEvent.objects.create(match=self.match, team=self.team2, player=self.player2)

        self.assertEqual(MatchEvent.objects.count(), 3)
        self.assertEqual(GoalEvent.objects.count(), 2)

    def test_event_without_player(self):
        event = MatchEvent.objects.create(
            match=self.match,
            event_type='substitution',
            team=self.team1,
            minute=55,
            player=None
        )
        self.assertIsNone(event.player)

    def test_event_ordering_by_minute_then_created_at(self):
        MatchEvent.objects.create(match=self.match, event_type='goal', team=self.team1, player=self.player1, minute=10)
        MatchEvent.objects.create(match=self.match, event_type='yellow_card', team=self.team1, player=self.player1, minute=5)
        MatchEvent.objects.create(match=self.match, event_type='red_card', team=self.team1, player=self.player1, minute=15)

        events = list(MatchEvent.objects.all())
        self.assertEqual(events[0].minute, 5)
        self.assertEqual(events[1].minute, 10)
        self.assertEqual(events[2].minute, 15)

    def test_own_goal_event(self):
        event = MatchEvent.objects.create(
            match=self.match,
            event_type='own_goal',
            team=self.team1,
            player=self.player1,
            minute=40
        )
        self.assertEqual(event.event_type, 'own_goal')
        self.assertIn("Own Goal", str(event))
    
    def test_substitution_event(self):
        sub_in = Player.objects.create(name="Sub In", team=self.team1)
        event = MatchEvent.objects.create(
            match=self.match,
            event_type='substitution',
            team=self.team1,
            player=self.player1,
            substitute_player=sub_in,
            minute=60
        )
        self.assertEqual(event.event_type, 'substitution')
        self.assertEqual(event.substitute_player, sub_in)
        self.assertIn("Substitution", str(event))
        self.assertIn("Player A", str(event))
        self.assertIn("Sub In", str(event))

    def test_substitution_requires_same_team(self):
        sub_in = Player.objects.create(name="Wrong Team", team=self.team2)
        with self.assertRaisesMessage(ValidationError, "Substitute must be from the same team"):
            MatchEvent.objects.create(
                match=self.match,
                event_type='substitution',
                team=self.team1,
                player=self.player1,
                substitute_player=sub_in,
                minute=65
            ).full_clean()