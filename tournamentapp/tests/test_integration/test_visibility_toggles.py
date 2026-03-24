import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from announcements.models import Announcement


@pytest.mark.django_db
def test_announcements_hidden_when_toggle_off(auth_client, tournament):
    tournament.show_announcements = False
    tournament.save()

    now = timezone.now()
    Announcement.objects.create(
        tournament=tournament,
        message='Should not show',
        starts_at=now - timedelta(minutes=10),
        ends_at=now + timedelta(minutes=10),
        is_active=True
    )

    url = reverse('tournament-detail', kwargs={'pk': tournament.pk})
    response = auth_client.get(url)
    assert 'Should not show' not in response.content.decode()


@pytest.mark.django_db
def test_default_toggles_are_true(tournament):
    assert tournament.show_leaderboard is True
    assert tournament.show_vendors is True
    assert tournament.show_side_events is True
    assert tournament.show_announcements is True


@pytest.mark.django_db
def test_toggles_saved_via_update_form(auth_client, tournament):
    url = reverse('tournament-edit', kwargs={'pk': tournament.pk})
    response = auth_client.post(url, {
        'name': tournament.name,
        'tournament_date': '',
        'points_for_win': 3,
        'points_for_draw': 1,
        'yellow_cards_for_suspension': 2,
        'show_leaderboard': True,
        'show_vendors': False,
        'show_side_events': False,
        'show_announcements': True,
    })
    assert response.status_code == 302
    tournament.refresh_from_db()
    assert tournament.show_vendors is False
    assert tournament.show_side_events is False
    assert tournament.show_leaderboard is True
    assert tournament.show_announcements is True