import pytest
from sponsors.models import SponsorBanner


@pytest.mark.django_db
def test_meta_returns_200(client, tournament):
    url = f'/api/tournaments/{tournament.slug}/'
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_meta_contains_required_fields(client, tournament):
    url = f'/api/tournaments/{tournament.slug}/'
    response = client.get(url)
    data = response.json()
    assert 'name' in data
    assert 'slug' in data
    assert 'is_finished' in data
    assert 'show_leaderboard' in data
    assert 'show_vendors' in data
    assert 'show_side_events' in data
    assert 'show_announcements' in data
    assert 'sponsors' in data


@pytest.mark.django_db
def test_meta_reflects_tournament_name(client, tournament):
    url = f'/api/tournaments/{tournament.slug}/'
    response = client.get(url)
    data = response.json()
    assert data['name'] == tournament.name


@pytest.mark.django_db
def test_meta_reflects_visibility_toggles(client, tournament):
    tournament.show_vendors = False
    tournament.show_side_events = False
    tournament.save()

    url = f'/api/tournaments/{tournament.slug}/'
    response = client.get(url)
    data = response.json()
    assert data['show_vendors'] is False
    assert data['show_side_events'] is False
    assert data['show_leaderboard'] is True


@pytest.mark.django_db
def test_meta_includes_sponsors(client, tournament):
    SponsorBanner.objects.create(
        tournament=tournament,
        name='UniLED',
        link_url='https://uniled.bg'
    )
    url = f'/api/tournaments/{tournament.slug}/'
    response = client.get(url)
    data = response.json()
    assert any(s['name'] == 'UniLED' for s in data['sponsors'])


@pytest.mark.django_db
def test_meta_no_auth_required(client, tournament):
    url = f'/api/tournaments/{tournament.slug}/'
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_meta_404_for_unknown_slug(client):
    url = '/api/tournaments/nonexistent/'
    response = client.get(url)
    assert response.status_code == 404
