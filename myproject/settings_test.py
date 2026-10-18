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

# Tests always use local storage, independent of the DEBUG value in .env
import tempfile
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
MEDIA_ROOT = tempfile.mkdtemp(prefix="tm-test-media-")
MEDIA_URL = "/media/"
STATIC_URL = "/static/"
