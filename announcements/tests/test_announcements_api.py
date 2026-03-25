import pytest
from django.urls import reverse
from announcements.models import Announcement
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
def test_announcements_returns_200(client, tournament):
    url = f'/api/tournaments/{tournament.slug}/announcements/'
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_announcements_returns_active_only(client, tournament):
    now = timezone.now()

    # Should be returned
    Announcement.objects.create(
        tournament=tournament,
        message='Active',
        starts_at=now - timedelta(minutes=1),
        ends_at=now + timedelta(minutes=5),
        is_active=True
    )

    # Not returned (inactive flag)
    Announcement.objects.create(
        tournament=tournament,
        message='Inactive flag',
        starts_at=now - timedelta(minutes=1),
        ends_at=now + timedelta(minutes=5),
        is_active=False
    )

    # Not returned (expired)
    Announcement.objects.create(
        tournament=tournament,
        message='Expired',
        starts_at=now - timedelta(minutes=10),
        ends_at=now - timedelta(minutes=5),
        is_active=False
    )

    # Not returned (not started yet)
    Announcement.objects.create(
        tournament=tournament,
        message='Future',
        starts_at=now + timedelta(minutes=5),
        ends_at=now + timedelta(minutes=10),
        is_active=False
    )

    url = f'/api/tournaments/{tournament.slug}/announcements/'
    response = client.get(url)
    data = response.json()

    messages = [v['message'] for v in data]

    assert 'Active' in messages
    assert 'Inactive flag' not in messages
    assert 'Expired' not in messages
    assert 'Future' not in messages


@pytest.mark.django_db
def test_announcements_404_when_toggle_off(client, tournament):
    tournament.show_announcements = False
    tournament.save()

    url = f'/api/tournaments/{tournament.slug}/announcements/'
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_announcements_no_auth_required(client, tournament):
    url = f'/api/tournaments/{tournament.slug}/announcements/'
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_announcements_404_for_unknown_slug(client):
    url = '/api/tournaments/nonexistent/announcements/'
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_announcement_fields(client, tournament):
    now = timezone.now()

    Announcement.objects.create(
        tournament=tournament,
        message='EUREKA!',
        starts_at=now - timedelta(minutes=1),
        ends_at=now + timedelta(minutes=5),
        is_active=True
    )

    url = f'/api/tournaments/{tournament.slug}/announcements/'
    response = client.get(url)

    assert response.status_code == 200

    data = response.json()
    assert len(data) > 0

    vendor = data[0]

    assert vendor['message'] == 'EUREKA!'