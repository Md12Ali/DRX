"""
Django settings for the DRX project.

Every secret and every environment-specific value is read from environment
variables. For local development these can be placed in ``env.py`` (which is
listed in .gitignore and never committed). See ``env_example.py``.

The data store is configured in ONE place: the DATABASE_URL variable.
"""
import os
import sys
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Load local environment variables if an env.py file exists.
if (BASE_DIR / "env.py").is_file():
    import env  # noqa: F401  pylint: disable=unused-import


# ---------------------------------------------------------------------------
# Core security settings
# ---------------------------------------------------------------------------
DEBUG = os.environ.get("DEBUG", "False") == "True"
RUNNING_TESTS = len(sys.argv) > 1 and sys.argv[1] == "test"

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG or RUNNING_TESTS:
        SECRET_KEY = "insecure-local-development-key-do-not-use-in-production"
    else:
        raise ImproperlyConfigured("The SECRET_KEY environment variable is not set.")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

# Render sets this automatically to the site's own address, e.g. drx.onrender.com
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Project apps - one per reusable component
    "core",
    "accounts.apps.AccountsConfig",
    "instructors",
    "bookings",
    "payments",
    "packages",
    "progress",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "drx.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.user_role",
                "core.context_processors.site_info",
            ],
        },
    },
]

WSGI_APPLICATION = "drx.wsgi.application"


# ---------------------------------------------------------------------------
# Database - single source of truth: DATABASE_URL
# Falls back to a local SQLite file when DATABASE_URL is not set.
# ---------------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "bookings:dashboard"
LOGOUT_REDIRECT_URL = "core:home"


# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static and media files
# ---------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# Uploaded images are limited in size (also validated in the forms).
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Production hardening (applies whenever DEBUG is off)
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # The test client talks plain HTTP, so never redirect to HTTPS during tests.
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "False") == "True" and not RUNNING_TESTS
    SECURE_HSTS_SECONDS = 0 if RUNNING_TESTS else int(os.environ.get("SECURE_HSTS_SECONDS", "3600"))


# ---------------------------------------------------------------------------
# Stripe payments (payments app)
# ---------------------------------------------------------------------------
STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_CURRENCY = "gbp"


# ---------------------------------------------------------------------------
# Booking rules (bookings app) - change the business rules in one place
# ---------------------------------------------------------------------------
BOOKING_MIN_NOTICE_HOURS = 12        # earliest a lesson can be booked
BOOKING_MAX_WEEKS_AHEAD = 8          # furthest ahead a lesson can be booked
BOOKING_CHANGE_CUTOFF_HOURS = 24     # learners can't change/cancel later than this
BOOKING_PAYMENT_HOLD_MINUTES = 35    # unpaid bookings hold the slot this long
BOOKING_SLOT_STEP_MINUTES = 30       # lessons start on the hour or half hour


# ---------------------------------------------------------------------------
# Business details (one place to change them)
# ---------------------------------------------------------------------------
SITE_NAME = "DRX"
STANDARD_HOURLY_RATE_PENCE = 3500    # £35 an hour, pay as you go

# Postcode districts covered for pick-ups, with the neighbourhoods they include.
COVERED_POSTCODE_DISTRICTS = {
    "E1": "Whitechapel, Stepney, Wapping",
    "E2": "Bethnal Green, Haggerston",
    "E3": "Bow, Bromley-by-Bow, Mile End",
    "E8": "Dalston, Hackney Central",
    "E9": "Homerton, Hackney Wick, South Hackney",
    "E14": "Poplar, Limehouse, Canary Wharf, Isle of Dogs",
    "EC1": "Clerkenwell, Farringdon, Old Street",
    "EC2": "Shoreditch, Liverpool Street, Moorgate",
    "N1": "Islington, Hoxton, King's Cross",
}
