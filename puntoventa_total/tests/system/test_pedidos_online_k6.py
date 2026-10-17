import json
import os
from pathlib import Path
import subprocess

import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse

from tests.system.test_k6_pos_real import pos_http_server  # noqa: F401
from tests.integration.test_pedidos_online import carrito, confirmar, registrar, iniciar
from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel

pytestmark = [pytest.mark.system, pytest.mark.performance, pytest.mark.django_db(transaction=True),
              pytest.mark.skipif(not os.environ.get("QA_K6_BINARY"), reason="Requiere QA_K6_BINARY")]


def test_carga_consulta_pedidos_aisla_dos_clientes(client, pos_http_server):
    primero, p = carrito(client)
    assert confirmar(client).status_code == 302
    otro = Client()
    assert registrar(otro, "otro@example.com", "87654321").status_code == 302
    assert iniciar(otro, "otro@example.com").status_code == 302
    assert otro.post(reverse("orders:agregar", args=[p.id]), {"cantidad": 2}).status_code == 302
    segundo = PedidoModel.objects.exclude(pk=primero.id).get()
    assert confirmar(otro).status_code == 302
    clientes = [{"ruta": reverse("orders:detalle", args=[pedido.id]), "numero": pedido.numero,
                 "cookie": settings.SESSION_COOKIE_NAME + "=" + navegador.cookies[settings.SESSION_COOKIE_NAME].value}
                for pedido, navegador in ((primero, client), (segundo, otro))]
    root = Path(__file__).resolve().parents[2]
    summary = root / "reports/k6-pedidos-summary.json"
    summary.parent.mkdir(exist_ok=True)
    env = dict(os.environ, BASE_URL=pos_http_server, QA_PEDIDOS_CLIENTES=json.dumps(clientes), K6_NO_USAGE_REPORT="true")
    resultado = subprocess.run([os.environ["QA_K6_BINARY"], "run", "--summary-export", str(summary),
                                "tests/performance/k6_pedidos.js"], cwd=root, env=env,
                               capture_output=True, text=True, timeout=60)
    (root / "reports/k6-pedidos-output.txt").write_text(resultado.stdout + resultado.stderr, encoding="utf-8")
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    evidencia = json.loads(summary.read_text())
    assert evidencia["metrics"]["checks"]["value"] == 1
    assert PedidoModel.objects.filter(estado="CONFIRMADO").count() == 2
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 4
