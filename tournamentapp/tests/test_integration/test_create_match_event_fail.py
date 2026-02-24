import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_create_match_event_forbidden(client, match, other_user):
    client.login(email="other@test.com", password="pass")

    url = reverse("add-match-event", kwargs={
        "tournament_id": match.tournament.id,
        "match_id": match.id
    })

    response = client.post(url)

    assert response.status_code == 403