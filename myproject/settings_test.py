from .settings import *

AZURE_CONTAINER = "test-container"
AZURE_ACCOUNT_NAME = "test"
AZURE_ACCOUNT_KEY = "test"
SECRET_KEY = "test-secret-key"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}