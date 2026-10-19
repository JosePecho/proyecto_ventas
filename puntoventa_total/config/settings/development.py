import django
from importlib.util import find_spec

from .base import *  # noqa: F401,F403
from .base import DEBUG, INSTALLED_APPS, MIDDLEWARE

DEBUG = True

ALLOWED_HOSTS = ["*"]

if find_spec("debug_toolbar") is not None:
    INSTALLED_APPS = INSTALLED_APPS + ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]

if django.VERSION >= (6, 1):
    MAILERS = {"default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"}}
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Permite desarrollar sin Redis instalado
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "puntoventa-dev",
    }
}

CELERY_TASK_ALWAYS_EAGER = True

