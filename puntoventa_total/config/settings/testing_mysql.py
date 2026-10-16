"""Solo para el contenedor desechable creado por scripts/qa_inventory_mysql.py."""
import os

from django.core.exceptions import ImproperlyConfigured

from .testing import *  # noqa: F401,F403

if os.environ.get("INVENTORY_EPHEMERAL_MYSQL") != "1":
    raise ImproperlyConfigured("Use scripts/qa_inventory_mysql.py para crear el MySQL aislado")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["QA_MYSQL_DATABASE"],
        "USER": os.environ["QA_MYSQL_USER"],
        "PASSWORD": os.environ["QA_MYSQL_PASSWORD"],
        "HOST": os.environ["QA_MYSQL_HOST"],
        "PORT": os.environ["QA_MYSQL_PORT"],
        "CONN_MAX_AGE": 0,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES', innodb_lock_wait_timeout=10",
        },
        "TEST": {"NAME": os.environ["QA_MYSQL_DATABASE"]},
    }
}
