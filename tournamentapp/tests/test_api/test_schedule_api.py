import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from tournamentapp.models import Match, Team


@pytest.mark.django_db
def test_schedule_returns_200(client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    url = f'/api/tournaments/{tournament.slug}/schedule/'
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_schedule_contains_field_names(client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    url = f'/api/tournaments/{tournament.slug}/schedule/'
    response = client.get(url)
    data = response.json()
    assert 'field_names' in data
    assert field.name in data['field_names']


@pytest.mark.django_db
def test_schedule_contains_timeline(client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    url = f'/api/tournaments/{tournament.slug}/schedule/'
    response = client.get(url)
    data = response.json()
    assert 'timeline' in data
    assert len(data['timeline']) > 0


@pytest.mark.django_db
def test_schedule_match_data(client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field,
        is_finished=False
    )
    url = f'/api/tournaments/{tournament.slug}/schedule/'
    response = client.get(url)
    data = response.json()
    first_match = next(
        m for row in data['timeline']
        for m in row['matches'] if m is not None
    )
    assert first_match['home_team'] == team.name
    assert first_match['away_team'] == away.name
    assert first_match['is_finished'] is False


@pytest.mark.django_db
def test_schedule_404_for_unknown_slug(client):
    url = '/api/tournaments/nonexistent-slug/schedule/'
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_schedule_no_auth_required(client, tournament):
    url = f'/api/tournaments/{tournament.slug}/schedule/'
    response = client.get(url)
    assert response.status_code == 200