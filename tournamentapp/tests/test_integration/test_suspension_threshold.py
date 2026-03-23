import pytest
from tournamentapp.models import Match, MatchEvent, Team
from django.utils import timezone
from datetime import timedelta


@pytest.mark.django_db
def test_default_suspension_threshold(tournament, team, field):
    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    player = team.players.create(name="Player A")

    MatchEvent.objects.create(match=match, event_type='yellow_card', team=team, player=player, minute=10)
    assert player.is_suspended() is False

    MatchEvent.objects.create(match=match, event_type='yellow_card', team=team, player=player, minute=20)
    assert player.is_suspended() is True


@pytest.mark.django_db
def test_custom_suspension_threshold(tournament, team, field):
    tournament.yellow_cards_for_suspension = 3
    tournament.save()

    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    player = team.players.create(name="Player A")

    MatchEvent.objects.create(match=match, event_type='yellow_card', team=team, player=player, minute=10)
    MatchEvent.objects.create(match=match, event_type='yellow_card', team=team, player=player, minute=20)
    assert player.is_suspended() is False

    MatchEvent.objects.create(match=match, event_type='yellow_card', team=team, player=player, minute=30)
    assert player.is_suspended() is True


@pytest.mark.django_db
def test_red_card_always_suspends(tournament, team, field):
    away = Team.objects.create(name="Away", tournament=tournament)
    match = Match.objects.create(
        tournament=tournament,
        home_team=team, away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    player = team.players.create(name="Player A")

    MatchEvent.objects.create(match=match, event_type='red_card', team=team, player=player, minute=10)
    assert player.is_suspended() is True


@pytest.mark.django_db
def test_suspension_threshold_locked_after_scored_match(auth_client, tournament, field, team):
    from django.urls import reverse
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
        'points_for_win': 3,
        'points_for_draw': 1,
        'yellow_cards_for_suspension': 3,
    })
    assert response.status_code == 302
    tournament.refresh_from_db()
    assert tournament.yellow_cards_for_suspension == 2