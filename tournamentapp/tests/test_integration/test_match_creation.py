from django.test import TestCase, Client
from django.urls import reverse
from tournamentapp.models import Team, Player, Match, GoalEvent, MatchEvent, Field
from django.utils import timezone
from datetime import timedelta

class MatchFlowIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.field = Field.objects.create(name="Main Field")
        self.team1 = Team.objects.create(name="Alpha")
        self.team2 = Team.objects.create(name="Beta")

    def test_create_match_and_view_detail(self):
        match_data = {
            'home_team': self.team1.id,
            'away_team': self.team2.id,
            'start_time': timezone.now() + timedelta(days=1),
            'field': self.field.id,
        }

        response = self.client.post(reverse('match-create'), match_data)
        self.assertEqual(response.status_code, 302)

        match = Match.objects.first()
        self.assertIsNotNone(match)

        # Visit match detail
        response = self.client.get(reverse('match-detail', kwargs={'pk': match.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha")
        self.assertContains(response, "Beta")
