import pytest
from django.urls import reverse
from vendors.models import Vendor


@pytest.mark.django_db
def test_create_vendor(auth_client, tournament):
    url = reverse('vendor-create', kwargs={'tournament_id': tournament.pk})
    response = auth_client.post(url, {
        'name': 'Hot Dogs',
        'description': 'Best hot dogs in town',
        'category': 'Food',
        'venue_location': 'Gate A',
        'is_active': True,
    })
    assert response.status_code == 302
    assert Vendor.objects.filter(tournament=tournament, name='Hot Dogs').exists()


@pytest.mark.django_db
def test_vendor_scoped_to_tournament(auth_client, tournament, django_user_model):
    other_user = django_user_model.objects.create_user(
        email='other@test.com', password='pass'
    )
    from tournamentapp.models import Tournament
    other_tournament = Tournament.objects.create(
        name='Other Tournament', owner=other_user
    )
    vendor = Vendor.objects.create(
        tournament=other_tournament,
        name='Other Vendor'
    )
    url = reverse('vendor-edit', kwargs={
        'tournament_id': tournament.pk,
        'pk': vendor.pk
    })
    response = auth_client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_vendor(auth_client, tournament):
    vendor = Vendor.objects.create(tournament=tournament, name='Burger Stand')
    url = reverse('vendor-delete', kwargs={
        'tournament_id': tournament.pk,
        'pk': vendor.pk
    })
    response = auth_client.post(url)
    assert response.status_code == 302
    assert not Vendor.objects.filter(pk=vendor.pk).exists()


@pytest.mark.django_db
def test_vendor_requires_owner(client, tournament, django_user_model):
    other = django_user_model.objects.create_user(
        email='other@test.com', password='pass'
    )
    client.force_login(other)
    url = reverse('vendor-create', kwargs={'tournament_id': tournament.pk})
    response = client.post(url, {'name': 'Hacked Vendor', 'is_active': True})
    assert response.status_code == 404