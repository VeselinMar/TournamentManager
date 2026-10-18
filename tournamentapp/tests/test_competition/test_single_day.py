"""Single-day assumptions: one event date, timeline rows keyed by date and time."""
from datetime import date, datetime, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from tournamentapp.models import Match, Team
from tournamentapp.utils import build_timeline


@pytest.mark.django_db
def test_timeline_keeps_matches_at_same_time_on_different_days(tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    day_one = timezone.make_aware(datetime(2026, 6, 20, 10, 0))
    Match.objects.create(tournament=tournament, home_team=team, away_team=away, field=field, start_time=day_one)
    Match.objects.create(tournament=tournament, home_team=away, away_team=team, field=field,
                         start_time=day_one + timedelta(days=1))

    timeline, _ = build_timeline(tournament)

    assert [row["time"] for row in timeline] == ["10:00", "10:00"]
    assert sum(1 for row in timeline for m in row["matches"] if m) == 2


@pytest.mark.django_db
def test_rescheduling_keeps_the_generated_event_day(auth_client, tournament, field):
    # The tournament was created with a different (e.g. provisional) date
    tournament.tournament_date = date(2026, 6, 1)
    tournament.save()
    for i in range(4):
        Team.objects.create(name=f"T{i}", tournament=tournament)
    auth_client.post(reverse("generate-tournament-schedule", args=[tournament.pk]), {
        "start_date": "2026-06-20", "start_time": "10:00", "game_duration": 15, "pause_duration": 5,
    })
    tournament.refresh_from_db()
    assert tournament.tournament_date == date(2026, 6, 20)

    match = tournament.matches.first()
    auth_client.post(reverse("edit-match", args=[tournament.pk, match.pk]),
                     {"start_time": "15:30", "field": field.pk})

    match.refresh_from_db()
    assert timezone.localtime(match.start_time).date() == date(2026, 6, 20)
