from django.test import TestCase
from django.urls import reverse
from tournamentapp.models import Team, Match, Field
from django.utils import timezone
from datetime import timedelta

class HomeViewIntegrationTests(TestCase):
    def setUp(self):
        # Teams
        self.team1 = Team.objects.create(name="Team Alpha")
        self.team2 = Team.objects.create(name="Team Beta")
        self.team3 = Team.objects.create(name="Team Gamma")
        self.team4 = Team.objects.create(name="Team Delta")

        # Field
        self.field = Field.objects.create(name="Field A")

        # Matches:
        # 1) Two matches on same field, different times
        self.match1 = Match.objects.create(
            home_team=self.team1,
            away_team=self.team2,
            start_time=timezone.now() + timedelta(days=1, hours=10),
            field=self.field
        )
        self.match2 = Match.objects.create(
            home_team=self.team3,
            away_team=self.team4,
            start_time=timezone.now() + timedelta(days=1, hours=12),  # later on same day, same field
            field=self.field
        )

        # 2) Team playing two matches concurrently (should not be possible)
        self.field2 = Field.objects.create(name="Field B")
        concurrent_start = timezone.now() + timedelta(days=2, hours=15)
        self.match3 = Match.objects.create(
            home_team=self.team1,
            away_team=self.team3,
            start_time=concurrent_start,
            field=self.field
        )
        self.match4 = Match.objects.create(
            home_team=self.team1,
            away_team=self.team4,
            start_time=concurrent_start,  # same time as match3, different field
            field=self.field2
        )

    def test_homepage_displays_teams_and_matches(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('teams', response.context)
        self.assertIn('matches', response.context)

        teams = response.context['teams']
        self.assertTrue(any(team.name == "Team Alpha" for team in teams))
        self.assertTrue(any(team.name == "Team Beta" for team in teams))
        self.assertTrue(any(team.name == "Team Gamma" for team in teams))
        self.assertTrue(any(team.name == "Team Delta" for team in teams))

        matches = response.context['matches']

        # Check all created matches are present
        match_ids = set(match.id for match in matches)
        for m in [self.match1, self.match2, self.match3, self.match4]:
            self.assertIn(m.id, match_ids)

        # Check ordering by start_time ascending
        start_times = [m.start_time for m in matches]
        self.assertEqual(start_times, sorted(start_times))

        # Check matches on same field but different times
        same_field_matches = [m for m in matches if m.field == self.field]
        self.assertTrue(len(same_field_matches) >= 3)  # match1, match2, match3 all on field A

        # Check that a team appears in two concurrent matches (which is impossible in reality)
        concurrent_matches = [m for m in matches if m.start_time == self.match3.start_time]
        team1_matches_at_concurrent_time = [m for m in concurrent_matches if self.team1 in [m.home_team, m.away_team]]
        self.assertEqual(len(team1_matches_at_concurrent_time), 2)  # team1 plays 2 matches concurrently

        # Check flags
        self.assertFalse(response.context['no_teams'])
        self.assertFalse(response.context['no_matches'])

    def test_no_teams_or_matches_flags_when_empty(self):
        # Clear all data
        Team.objects.all().delete()
        Match.objects.all().delete()

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['no_teams'])
        self.assertTrue(response.context['no_matches'])

    def test_homepage_with_no_matches(self):
        # Clear matches but keep teams
        Match.objects.all().delete()

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['no_teams'])
        self.assertTrue(response.context['no_matches'])
