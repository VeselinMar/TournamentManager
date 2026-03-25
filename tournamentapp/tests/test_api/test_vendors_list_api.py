import pytest
from django.urls import reverse
from vendors.models import Vendor


@pytest.mark.django_db
def test_vendors_returns_200(client, tournament):
    url = f'/api/tournaments/{tournament.slug}/vendors/'
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_vendors_returns_active_only(client, tournament):
    Vendor.objects.create(tournament=tournament, name='Active', is_active=True)
    Vendor.objects.create(tournament=tournament, name='Inactive', is_active=False)

    url = f'/api/tournaments/{tournament.slug}/vendors/'
    response = client.get(url)
    data = response.json()

    names = [v['name'] for v in data]
    assert 'Active' in names
    assert 'Inactive' not in names


@pytest.mark.django_db
def test_vendors_404_when_toggle_off(client, tournament):
    tournament.show_vendors = False
    tournament.save()

    url = f'/api/tournaments/{tournament.slug}/vendors/'
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_vendors_no_auth_required(client, tournament):
    url = f'/api/tournaments/{tournament.slug}/vendors/'
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_vendors_404_for_unknown_slug(client):
    url = '/api/tournaments/nonexistent/vendors/'
    response = client.get(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_vendor_fields(client, tournament):
    Vendor.objects.create(
        tournament=tournament,
        name='Burger Stand',
        description='Best burgers',
        category='Food',
        is_active=True
    )
    url = f'/api/tournaments/{tournament.slug}/vendors/'
    response = client.get(url)
    data = response.json()

    vendor = data[0]
    assert vendor['name'] == 'Burger Stand'
    assert vendor['description'] == 'Best burgers'
    assert vendor['category'] == 'Food'
    assert 'image_url' in vendor