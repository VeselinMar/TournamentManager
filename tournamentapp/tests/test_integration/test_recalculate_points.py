import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from tournamentapp.models import Match, Team, MatchEvent


@pytest.mark.django_db
def test_adding_goal_to_finished_match_updates_points(auth_client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament, tournament_points=3)
    team.tournament_points = 0
    team.save()

    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field,
        is_finished=True,
        home_score=0, away_score=1
    )
    away_player = away.players.create(name="Away Scorer")
    MatchEvent.objects.create(
        match=match,
        event_type='goal',
        team=away,
        player=away_player,
        minute=5
    )

    player = team.players.create(name="Scorer")
    url = reverse('add-match-event', kwargs={
        'tournament_id': tournament.pk,
        'match_id': match.pk
    })
    response = auth_client.post(url, {
        'event_type': 'goal',
        'team': 'home',
        'team_id': team.pk,
        'player_id': player.pk,
        'minute': 10,
    })
    assert response.status_code == 200

@pytest.mark.django_db
def test_removing_goal_from_finished_match_updates_points(auth_client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament, tournament_points=0)
    team.tournament_points = 3
    team.save()

    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field,
        is_finished=True,
        home_score=1, away_score=0
    )
    player = team.players.create(name="Scorer")
    event = MatchEvent.objects.create(
        match=match, event_type='goal',
        team=team, player=player, minute=10
    )

    url = reverse('delete-match-event', kwargs={
        'tournament_id': tournament.pk,
        'event_id': event.pk
    })
    response = auth_client.delete(url)
    assert response.status_code == 200

    team.refresh_from_db()
    away.refresh_from_db()
    match.refresh_from_db()

    # now 0-0, should be draw
    assert match.home_score == 0
    assert match.away_score == 0
    assert team.tournament_points == 1
    assert away.tournament_points == 1

    response = auth_client.post(url, {
    'event_type': 'goal',
    'team': 'home',
    'team_id': team.pk,
    'player_id': player.pk,
    'minute': 10,
})
