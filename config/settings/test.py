"""Testes executam contra PostgreSQL de teste isolado (banco `test_<DB_NAME>`), nunca SQLite."""

import tempfile
from pathlib import Path

from .base import *  # noqa: F403

DEBUG = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # apenas para acelerar testes
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
PRIVATE_MEDIA_ROOT = Path(tempfile.mkdtemp(prefix="govia-test-media-"))
APP_ENVIRONMENT_LABEL = "Teste"
LOGGING["root"]["level"] = "WARNING"  # noqa: F405
