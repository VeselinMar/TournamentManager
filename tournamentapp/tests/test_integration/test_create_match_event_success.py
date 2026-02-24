import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_create_match_event_success(auth_client, match):
    player = match.home_team.players.create(name="Player 1")

    url = reverse("add-match-event", kwargs={
        "tournament_id": match.tournament.id,
        "match_id": match.id
    })

    response = auth_client.post(url, {
        "event_type": "goal",
        "team": "home",
        "player_id": player.id,
        "team_id": match.home_team.id,
        "minute": "10"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True