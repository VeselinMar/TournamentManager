import pytest
import datetime
from datetime import timedelta
from django.utils import timezone
from tournamentapp.models import Match, Field, Tournament, Team
from tournamentapp.utils import create_round_robin_matches

@pytest.mark.django_db
def test_create_round_robin_matches_assigns_fields_and_times(django_user_model):
    user = django_user_model.objects.create_user(
        email="testuser@abv.bg",
        password="pass"
    )
    tournament = Tournament.objects.create(name="T", owner_id=1)
    teams = [Team.objects.create(name=f"Team{i}", tournament=tournament) for i in range(4)]
    # Create fields
    field1 = Field.objects.create(name="Field 1", tournament=tournament, owner=tournament.owner)
    field2 = Field.objects.create(name="Field 2", tournament=tournament, owner=tournament.owner)

    start_time = timezone.now()
    game_duration = timedelta(minutes=30)
    pause_duration = timedelta(minutes=10)

    create_round_robin_matches(tournament, start_time, game_duration, pause_duration)

    matches = Match.objects.filter(tournament=tournament)
    assert matches.count() > 0

    # Check no match shares same field/time
    seen = set()
    for m in matches:
        key = (m.field.id, m.start_time)
        assert key not in seen
        seen.add(key)