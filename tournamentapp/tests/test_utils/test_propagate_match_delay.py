import pytest
from datetime import datetime, timezone, timedelta
from tournamentapp.utils import propagate_match_delay
from tournamentapp.models import Field, Match, Tournament, Team

@pytest.mark.django_db
def test_propagate_match_delay_updates_future_matches(django_user_model):
    user = django_user_model.objects.create_user(
        email="testuser@abv.bg",
        password="pass"
    )
    tournament = Tournament.objects.create(name="T", owner_id=1)
    teams = [Team.objects.create(name=f"Team{i}", tournament=tournament) for i in range(2)]
    field = Field.objects.create(name="Main", tournament=tournament, owner=tournament.owner)

    m1 = Match.objects.create(
        tournament=tournament, 
        home_team=teams[0], 
        away_team=teams[1], 
        start_time=datetime(2026,2,23,10,0, tzinfo=timezone.utc), 
        field=field)
    m2 = Match.objects.create(
        tournament=tournament, 
        home_team=teams[1], 
        away_team=teams[0], 
        start_time=datetime(2026,2,23,11,0, tzinfo=timezone.utc), 
        field=field)

    new_start = datetime(2026, 2, 23, 10, 10, tzinfo=timezone.utc)
    propagate_match_delay(m1, new_start)

    m1.refresh_from_db()
    m2.refresh_from_db()

    assert m1.start_time == new_start
    # m2 should be delayed by 30 mins
    assert m2.start_time == datetime(2026,2,23,11,10, tzinfo=timezone.utc)