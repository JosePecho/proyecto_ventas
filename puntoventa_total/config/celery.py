import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("puntoventa")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    """Registra las tareas programadas de los modulos."""
    app.conf.beat_schedule = {
        "verificar-stock-minimo-diario": {
            "task": "src.modules.inventory.tasks.verificar_stock_minimo.run",
            "schedule": 60.0 * 60.0,
        },
        "verificar-vencimientos-diario": {
            "task": "src.modules.inventory.tasks.verificar_vencimientos.run",
            "schedule": 60.0 * 60.0 * 6.0,
        },
        "actualizar-estado-promociones": {
            "task": "src.modules.promotions.tasks.actualizar_estado_promociones.run",
            "schedule": 60.0 * 30.0,
        },
    }

