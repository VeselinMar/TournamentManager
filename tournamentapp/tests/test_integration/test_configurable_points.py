import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from tournamentapp.models import Match, Team, Tournament, MatchEvent


@pytest.mark.django_db
def test_custom_points_applied_on_finish(auth_client, tournament, field, team):
    tournament.points_for_win = 2
    tournament.points_for_draw = 1
    tournament.save()

    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field,
        home_score=1, away_score=0
    )
    player = team.players.create(name="Scorer")
    MatchEvent.objects.create(
        match=match,
        event_type='goal',
        team=team,
        player=player,
        minute=10
    )

    url = reverse('finish-match', kwargs={
        'tournament_id': tournament.pk,
        'match_id': match.pk,
    })
    auth_client.post(url)

    team.refresh_from_db()
    away.refresh_from_db()
    assert team.tournament_points == 2
    assert away.tournament_points == 0

@pytest.mark.django_db
def test_custom_draw_points(auth_client, tournament, field, team):
    tournament.points_for_win = 3
    tournament.points_for_draw = 2
    tournament.save()

    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field,
        home_score=1, away_score=1
    )

    url = reverse('finish-match', kwargs={
        'tournament_id': tournament.pk,
        'match_id': match.pk
    })
    auth_client.post(url)

    team.refresh_from_db()
    away.refresh_from_db()
    assert team.tournament_points == 2
    assert away.tournament_points == 2


@pytest.mark.django_db
def test_points_locked_after_scored_match(auth_client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field,
        is_finished=True,
        home_score=1, away_score=0
    )

    url = reverse('tournament-edit', kwargs={'pk': tournament.pk})
    response = auth_client.post(url, {
        'name': tournament.name,
        'tournament_date': '',
        'points_for_win': 2,
        'points_for_draw': 1,
    })
    assert response.status_code == 302
    tournament.refresh_from_db()
    # points should not have changed — fields were disabled
    assert tournament.points_for_win == 3
    assert tournament.points_for_draw == 1


@pytest.mark.django_db
def test_points_validation_win_must_exceed_draw(auth_client, tournament):
    url = reverse('tournament-edit', kwargs={'pk': tournament.pk})
    response = auth_client.post(url, {
        'name': tournament.name,
        'tournament_date': '',
        'points_for_win': 1,
        'points_for_draw': 1,
    })
    assert response.status_code == 200  # form invalid, re-renders
    tournament.refresh_from_db()
    assert tournament.points_for_win == 3