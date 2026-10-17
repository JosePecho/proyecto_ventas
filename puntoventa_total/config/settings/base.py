"""Configuracion base compartida por todos los entornos."""
from pathlib import Path

import environ
import django

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="clave-insegura-solo-desarrollo")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Modulos del negocio
    "src.modules.identity",
    "src.modules.catalog",
    "src.modules.inventory",
    "src.modules.sales",
    "src.modules.cash_register",
    "src.modules.orders",
    "src.modules.customers",
    "src.modules.promotions",
    "src.modules.reporting",
    "src.modules.auditing",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME", default="puntoventa"),
        "USER": env("DB_USER", default="puntoventa"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="3306"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es"
TIME_ZONE = env("TIME_ZONE", default="America/Lima")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Autenticacion
LOGIN_URL = "identity:login"
LOGIN_REDIRECT_URL = "catalog:catalogo"
LOGOUT_REDIRECT_URL = "identity:login"

# Cache (Redis) con fallback a memoria local si Redis no esta disponible
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True

# RF-037: SMTP configurable; nunca guardar credenciales en el repositorio.
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="pedidos@puntoventa.local")
_smtp_options = {
    "host": env("EMAIL_HOST", default="localhost"), "port": env.int("EMAIL_PORT", default=25),
    "username": env("EMAIL_HOST_USER", default=""), "password": env("EMAIL_HOST_PASSWORD", default=""),
    "use_tls": env.bool("EMAIL_USE_TLS", default=False), "use_ssl": env.bool("EMAIL_USE_SSL", default=False),
    "timeout": env.int("EMAIL_TIMEOUT", default=10),
}
if django.VERSION >= (6, 1):
    MAILERS = {"default": {"BACKEND": "django.core.mail.backends.smtp.EmailBackend", "OPTIONS": _smtp_options}}
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = _smtp_options["host"]
    EMAIL_PORT = _smtp_options["port"]
    EMAIL_HOST_USER = _smtp_options["username"]
    EMAIL_HOST_PASSWORD = _smtp_options["password"]
    EMAIL_USE_TLS = _smtp_options["use_tls"]
    EMAIL_USE_SSL = _smtp_options["use_ssl"]
    EMAIL_TIMEOUT = _smtp_options["timeout"]

CELERY_BEAT_SCHEDULE = {
    "verificar-stock-minimo-diario": {
        "task": "src.modules.inventory.tasks.verificar_stock_minimo.run", "schedule": 3600.0,
    },
    "verificar-vencimientos-diario": {
        "task": "src.modules.inventory.tasks.verificar_vencimientos.run", "schedule": 21600.0,
    },
    "actualizar-estado-promociones": {
        "task": "src.modules.promotions.tasks.actualizar_estado_promociones.run", "schedule": 1800.0,
    },
    "pedidos-listos-pendientes": {
        "task": "src.modules.orders.tasks.reintentar_notificaciones", "schedule": 60.0,
    },
}

# Negocio
DEFAULT_CURRENCY = env("DEFAULT_CURRENCY", default="PEN")
STOCK_MINIMO_ALERTA = 5
STOCK_ALERTA_DESTINATARIOS = env.list("STOCK_ALERTA_DESTINATARIOS", default=["compras@puntoventa.local"])
DIAS_ALERTA_VENCIMIENTO = 30

CELERY_IMPORTS = (
    "src.modules.inventory.infrastructure.tasks.verificar_stock_minimo",
    "src.modules.inventory.infrastructure.tasks.verificar_vencimientos",
    "src.modules.promotions.infrastructure.tasks.actualizar_estado_promociones",
    "src.modules.orders.infrastructure.tasks.enviar_notificacion_pedido",
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

