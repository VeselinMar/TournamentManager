import pytest
from tournamentapp.utils import generate_round_robin
from tournamentapp.models import Tournament, Team

@pytest.mark.django_db
def test_generate_round_robin_even_teams(django_user_model):
    user = django_user_model.objects.create_user(
        email="testuser@abv.bg",
        password="pass"
    )
    tournament = Tournament.objects.create(name="T", owner=user)
    teams = [Team.objects.create(name=f"Team{i}", tournament=tournament) for i in range(4)]

    rounds = generate_round_robin(tournament)
    assert len(rounds) == 3  # n-1 rounds
    for round_matches in rounds:
        # Each round should have n/2 matches
        assert len(round_matches) == 2
        for home, away in round_matches:
            assert home in teams
            assert away in teams
            assert home != away

@pytest.mark.django_db
def test_generate_round_robin_odd_teams(django_user_model):
    user = django_user_model.objects.create_user(
        email="testuser@abv.bg",
        password="pass"
    )
    tournament = Tournament.objects.create(name="T", owner=user)
    teams = [Team.objects.create(name=f"Team{i}", tournament=tournament) for i in range(3)]

    rounds = generate_round_robin(tournament)
    # should handle "bye" without errors
    total_matches = sum(len(r) for r in rounds)
    assert total_matches == 3  # 3 matches total for 3 teams