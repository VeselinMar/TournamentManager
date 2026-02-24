import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_match_detail_forbidden_for_non_owner(client, match, other_user):
    client.login(email="other@test.com", password="pass")

    url = reverse("match-detail", kwargs={
        "tournament_id": match.tournament.id,
        "pk": match.id
    })

    response = client.get(url)

    assert response.status_code == 404 or response.status_code == 403