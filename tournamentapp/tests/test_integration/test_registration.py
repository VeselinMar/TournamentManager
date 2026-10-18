"""Registration must enforce Django's password validators."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
@pytest.mark.parametrize("password", ["1", "12345678", "password", "short"])
def test_register_rejects_weak_passwords(client, password):
    response = client.post(
        reverse("register"),
        {"email": "weak@example.com", "password1": password, "password2": password},
    )

    assert response.status_code == 200  # form re-rendered with errors
    assert not User.objects.filter(email="weak@example.com").exists()


@pytest.mark.django_db
def test_register_rejects_password_similar_to_email(client):
    password = "organiser.vienna@example.com"
    response = client.post(
        reverse("register"),
        {"email": "organiser.vienna@example.com", "password1": password, "password2": password},
    )

    assert response.status_code == 200
    assert not User.objects.filter(email="organiser.vienna@example.com").exists()


@pytest.mark.django_db
def test_register_accepts_strong_password_and_logs_in(client):
    password = "Turnier-Wien-2026!"
    response = client.post(
        reverse("register"),
        {"email": "strong@example.com", "password1": password, "password2": password},
    )

    assert response.status_code == 302
    assert User.objects.filter(email="strong@example.com").exists()
    assert "_auth_user_id" in client.session
