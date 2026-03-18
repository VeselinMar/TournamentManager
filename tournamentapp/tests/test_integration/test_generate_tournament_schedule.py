import pytest
from django.urls import reverse
from tournamentapp.models import Team


@pytest.mark.django_db
def test_generate_schedule_success(auth_client, tournament, team, field):
    Team.objects.create(name="Team B", tournament=tournament)

    url = reverse("generate-tournament-schedule", kwargs={
        "tournament_id": tournament.id
    })

    response = auth_client.post(url, {
        "start_date": "2026-03-20",
        "start_time": "10:00",
        "has_halves": False,
        "game_duration": 30,
        "pause_duration": 10
    })
    
    assert response.status_code == 302