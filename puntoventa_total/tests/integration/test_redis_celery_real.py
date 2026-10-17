"""Redis y worker real. CI proporciona un servicio exclusivo para este job."""
import os
from uuid import uuid4

import pytest
from django.conf import settings
from celery import Celery
from celery.contrib.testing.worker import start_worker
from django.core.cache.backends.redis import RedisCache
from redis import Redis

pytestmark = [pytest.mark.integration, pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.environ.get("QA_REDIS_URL"), reason="Requiere QA_REDIS_URL de un Redis exclusivo de QA"
)]


def test_cache_redis_y_tarea_en_worker_real(monkeypatch):
    url = os.environ["QA_REDIS_URL"]
    # Celery prioriza estas variables sobre broker= y sobre app.conf.
    # .env local puede apuntar a localhost:6379; nunca usar ese broker en QA.
    monkeypatch.setenv("CELERY_BROKER_URL", url)
    monkeypatch.setenv("CELERY_RESULT_BACKEND", url)
    namespace = "qa-" + uuid4().hex
    redis = Redis.from_url(url, socket_connect_timeout=5, socket_timeout=5)
    cache = RedisCache(url, {"KEY_PREFIX": namespace, "TIMEOUT": 30, "OPTIONS": {}})
    app = Celery(namespace, broker=url, backend=url)
    app.conf.update(task_always_eager=False, task_default_queue=namespace,
                    imports=settings.CELERY_IMPORTS,
                    broker_transport_options={"global_keyprefix": namespace + ":"},
                    result_backend_transport_options={"global_keyprefix": namespace + ":"})

    @app.task(name=namespace + ".confirmar")
    def confirmar(referencia):
        return {"referencia": referencia, "estado": "procesado"}

    resultado = None
    try:
        assert redis.ping()
        cache.set("estado", "pendiente")
        assert cache.get("estado") == "pendiente"
        with start_worker(app, pool="solo", perform_ping_check=False, shutdown_timeout=10):
            assert "src.modules.orders.tasks.enviar_notificacion_pedido.run" in app.tasks
            assert "src.modules.promotions.tasks.actualizar_estado_promociones.run" in app.tasks
            resultado = confirmar.delay("PEDIDO-QA")
            assert resultado.get(timeout=10) == {"referencia": "PEDIDO-QA", "estado": "procesado"}
            negocio = app.send_task("src.modules.inventory.tasks.verificar_stock_minimo.run", queue=namespace)
            assert negocio.get(timeout=10) == 0
            negocio.forget()
            from django.core import mail
            from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
            pedido = PedidoModel.objects.create(id=uuid4(), numero="P-WORKER-QA", cliente_nombre="Ana",
                                                 cliente_email="ana@example.test", estado="LISTO")
            aviso = app.send_task("src.modules.orders.tasks.enviar_notificacion_pedido.run",
                                  args=[str(pedido.id)], queue=namespace)
            assert aviso.get(timeout=10) is True
            aviso.forget()
            pedido.refresh_from_db()
            assert pedido.notificado_listo
            assert mail.outbox[-1].to == ["ana@example.test"]
            assert "P-WORKER-QA" in mail.outbox[-1].subject
    finally:
        if resultado is not None:
            resultado.forget()
        cache.delete("estado")
        cache.close()
        app.close()
        redis.close()
