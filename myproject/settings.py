from pathlib import Path
import os
from decouple import config, Csv
import dj_database_url
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent

Image.MAX_IMAGE_PIXELS = 20_000_000

# Secret key
SECRET_KEY = config("SECRET_KEY")

# Debug mode
DEBUG = config("DEBUG", default=True, cast=bool)

# session security
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"


# Allowed hosts
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1",
    cast=Csv()
)

# Application definition
INSTALLED_APPS = [

    # django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    # allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    # third-party apps
    "formtools",
    "storages",

    # local apps
    "accounts",
    "tournamentapp",
    "sponsors",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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

# Media files
# MEDIA_URL = "/media/"
# MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ------------------------------------------------------------------------------
# Database / model defaults
# ------------------------------------------------------------------------------

# Default PK field type for models
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model
AUTH_USER_MODEL = "accounts.AppUser"

# ------------------------------------------------------------------------------
# Sites framework
# ------------------------------------------------------------------------------

# Required for django-allauth (must match a Site object in the admin)
SITE_ID = 1

# ------------------------------------------------------------------------------
# Authentication backends
# ------------------------------------------------------------------------------

# Authentication backends used by Django
AUTHENTICATION_BACKENDS = [
    # Default Django authentication backend
    "django.contrib.auth.backends.ModelBackend",
    # django-allauth authentication backend (email-based login, social auth, etc.)
    "allauth.account.auth_backends.AuthenticationBackend",
]

# ------------------------------------------------------------------------------
# Email (disabled for now – using console backend)
# ------------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@example.com"

# ------------------------------------------------------------------------------
# Login / logout behavior
# ------------------------------------------------------------------------------

# URL name for the login page
LOGIN_URL = "login"

# Redirect destination after successful login
LOGIN_REDIRECT_URL = "/dashboard/"

# Redirect destination after logout
LOGOUT_REDIRECT_URL = "login"

# ------------------------------------------------------------------------------
# django-allauth account settings
# ------------------------------------------------------------------------------

# Login method
ACCOUNT_LOGIN_METHODS = {"email"}

# Signup fields (email required, passwords required)
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]

# No email verification
ACCOUNT_EMAIL_VERIFICATION = "none"

ACCOUNT_ADAPTER = "allauth.account.adapter.DefaultAccountAdapter"

# storage settings
if DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

    STATIC_URL = "/static/"
    STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
    # STATICFILES_DIRS = [BASE_DIR / "static"]

else:
    AZURE_BLOB_CACHE_CONTROL = "public, max-age=31536000, immutable"
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
                "cache_control": AZURE_BLOB_CACHE_CONTROL,
            },
        },
        "staticfiles": {
            "BACKEND": "storages.backends.azure_storage.AzureStorage",
            "OPTIONS": {
                "azure_container": AZURE_CONTAINER_STATIC,
                "account_name": AZURE_ACCOUNT_NAME,
                "account_key": AZURE_ACCOUNT_KEY,
                "connection_string": AZURE_CONNECTION_STRING,
                "cache_control": AZURE_BLOB_CACHE_CONTROL,
            }
        }
    }
