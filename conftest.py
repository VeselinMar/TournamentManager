import pytest
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from tournamentapp.models import Tournament, Team, Field, Match

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="owner@test.com",
        password="pass"
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email="other@test.com",
        password="pass"
    )


@pytest.fixture
def auth_client(client, user):
    client.login(email="owner@test.com", password="pass")
    return client


@pytest.fixture
def tournament(user):
    return Tournament.objects.create(
        name="Test Tournament",
        owner=user
    )


@pytest.fixture
def team(tournament):
    return Team.objects.create(name="Team A", tournament=tournament)


@pytest.fixture
def field(tournament, user):
    return Field.objects.create(
        name="Main Field",
        tournament=tournament,
        owner=user
    )


@pytest.fixture
def match(tournament, team, field):
    opponent = Team.objects.create(name="Team B", tournament=tournament)
    return Match.objects.create(
        tournament=tournament,
        home_team=team,
        away_team=opponent,
        field=field,
        start_time=timezone.now()
    )