import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from announcements.models import Announcement


@pytest.mark.django_db
def test_create_announcement(auth_client, tournament):
    url = reverse('announcement-create', kwargs={'tournament_id': tournament.pk})
    starts = timezone.now() + timedelta(hours=1)
    ends = timezone.now() + timedelta(hours=2)
    response = auth_client.post(url, {
        'message': 'Match delayed by 10 minutes',
        'starts_at': starts.strftime('%Y-%m-%dT%H:%M'),
        'ends_at': ends.strftime('%Y-%m-%dT%H:%M'),
        'is_active': True,
    })
    assert response.status_code == 302
    assert Announcement.objects.filter(
        tournament=tournament,
        message='Match delayed by 10 minutes'
    ).exists()


@pytest.mark.django_db
def test_ends_at_must_be_after_starts_at(auth_client, tournament):
    url = reverse('announcement-create', kwargs={'tournament_id': tournament.pk})
    starts = timezone.now() + timedelta(hours=2)
    ends = timezone.now() + timedelta(hours=1)
    response = auth_client.post(url, {
        'message': 'Bad announcement',
        'starts_at': starts.strftime('%Y-%m-%dT%H:%M'),
        'ends_at': ends.strftime('%Y-%m-%dT%H:%M'),
        'is_active': True,
    })
    assert response.status_code == 200
    assert not Announcement.objects.filter(message='Bad announcement').exists()


@pytest.mark.django_db
def test_is_currently_active(tournament):
    now = timezone.now()
    ann = Announcement.objects.create(
        tournament=tournament,
        message='Active now',
        starts_at=now - timedelta(minutes=10),
        ends_at=now + timedelta(minutes=10),
        is_active=True
    )
    assert ann.is_currently_active is True


@pytest.mark.django_db
def test_is_not_currently_active_when_disabled(tournament):
    now = timezone.now()
    ann = Announcement.objects.create(
        tournament=tournament,
        message='Disabled',
        starts_at=now - timedelta(minutes=10),
        ends_at=now + timedelta(minutes=10),
        is_active=False
    )
    assert ann.is_currently_active is False


@pytest.mark.django_db
def test_is_not_currently_active_when_expired(tournament):
    now = timezone.now()
    ann = Announcement.objects.create(
        tournament=tournament,
        message='Expired',
        starts_at=now - timedelta(hours=2),
        ends_at=now - timedelta(hours=1),
        is_active=True
    )
    assert ann.is_currently_active is False


@pytest.mark.django_db
def test_announcement_scoped_to_tournament(auth_client, tournament, django_user_model):
    other_user = django_user_model.objects.create_user(
        email='other@test.com', password='pass'
    )
    from tournamentapp.models import Tournament
    other_tournament = Tournament.objects.create(
        name='Other', owner=other_user
    )
    ann = Announcement.objects.create(
        tournament=other_tournament,
        message='Other',
        starts_at=timezone.now(),
        ends_at=timezone.now() + timedelta(hours=1)
    )
    url = reverse('announcement-edit', kwargs={
        'tournament_id': tournament.pk,
        'pk': ann.pk
    })
    response = auth_client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_announcement_requires_owner(client, tournament, django_user_model):
    other = django_user_model.objects.create_user(
        email='other@test.com', password='pass'
    )
    client.force_login(other)
    url = reverse('announcement-create', kwargs={'tournament_id': tournament.pk})
    response = client.post(url, {
        'message': 'Hacked',
        'starts_at': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        'ends_at': (timezone.now() + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
        'is_active': True,
    })
    assert response.status_code == 404