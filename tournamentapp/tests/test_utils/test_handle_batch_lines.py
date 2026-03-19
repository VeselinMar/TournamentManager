import pytest
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory

from tournamentapp.models import Tournament, Team, Player
from tournamentapp.services import handle_batch_lines
from tournamentapp.forms import TeamCreateForm

@pytest.mark.django_db
def test_handle_batch_lines_creates_teams_and_players(django_user_model):
    user = django_user_model.objects.create_user(
        email="testuser@abv.bg",
        password="pass"
    )

    factory = RequestFactory()
    request = factory.get('/')
    
    # Add messages middleware to request
    setattr(request, 'session', {})
    messages_storage = FallbackStorage(request)
    setattr(request, '_messages', messages_storage)

    tournament = Tournament.objects.create(name="Test Tournament", owner_id=1, is_finished=False)

    lines = [
        "Alpha",
        "-Alice",
        "-Bob",
        "Beta",
        "-Charlie",
        "invalid line"
    ]

    created_teams, created_players = handle_batch_lines(request, tournament, lines)

    assert created_teams == 2
    assert created_players == 3

    # Check database
    alpha_team = Team.objects.get(name="Alpha")
    beta_team = Team.objects.get(name="Beta")
    assert alpha_team.tournament == tournament
    assert beta_team.tournament == tournament

    assert Player.objects.filter(team=alpha_team).count() == 2
    assert Player.objects.filter(team=beta_team).count() == 1

@pytest.mark.django_db
def test_handle_batch_lines_skips_invalid_player_names(django_user_model):
    
    user = django_user_model.objects.create_user(
        email="testuser@abv.bg",
        password="pass"
    )
    factory = RequestFactory()
    request = factory.get('/')
    setattr(request, 'session', {})
    messages_storage = FallbackStorage(request)
    setattr(request, '_messages', messages_storage)

    tournament = Tournament.objects.create(name="T", owner_id=1, is_finished=False)
    lines = ["Alpha", "-", "Beta"]

    created_teams, created_players = handle_batch_lines(request, tournament, lines)

    assert created_teams == 2
    assert created_players == 0