import pytest
from django.urls import reverse
from django.utils import timezone
from programme.models import SideEvent

@pytest.mark.django_db
def test_side_events_returns_200(client, tournament):
    url = f'/api/tournaments/{tournament.slug}/side-events/'
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_side_events_returns_active_only(client, tournament):
    SideEvent.objects.create(tournament=tournament, name='Active', is_active=True)
    SideEvent.objects.create(tournament=tournament, name='Inactive', is_active=False)

    url = f'/api/tournaments/{tournament.slug}/side-events/'
    response = client.get(url)
    data = response.json()

    names = [v['name'] for v in data]
    assert 'Active' in names
    assert 'Inactive' not in names

@pytest.mark.django_db
def test_side_events_404_when_toggle_off(client, tournament):
    tournament.show_side_events = False
    tournament.save()

    url = f'/api/tournaments/{tournament.slug}/side-events/'
    response = client.get(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_side_events_no_auth_required(client, tournament):
    url = f'/api/tournaments/{tournament.slug}/side-events/'
    response = client.get(url)
    assert response.status_code == 200

@pytest.mark.django_db
def test_side_events_404_for_unknown_slug(client):
    url = '/api/tournaments/nonexistent/side-events/'
    response = client.get(url)
    assert response.status_code == 404

@pytest.mark.django_db
def test_side_event_fields(client, tournament):
    SideEvent.objects.create(
        tournament=tournament,
        name='Competition',
        description='Who can jump the longest distance',
        is_active=True
    )
    url = f'/api/tournaments/{tournament.slug}/side-events/'
    response = client.get(url)
    data = response.json()

    side_event = data[0]
    assert side_event['name'] == 'Competition'
    assert side_event['description'] == 'Who can jump the longest distance'
    assert side_event['is_active'] == True
