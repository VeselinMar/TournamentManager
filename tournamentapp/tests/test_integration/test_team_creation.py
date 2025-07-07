# from django.test import TestCase, Client
# from django.urls import reverse
# from tournamentapp.models import Team, Player, Match, GoalEvent, MatchEvent, Field
# from django.utils import timezone
# from datetime import timedelta

# class TeamCreateIntegrationTests(TestCase):
#     def setUp(self):
#         self.client = Client()

#     def test_create_team_view(self):
#         response = self.client.post(reverse('team_create'), {'name': 'New Team'})
#         self.assertEqual(response.status_code, 302)  # Redirect after success

#         team_exists = Team.objects.filter(name='New Team').exists()
#         self.assertTrue(team_exists)