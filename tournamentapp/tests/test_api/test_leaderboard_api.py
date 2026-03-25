import pytest
from django.utils import timezone
from datetime import timedelta
from tournamentapp.models import Match, Team, MatchEvent


@pytest.mark.django_db
def test_leaderboard_returns_200(client, tournament, field, team):
    url = f'/api/tournaments/{tournament.slug}/leaderboard/'
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_leaderboard_contains_standings(client, tournament, field, team):
    url = f'/api/tournaments/{tournament.slug}/leaderboard/'
    response = client.get(url)
    data = response.json()
    assert 'standings' in data
    assert 'top_scorers' in data


@pytest.mark.django_db
def test_leaderboard_shows_team_points(client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    team.tournament_points = 3
    team.save()

    url = f'/api/tournaments/{tournament.slug}/leaderboard/'
    response = client.get(url)
    data = response.json()

    team_entry = next(
        s for s in data['standings'] if s['team_name'] == team.name
    )
    assert team_entry['points'] == 3


@pytest.mark.django_db
def test_leaderboard_shows_top_scorers(client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    player = team.players.create(name="Scorer")
    MatchEvent.objects.create(
        match=match, event_type='goal',
        team=team, player=player, minute=10
    )

    url = f'/api/tournaments/{tournament.slug}/leaderboard/'
    response = client.get(url)
    data = response.json()

    assert any(s['player_name'] == 'Scorer' for s in data['top_scorers'])


@pytest.mark.django_db
def test_leaderboard_404_when_toggle_off(client, tournament):
    tournament.show_leaderboard = False
    tournament.save()

    url = f'/api/tournaments/{tournament.slug}/leaderboard/'
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_leaderboard_no_auth_required(client, tournament):
    url = f'/api/tournaments/{tournament.slug}/leaderboard/'
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_leaderboard_404_for_unknown_slug(client):
    url = '/api/tournaments/nonexistent/leaderboard/'
    response = client.get(url)
    assert response.status_code == 404