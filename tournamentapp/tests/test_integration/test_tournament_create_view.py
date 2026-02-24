import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_tournament_create_redirects_if_exists(auth_client, tournament):
    url = reverse("tournament-create")
    response = auth_client.get(url)

    assert response.status_code == 302
    assert str(tournament.pk) in response.url