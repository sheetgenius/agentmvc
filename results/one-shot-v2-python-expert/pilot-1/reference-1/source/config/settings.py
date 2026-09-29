import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ["SECRET_KEY_BASE"]
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "channels",
    "procrastinate.contrib.django",
    "conduit",
]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "conduit.middleware.ApiCors"]
DATABASES = {
    "default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=0),
}
DATABASES["default"]["OPTIONS"] = {"pool": {"min_size": 1, "max_size": 10}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "UTC"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

DATA_UPLOAD_MAX_MEMORY_SIZE = 3_000_000
