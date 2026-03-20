import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, time, date
from tournamentapp.models import Match, Team, Field, MatchEvent


@pytest.mark.django_db
def test_edit_match_start_time(auth_client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now().replace(hour=10, minute=0, second=0, microsecond=0),
        field=field
    )
    url = reverse('edit-match', kwargs={
        'tournament_id': tournament.pk,
        'match_id': match.pk
    })
    response = auth_client.post(url, {
        'start_time': '11:00',
        'field': field.pk,
        'propagate': False
    })
    assert response.status_code == 302
    match.refresh_from_db()
    assert match.start_time.hour == 11
    assert match.start_time.minute == 0


@pytest.mark.django_db
def test_edit_match_field(auth_client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    new_field = Field.objects.create(
        name="Second Field",
        tournament=tournament,
        owner=tournament.owner
    )
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    url = reverse('edit-match', kwargs={
        'tournament_id': tournament.pk,
        'match_id': match.pk
    })
    response = auth_client.post(url, {
        'start_time': match.start_time.strftime('%H:%M'),
        'field': new_field.pk,
        'propagate': False
    })
    assert response.status_code == 302
    match.refresh_from_db()
    assert match.field == new_field


@pytest.mark.django_db
def test_delete_unfinished_match(auth_client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    url = reverse('delete-match', kwargs={
        'tournament_id': tournament.pk,
        'match_id': match.pk
    })
    response = auth_client.post(url)
    assert response.status_code == 302
    assert not Match.objects.filter(pk=match.pk).exists()


@pytest.mark.django_db
def test_delete_finished_match_blocked(auth_client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field,
        is_finished=True
    )
    url = reverse('delete-match', kwargs={
        'tournament_id': tournament.pk,
        'match_id': match.pk
    })
    response = auth_client.post(url)
    assert response.status_code == 302
    assert Match.objects.filter(pk=match.pk).exists()


@pytest.mark.django_db
def test_edit_match_requires_owner(client, tournament, field, team, django_user_model):
    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    other = django_user_model.objects.create_user(
        email='other@test.com', password='pass'
    )
    client.force_login(other)
    url = reverse('edit-match', kwargs={
        'tournament_id': tournament.pk,
        'match_id': match.pk
    })
    response = client.post(url, {
        'start_time': '12:00',
        'field': field.pk,
        'propagate': False
    })
    assert response.status_code == 404