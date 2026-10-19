import json
import os
from pathlib import Path
import subprocess
from uuid import uuid4

import pytest
from django.conf import settings
from django.test import Client

from tests.system.test_k6_pos_real import pos_http_server  # noqa: F401
from tests.integration.test_rf038_050 import staff, compra
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel

pytestmark = [pytest.mark.system, pytest.mark.performance, pytest.mark.django_db(transaction=True),
              pytest.mark.skipif(not os.environ.get("QA_K6_BINARY"), reason="Requiere QA_K6_BINARY")]


def test_reportes_carga_dos_roles_sin_filtrar_datos(client, pos_http_server):
    staff(client)
    otro = Client()
    staff(otro, "CLIENTE")
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente carga")
    compra(cliente, total=37)
    sesiones = [{"admin": admin, "cookie": settings.SESSION_COOKIE_NAME + "=" + c.cookies[settings.SESSION_COOKIE_NAME].value}
                for c, admin in ((client, True), (otro, False))]
    root = Path(__file__).resolve().parents[2]
    summary = root / "reports/k6-reportes-summary.json"
    summary.parent.mkdir(exist_ok=True)
    result = subprocess.run([os.environ["QA_K6_BINARY"], "run", "--summary-export", str(summary),
        "tests/performance/k6_reportes.js"], cwd=root, capture_output=True, text=True, timeout=60,
        env=dict(os.environ, BASE_URL=pos_http_server, QA_REPORTES_SESIONES=json.dumps(sesiones), K6_NO_USAGE_REPORT="true"))
    (root / "reports/k6-reportes-output.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(summary.read_text())["metrics"]["checks"]["value"] == 1
    assert VentaModel.objects.filter(estado="PAGADA", total=37).count() == 1
