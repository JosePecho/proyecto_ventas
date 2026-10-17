from .base import *  # noqa: F401,F403

from pathlib import Path
from tempfile import gettempdir
from uuid import uuid4
import django

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",  # noqa: F405
        # live_server usa varios hilos. Un archivo permite conexiones distintas;
        # SQLite en memoria haria compartir una sola conexion entre esos hilos.
        "TEST": {"NAME": str(Path(gettempdir()) / f"inventory-tests-{uuid4().hex}.sqlite3")},
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "puntoventa-tests",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

if django.VERSION >= (6, 1):
    MAILERS = {"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
else:
    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

