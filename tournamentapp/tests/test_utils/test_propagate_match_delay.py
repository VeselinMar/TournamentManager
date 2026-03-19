import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from tournamentapp.utils import propagate_match_delay
from tournamentapp.models import Field, Match, Tournament, Team

@pytest.mark.django_db
def test_propagate_match_delay_updates_future_matches(django_user_model):
    user = django_user_model.objects.create_user(
        email="testuser@abv.bg",
        password="pass"
    )
    tournament = Tournament.objects.create(name="T", owner=user)
    teams = [Team.objects.create(name=f"Team{i}", tournament=tournament) for i in range(2)]
    field = Field.objects.create(name="Main", tournament=tournament, owner=user)

    base_time = timezone.make_aware(datetime(2026, 2, 23, 10, 0))
    
    m1 = Match.objects.create(
        tournament=tournament,
        home_team=teams[0],
        away_team=teams[1],
        start_time=base_time,
        field=field
    )
    m2 = Match.objects.create(
        tournament=tournament,
        home_team=teams[1],
        away_team=teams[0],
        start_time=base_time + timedelta(hours=1),
        field=field
    )

    new_start = base_time + timedelta(minutes=10)
    propagate_match_delay(m1, new_start)

    m1.refresh_from_db()
    m2.refresh_from_db()

    assert m1.start_time == new_start

    expected = base_time + timedelta(hours=1, minutes=10)
    assert abs(m2.start_time - expected) < timedelta(seconds=1)
