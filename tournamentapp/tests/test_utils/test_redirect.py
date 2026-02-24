import pytest
from django.urls import reverse
from tournamentapp.models import Tournament
from accounts.utils import get_post_login_redirect

@pytest.mark.django_db
def test_redirects_to_existing_active_tournament(django_user_model):
    user = django_user_model.objects.create_user(
        email="testuser@abv.bg",
        password="pass"
    )

    tournament = Tournament.objects.create(
        name="Summer Cup",
        owner=user,
        is_finished=False
    )

    url = get_post_login_redirect(user)

    expected_url = reverse("tournament-detail", kwargs={"pk": tournament.pk})
    assert url == expected_url


@pytest.mark.django_db
def test_redirects_to_create_when_no_active_tournament(django_user_model):
    user = django_user_model.objects.create_user(
        email="testuser2@abv.bg",
        password="pass"
    )

    url = get_post_login_redirect(user)

    expected_url = reverse("tournament-create")
    assert url == expected_url