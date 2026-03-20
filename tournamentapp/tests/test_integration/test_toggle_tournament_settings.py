import pytest
from django.urls import reverse
from tournamentapp.models import Tournament


@pytest.mark.django_db
def test_finish_tournament(auth_client, tournament):
    assert tournament.is_finished is False
    url = reverse('toggle-tournament-status', kwargs={'pk': tournament.pk})
    response = auth_client.post(url)
    assert response.status_code == 302
    tournament.refresh_from_db()
    assert tournament.is_finished is True


@pytest.mark.django_db
def test_reopen_tournament(auth_client, tournament):
    tournament.is_finished = True
    tournament.save()
    url = reverse('toggle-tournament-status', kwargs={'pk': tournament.pk})
    response = auth_client.post(url)
    assert response.status_code == 302
    tournament.refresh_from_db()
    assert tournament.is_finished is False


@pytest.mark.django_db
def test_toggle_requires_owner(client, tournament, django_user_model):
    other_user = django_user_model.objects.create_user(
        email='other@test.com', password='pass'
    )
    client.force_login(other_user)
    url = reverse('toggle-tournament-status', kwargs={'pk': tournament.pk})
    response = client.post(url)
    assert response.status_code == 404
    tournament.refresh_from_db()
    assert tournament.is_finished is False


@pytest.mark.django_db
def test_toggle_requires_post(auth_client, tournament):
    url = reverse('toggle-tournament-status', kwargs={'pk': tournament.pk})
    response = auth_client.get(url)
    assert response.status_code == 405
    tournament.refresh_from_db()
    assert tournament.is_finished is False