from django.test import TestCase
from tournamentapp.models import Player, Team, Field, Match
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

class TeamModelTests(TestCase):
    # Test cases for the Team model
    def test_team_creation(self):
        team = Team.objects.create(name="Lions FC")
        self.assertEqual(team.name, "Lions FC")
        self.assertEqual(team.match_points, 0)
        self.assertEqual(team.tournament_points, 0)
        self.assertFalse(team.logo)

    def test_team_str_representation(self):
        team = Team.objects.create(name="Bears FC")
        self.assertEqual(str(team), "Bears FC")
    
    def test_team_name_uniqueness(self):
        Team.objects.create(name="Tigers FC")
        with self.assertRaises(IntegrityError):
            Team.objects.create(name="Tigers FC")
    
    def test_add_match_points(self):
        team = Team.objects.create(name="Wolves FC")
        team.add_match_points(5)
        team.refresh_from_db()
        self.assertEqual(team.match_points, 5)

    def test_add_tournament_points(self):
        team = Team.objects.create(name="Eagles FC")
        team.add_tournament_points(3)
        team.refresh_from_db()
        self.assertEqual(team.tournament_points, 3)

    def test_point_incrementation_with_varied_totals(self):
        base_increments = [3, 1, 0]  # Win, draw, loss points
        num_teams = 10

        for i in range(num_teams):
            team = Team.objects.create(name=f"Team {i+1}")

            # Repeat the base pattern i+1 times for each team to vary totals:
            increments = base_increments * (i + 1)  

            for inc in increments:
                team.add_match_points(inc)

            team.refresh_from_db()

            expected_points = sum(increments)

            self.assertEqual(
                team.match_points,
                expected_points,
                f"{team.name} expected {expected_points} points but got {team.match_points}"
            )