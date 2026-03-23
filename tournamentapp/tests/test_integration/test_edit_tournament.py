import pytest
from django.urls import reverse
from tournamentapp.models import Tournament


@pytest.mark.django_db
def test_rename_tournament(auth_client, tournament):
    url = reverse('tournament-edit', kwargs={'pk': tournament.pk})
    response = auth_client.post(url, {
        'name': 'New Name',
        'tournament_date': '',
        'points_for_win': 3,
        'points_for_draw': 1,
        'yellow_cards_for_suspension': 2,
    })
    assert response.status_code == 302
    tournament.refresh_from_db()
    assert tournament.name == 'New Name'
    assert tournament.slug == 'new-name'


@pytest.mark.django_db
def test_rename_slug_collision(auth_client, tournament, django_user_model):
    # create another tournament with the target name's slug
    other_user = django_user_model.objects.create_user(
        email='other@test.com', password='pass'
    )
    Tournament.objects.create(name='New Name', owner=other_user, slug='new-name')
    url = reverse('tournament-edit', kwargs={'pk': tournament.pk})
    response = auth_client.post(url, 
        {'name': 'New Name', 
        'tournament_date': '',
        'points_for_win': 3,
        'points_for_draw': 1,
        'yellow_cards_for_suspension': 2,
        })
    assert response.status_code == 302
    tournament.refresh_from_db()
    assert tournament.slug == 'new-name-1'


@pytest.mark.django_db
def test_edit_tournament_requires_owner(client, tournament, django_user_model):
    other_user = django_user_model.objects.create_user(
        email='other@test.com', password='pass'
    )
    client.force_login(other_user)
    url = reverse('tournament-edit', kwargs={'pk': tournament.pk})
    response = client.post(url, {
        'name': 'Hacked',
        'tournament_date': '',
        'points_for_win': 3,
        'points_for_draw': 1,
        'yellow_cards_for_suspension': 2,
    })
    assert response.status_code == 404
    tournament.refresh_from_db()
    assert tournament.name != 'Hacked'

@pytest.mark.django_db
def test_reschedule_tournament(auth_client, tournament):
    url = reverse('tournament-edit', kwargs={'pk': tournament.pk})
    response = auth_client.post(url, 
    {'name': tournament.name,
     'tournament_date': '2026-06-15',
     'points_for_win': 3,
     'points_for_draw': 0,
     'yellow_cards_for_suspension': 2,
     })
    assert response.status_code == 302
    tournament.refresh_from_db()
    assert str(tournament.tournament_date) == '2026-06-15'