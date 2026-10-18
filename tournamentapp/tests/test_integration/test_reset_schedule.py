import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from tournamentapp.models import Tournament, Team, Match, Field, MatchEvent


@pytest.mark.django_db
def test_reset_clears_matches_and_points(auth_client, tournament, field, team, points_table):
    away = Team.objects.create(name="Away", tournament=tournament)

    Match.objects.create(
        tournament=tournament,
        home_team=team,
        away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field,
        home_score=3,
        is_finished=True
    )
    assert points_table(tournament)[team.name] == 3

    url = reverse('reset-schedule', kwargs={'tournament_id': tournament.pk})
    response = auth_client.post(url)
    assert response.status_code == 302

    assert tournament.matches.count() == 0
    points = points_table(tournament)
    assert points[team.name] == 0
    assert points[away.name] == 0


@pytest.mark.django_db
def test_reset_cascades_to_match_events(auth_client, tournament, field, team):
    away = Team.objects.create(name="Away", tournament=tournament)
    player = team.players.create(name="Player A")

    match = Match.objects.create(
        tournament=tournament,
        home_team=team,
        away_team=away,
        start_time=timezone.now() + timedelta(hours=1),
        field=field
    )
    MatchEvent.objects.create(
        match=match, event_type='goal',
        team=team, player=player, minute=10
    )

    url = reverse('reset-schedule', kwargs={'tournament_id': tournament.pk})
    auth_client.post(url)

    assert Match.objects.filter(tournament=tournament).count() == 0
    assert MatchEvent.objects.filter(match__tournament=tournament).count() == 0


@pytest.mark.django_db
def test_reset_redirects_to_schedule_generator(auth_client, tournament):
    url = reverse('reset-schedule', kwargs={'tournament_id': tournament.pk})
    response = auth_client.post(url)
    assert response.status_code == 302
    assert 'generate-tournament-schedule' in response.url or \
           f'/tournament/{tournament.pk}/' in response.url


@pytest.mark.django_db
def test_reset_requires_owner(client, tournament, django_user_model):
    other = django_user_model.objects.create_user(
        email='other@test.com', password='pass'
    )
    client.force_login(other)
    url = reverse('reset-schedule', kwargs={'tournament_id': tournament.pk})
    response = client.post(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_reset_requires_post(auth_client, tournament):
    url = reverse('reset-schedule', kwargs={'tournament_id': tournament.pk})
    response = auth_client.get(url)
    assert response.status_code == 405