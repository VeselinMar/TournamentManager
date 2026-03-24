import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from programme.models import SideEvent


@pytest.mark.django_db
def test_create_side_event(auth_client, tournament):
    url = reverse('sideevent-create', kwargs={'tournament_id': tournament.pk})
    start = timezone.now() + timedelta(hours=2)
    response = auth_client.post(url, {
        'name': 'Raffle',
        'description': 'Win prizes',
        'start_time': start.strftime('%Y-%m-%dT%H:%M'),
        'location': 'Main Stage',
        'is_active': True,
    })
    assert response.status_code == 302
    assert SideEvent.objects.filter(tournament=tournament, name='Raffle').exists()


@pytest.mark.django_db
def test_end_time_must_be_after_start_time(auth_client, tournament):
    url = reverse('sideevent-create', kwargs={'tournament_id': tournament.pk})
    start = timezone.now() + timedelta(hours=2)
    end = timezone.now() + timedelta(hours=1)
    response = auth_client.post(url, {
        'name': 'Bad Event',
        'start_time': start.strftime('%Y-%m-%dT%H:%M'),
        'end_time': end.strftime('%Y-%m-%dT%H:%M'),
        'is_active': True,
    })
    assert response.status_code == 200
    assert not SideEvent.objects.filter(name='Bad Event').exists()


@pytest.mark.django_db
def test_side_event_scoped_to_tournament(auth_client, tournament, django_user_model):
    other_user = django_user_model.objects.create_user(
        email='other@test.com', password='pass'
    )
    from tournamentapp.models import Tournament
    other_tournament = Tournament.objects.create(
        name='Other', owner=other_user
    )
    event = SideEvent.objects.create(
        tournament=other_tournament,
        name='Other Event',
        start_time=timezone.now() + timedelta(hours=1)
    )
    url = reverse('sideevent-edit', kwargs={
        'tournament_id': tournament.pk,
        'pk': event.pk
    })
    response = auth_client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_side_event(auth_client, tournament):
    event = SideEvent.objects.create(
        tournament=tournament,
        name='Awards',
        start_time=timezone.now() + timedelta(hours=3)
    )
    url = reverse('sideevent-delete', kwargs={
        'tournament_id': tournament.pk,
        'pk': event.pk
    })
    response = auth_client.post(url)
    assert response.status_code == 302
    assert not SideEvent.objects.filter(pk=event.pk).exists()


@pytest.mark.django_db
def test_sideevent_requires_owner(client, tournament, django_user_model):
    other = django_user_model.objects.create_user(
        email='other@test.com', password='pass'
    )
    client.force_login(other)
    url = reverse('sideevent-create', kwargs={'tournament_id': tournament.pk})
    response = client.post(url, {
        'name': 'Hacked',
        'start_time': timezone.now().strftime('%Y-%m-%dT%H:%M'),
        'is_active': True,
    })
    assert response.status_code == 404