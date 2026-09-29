import os

import dj_database_url

SECRET_KEY = os.environ["SECRET_KEY_BASE"]
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"
INSTALLED_APPS = [
    "procrastinate.contrib.django",
    "conduit",
    "corsheaders",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.postgres",
]
AUTH_USER_MODEL = "conduit.User"
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
]
CORS_ALLOW_ALL_ORIGINS = True
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
