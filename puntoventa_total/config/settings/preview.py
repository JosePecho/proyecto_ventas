"""Vista local de demostracion con SQLite, independiente de MySQL."""
from .development import *  # noqa: F401,F403
from .base import BASE_DIR

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "reports" / "preview.sqlite3",
    }
}
