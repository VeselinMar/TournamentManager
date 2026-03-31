from pathlib import Path
import os
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Secret key
SECRET_KEY = config("SECRET_KEY")

# Debug mode
DEBUG = config("DEBUG", default=True, cast=bool)

FORMS_URLFIELD_ASSUME_HTTPS = True

# session security
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True


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
    "rest_framework",

    # allauth
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    # third-party apps
    "formtools",
    "storages",
    "corsheaders",

    # local apps
    "accounts",
    "tournamentapp",
    "sponsors",
    "vendors",
    "programme",
    "announcements",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
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

CSRF_TRUSTED_ORIGINS = [
    "https://eventmanager-ep2v.onrender.com"
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    'https://eventmanager-ep2v.onrender.com'
]

CORS_ALLOW_CREDENTIALS = True

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
                'announcements.context_processors.active_announcements',
            ],
        },
    },
]

WSGI_APPLICATION = "myproject.wsgi.application"

# DjangoREST
REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
    ],
}

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

# SITE_ID = 2 because Django creates a default Site with id=1 (example.com) during
# initial migration. A second Site object was manually created in the admin with the
# correct domain (tournamentmanager.onrender.com) which received id=2.
# If redeploying from scratch: run migrations, go to /admin/sites/site/, update the
# existing Site or create a new one with the correct domain, then set SITE_ID to match.
SITE_ID = 2

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
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = "noreply@example.com"

# ------------------------------------------------------------------------------
# Login / logout behavior
# ------------------------------------------------------------------------------

# URL name for the login page
LOGIN_URL = "custom-login"

# Redirect destination after successful login
LOGIN_REDIRECT_URL = "tournament-create"

# Redirect destination after logout
LOGOUT_REDIRECT_URL = "custom-login"

# Disable confirmation
SOCIALACCOUNT_LOGIN_ON_GET = True

SOCIALACCOUNT_EMAIL_AUTHENTICATION = True

SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True



# ------------------------------------------------------------------------------
# django-allauth account settings
# ------------------------------------------------------------------------------

# App uses only e-mail and password fields
ACCOUNT_USER_MODEL_USERNAME_FIELD = None

# Login method
ACCOUNT_LOGIN_METHODS = {"email"}

# Signup fields (email required, passwords required)
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]

# No email verification
ACCOUNT_EMAIL_VERIFICATION = "none"

# storage settings
# if DEBUG:
#     STORAGES = {
#         "default": {
#             "BACKEND": "django.core.files.storage.FileSystemStorage",
#         },
#         "staticfiles": {
#             "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
#         },
#     }

#     MEDIA_URL = "/media/"
#     MEDIA_ROOT = BASE_DIR / "media"

#     STATIC_URL = "/static/"
#     STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
#     # STATICFILES_DIRS = [BASE_DIR / "static"]

# else:
AZURE_BLOB_CACHE_CONTROL = "public, max-age=31536000, immutable"
AZURE_ACCOUNT_NAME = config("AZURE_ACCOUNT_NAME", default="")
AZURE_ACCOUNT_KEY = config("AZURE_ACCOUNT_KEY", default="")
AZURE_CONNECTION_STRING = config("AZURE_CONNECTION_STRING", default="")
AZURE_CONTAINER = config("AZURE_CONTAINER", default="")
AZURE_CONTAINER_STATIC = "static"
AZURE_CONTAINER_MEDIA = "media"
STATIC_URL = f'https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER_STATIC}/'


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

