# from django.test import TestCase, Client
# from django.urls import reverse
# from tournamentapp.models import Team, Player, Match, GoalEvent, MatchEvent, Field
# from django.utils import timezone
# from datetime import timedelta

# class TopScorersIntegrationTests(TestCase):
#     def setUp(self):
#         self.client = Client()
#         team = Team.objects.create(name="Team A")
#         player = Player.objects.create(name="Player A", team=team, goals=5)

#     def test_top_scorers_view(self):
#         response = self.client.get(reverse('top_scorers'))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, "Player A")
