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

    matches = generate_round_robin(tournament)

    # 4 teams → 4*3/2 = 6 unique matches
    assert len(matches) == 6

    for home, away in matches:
        assert home in teams
        assert away in teams
        assert home != away

    # Every team plays exactly n-1 = 3 times
    from collections import Counter
    participation = Counter(t for match in matches for t in match)
    assert all(count == 3 for count in participation.values())

    # No duplicate matchups (regardless of home/away order)
    pairs = {frozenset(m) for m in matches}
    assert len(pairs) == 6


@pytest.mark.django_db
def test_generate_round_robin_odd_teams(django_user_model):
    user = django_user_model.objects.create_user(
        email="testuser@abv.bg",
        password="pass"
    )
    tournament = Tournament.objects.create(name="T", owner=user)
    teams = [Team.objects.create(name=f"Team{i}", tournament=tournament) for i in range(3)]

    matches = generate_round_robin(tournament)

    # 3 teams → 3*2/2 = 3 unique matches, bye is internal
    assert len(matches) == 3

    for home, away in matches:
        assert home in teams
        assert away in teams
        assert home != away

    # No duplicate matchups
    pairs = {frozenset(m) for m in matches}
    assert len(pairs) == 3


@pytest.mark.django_db
def test_generate_round_robin_home_away_balance(django_user_model):
    user = django_user_model.objects.create_user(
        email="testuser@abv.bg",
        password="pass"
    )
    tournament = Tournament.objects.create(name="T", owner=user)
    teams = [Team.objects.create(name=f"Team{i}", tournament=tournament) for i in range(6)]

    matches = generate_round_robin(tournament)

    from collections import Counter
    home_counts = Counter(home for home, _ in matches)
    away_counts = Counter(away for _, away in matches)

    for team in teams:
        imbalance = abs(home_counts[team] - away_counts[team])
        assert imbalance <= 1, (
            f"{team} has home={home_counts[team]} away={away_counts[team]}"
        )