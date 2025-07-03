from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from tournamentapp.models import Player, Team, MatchEvent, GoalEvent, Match

class PlayerModelTests(TestCase):
    def setUp(self):
        self.team = Team.objects.create(name="Test Team")
        self.player = Player.objects.create(name="John Doe", team=self.team)

        # Create a match instance required by event models
        self.match = Match.objects.create(
            home_team=self.team,
            away_team=self.team,  # or create another team if needed
            start_time=timezone.now() + timedelta(days=1),
            field=None  # provide field if required, else allow null in model
        )

    def test_initial_eligibility(self):
        self.assertTrue(self.player.is_allowed_to_play)

    def test_update_eligibility_with_cards(self):
        self.player.red_cards = 0
        self.player.yellow_cards = 0
        self.player.update_eligibility()
        self.assertTrue(self.player.is_allowed_to_play)

        self.player.red_cards = 1
        self.player.yellow_cards = 0
        self.player.update_eligibility()
        self.assertFalse(self.player.is_allowed_to_play)

        self.player.red_cards = 0
        self.player.yellow_cards = 2
        self.player.update_eligibility()
        self.assertFalse(self.player.is_allowed_to_play)

    def test_save_updates_eligibility(self):
        self.player.red_cards = 1
        self.player.save()
        self.assertFalse(Player.objects.get(pk=self.player.pk).is_allowed_to_play)

    def test_apply_event_effects_goal_increments_goals(self):
        event = GoalEvent.objects.create(
            match=self.match,
            event_type='goal',
            minute=10,
            team=self.team,
            player=self.player
        )
        event.apply_event_effects()
        self.player.refresh_from_db()
        self.assertEqual(self.player.goals, 1)

    def test_apply_event_effects_own_goal_increments_own_goals(self):
        event = MatchEvent.objects.create(
            match=self.match,  # ensure this is valid match instance
            event_type='own_goal',
            minute=15,
            team=self.team,
            player=self.player
        )
        event.apply_event_effects()

        self.player.refresh_from_db()
        self.assertEqual(self.player.own_goals, 1)


    def test_apply_event_effects_yellow_card_increments_and_disables(self):
        event = MatchEvent.objects.create(
            match=self.match,
            event_type='yellow_card',
            minute=20,
            team=self.team,
            player=self.player
        )
        event.apply_event_effects()
        self.player.refresh_from_db()
        self.assertEqual(self.player.yellow_cards, 1)
        self.assertTrue(self.player.is_allowed_to_play)

        event2 = MatchEvent.objects.create(
            match=self.match,
            event_type='yellow_card',
            minute=21,
            team=self.team,
            player=self.player
        )
        event2.apply_event_effects()
        self.player.refresh_from_db()
        self.assertEqual(self.player.yellow_cards, 2)
        self.assertFalse(self.player.is_allowed_to_play)

    def test_apply_event_effects_red_card_increments_and_disables(self):
        event = MatchEvent.objects.create(
            match=self.match,
            event_type='red_card',
            minute=30,
            team=self.team,
            player=self.player
        )
        event.apply_event_effects()
        self.player.refresh_from_db()
        self.assertEqual(self.player.red_cards, 1)
        self.assertFalse(self.player.is_allowed_to_play)

    def test_str_method(self):
        expected_str = f"Player: {self.player.name} (Team: {self.team.name})"
        self.assertEqual(str(self.player), expected_str)
