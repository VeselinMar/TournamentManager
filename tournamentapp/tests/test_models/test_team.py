from django.test import TestCase
from tournamentapp.models import Player, Team, Field, Match, Tournament
from accounts.models import AppUser
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

class TeamModelTests(TestCase):
    def setUp(self):
        self.user = AppUser.objects.create(
            email = 'testuser@abv.bg',
            password = 'password123'
        )
        self.tournament = Tournament.objects.create(
            name="AnimalsTournament",
            owner = self.user
            )

    def test_team_creation(self):
        team = Team.objects.create(name="Lions FC", tournament=self.tournament)
        self.assertEqual(team.name, "Lions FC")
        self.assertIsNone(team.group)
        self.assertFalse(team.logo)

    def test_team_str_representation(self):
        team = Team.objects.create(name="Bears FC", tournament=self.tournament)
        self.assertEqual(str(team), "Bears FC")
    
    def test_team_name_uniqueness(self):
        Team.objects.create(name="Tigers FC", tournament=self.tournament)
        with self.assertRaises(IntegrityError):
            Team.objects.create(name="Tigers FC")
    
    def test_team_can_be_assigned_to_group(self):
        from tournamentapp.models import Group
        group = Group.objects.create(tournament=self.tournament, name="A")
        team = Team.objects.create(name="Owls FC", tournament=self.tournament, group=group)
        self.assertEqual(list(group.teams.all()), [team])

    def test_deleting_group_keeps_team(self):
        from tournamentapp.models import Group
        group = Group.objects.create(tournament=self.tournament, name="A")
        team = Team.objects.create(name="Owls FC", tournament=self.tournament, group=group)
        group.delete()
        team.refresh_from_db()
        self.assertIsNone(team.group)