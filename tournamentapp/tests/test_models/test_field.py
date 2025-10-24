from django.test import TestCase
from tournamentapp.models import Player, Team, Field, Match, Tournament
from accounts.models import AppUser
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta


class FieldModelTests(TestCase):
    def setUp(self):
        self.user = AppUser.objects.create(
            email="testuser@abv.bg",
            password="testpass123"
        )
        self.tournament = Tournament.objects.create(
            name="Musterment",
            owner=self.user
        )

    def test_create_field(self):
        field = Field.objects.create(
            name="Main Pitch",
            owner=self.user,
            tournament=self.tournament
            )
        self.assertEqual(field.name, "Main Pitch")
        self.assertEqual(Field.objects.count(), 1)

    def test_field_name_uniqueness(self):
        Field.objects.create(
            name="Field A",
            owner=self.user,
            tournament=self.tournament
            )
        with self.assertRaises(IntegrityError):
            Field.objects.create(name="Field A")

    def test_str_representation(self):
        field = Field.objects.create(
            name="Court 2",
            owner=self.user,
            tournament=self.tournament
            )
        self.assertEqual(str(field), "Court 2")