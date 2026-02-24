import pytest
from django.contrib.auth import get_user_model

User = get_user_model()



@pytest.mark.django_db
def test_create_user_without_email_raises_error():
    with pytest.raises(ValueError):
        User.objects.create_user(email=None, password="pass")


@pytest.mark.django_db
def test_passwords_is_hashed(django_user_model):
    user = User.objects.create_user(email="spas@abv.bg", password="secret")
    assert user.check_password("secret")

@pytest.mark.django_db
def test_create_superuser_sets_flags(django_user_model):
    user = User.objects.create_superuser(
        email="admin@test.com",
        password="adminpass"
    )
    assert user.is_staff is True
    assert user.is_superuser is True


@pytest.mark.django_db
def test_user_str_returns_email(django_user_model):
    user = User.objects.create_user(
        email="test@test.com",
        password="pass"
    )
    assert str(user) == "test@test.com"