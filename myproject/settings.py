from pathlib import Path
import os
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Secret key
SECRET_KEY = config("SECRET_KEY", default="insecure-secret")

# Debug mode
DEBUG = config("DEBUG", default=True, cast=bool)

# Allowed hosts
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=Csv()
)

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "tournamentapp",
    "accounts",
    "sponsors",
    "formtools",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

ROOT_URLCONF = "myproject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tournamentapp.context_processors.current_tournament",
            ],
        },
    },
]

WSGI_APPLICATION = "myproject.wsgi.application"

# Database
DATABASE_URL = config("DATABASE_URL", default=None)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }

else:

    DATABASES = {
        "default": dj_database_url.config(
            default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
            conn_max_age=600,
        )
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Media files
# MEDIA_URL = "/media/"
# MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default PK type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model
AUTH_USER_MODEL = "accounts.AppUser"

# Authentication redirects
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "login"

# Azure storage settings
AZURE_ACCOUNT_NAME = config("AZURE_ACCOUNT_NAME", default="")
AZURE_ACCOUNT_KEY = config("AZURE_ACCOUNT_KEY", default="")
AZURE_CONNECTION_STRING = config("AZURE_CONNECTION_STRING", default="")
AZURE_CONTAINER = config("AZURE_CONTAINER", default="")
AZURE_CONTAINER_STATIC = "static"
AZURE_CONTAINER_MEDIA = "media"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": {
            "azure_container": AZURE_CONTAINER,
            "account_name": AZURE_ACCOUNT_NAME,
            "account_key": AZURE_ACCOUNT_KEY,
            "connection_string": AZURE_CONNECTION_STRING,
        },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.azure_storage.AzureStorage",
        "OPTIONS": {
            "azure_container": AZURE_CONTAINER_STATIC,
            "account_name": AZURE_ACCOUNT_NAME,
            "account_key": AZURE_ACCOUNT_KEY,
            "connection_string": AZURE_CONNECTION_STRING,
        }
    }
}
