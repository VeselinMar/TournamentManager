import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from tournamentapp.models import Match, Team, MatchEvent, Player


@pytest.mark.django_db
def test_yellow_card_threshold_mutes_player(auth_client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    player = team.players.create(name="Player A")

    url = reverse('add-match-event', kwargs={
        'tournament_id': tournament.pk,
        'match_id': match.pk
    })

    # first yellow — not muted yet
    auth_client.post(url, {
        'event_type': 'yellow_card',
        'team': 'home',
        'team_id': team.pk,
        'player_id': player.pk,
        'minute': 10,
    })
    player.refresh_from_db()
    assert player.is_muted is False

    # second yellow — muted
    auth_client.post(url, {
        'event_type': 'yellow_card',
        'team': 'home',
        'team_id': team.pk,
        'player_id': player.pk,
        'minute': 20,
    })
    player.refresh_from_db()
    assert player.is_muted is True


@pytest.mark.django_db
def test_red_card_mutes_player_immediately(auth_client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    player = team.players.create(name="Player A")

    url = reverse('add-match-event', kwargs={
        'tournament_id': tournament.pk,
        'match_id': match.pk
    })
    auth_client.post(url, {
        'event_type': 'red_card',
        'team': 'home',
        'team_id': team.pk,
        'player_id': player.pk,
        'minute': 30,
    })
    player.refresh_from_db()
    assert player.is_muted is True


@pytest.mark.django_db
def test_muted_player_cannot_score(auth_client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    player = team.players.create(name="Player A", is_muted=True)

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
    assert response.status_code == 400
    assert MatchEvent.objects.filter(match=match, player=player).count() == 0


@pytest.mark.django_db
def test_finish_match_increments_games_sat_out(auth_client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    player = team.players.create(name="Player A", is_muted=True)

    url = reverse('finish-match', kwargs={
        'tournament_id': tournament.pk,
        'match_id': match.pk
    })
    auth_client.post(url)

    player.refresh_from_db()
    assert player.games_sat_out == 1


@pytest.mark.django_db
def test_toggle_mute_lifts_suspension(auth_client, tournament, team):
    player = team.players.create(name="Player A", is_muted=True, games_sat_out=2)

    url = reverse('toggle-player-mute', kwargs={
        'tournament_id': tournament.pk,
        'player_id': player.pk
    })
    auth_client.post(url)

    player.refresh_from_db()
    assert player.is_muted is False
    assert player.games_sat_out == 0


@pytest.mark.django_db
def test_toggle_mute_requires_owner(client, tournament, team, django_user_model):
    player = team.players.create(name="Player A")
    other = django_user_model.objects.create_user(
        email='other@test.com', password='pass'
    )
    client.force_login(other)

    url = reverse('toggle-player-mute', kwargs={
        'tournament_id': tournament.pk,
        'player_id': player.pk
    })
    response = client.post(url)
    assert response.status_code == 404