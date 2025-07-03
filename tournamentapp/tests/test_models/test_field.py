from django.test import TestCase
from tournamentapp.models import Player, Team, Field, Match
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta


# Test cases for the Team model in the tournamentapp

class FieldModelTests(TestCase):
    # Test cases for the Field model
    def test_create_field(self):
        field = Field.objects.create(name="Main Pitch")
        self.assertEqual(field.name, "Main Pitch")
        self.assertEqual(Field.objects.count(), 1)

    def test_field_name_uniqueness(self):
        Field.objects.create(name="Field A")
        with self.assertRaises(IntegrityError):
            Field.objects.create(name="Field A")

    def test_str_representation(self):
        field = Field.objects.create(name="Court 2")
        self.assertEqual(str(field), "Court 2")