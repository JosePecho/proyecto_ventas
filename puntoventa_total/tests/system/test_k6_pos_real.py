"""Ejecuta k6 real contra Django HTTP + BD de pruebas aislada."""
from datetime import date
import json
import os
from pathlib import Path
import secrets
import subprocess
from uuid import uuid4

import pytest

from src.modules.catalog.models import ProductoModel
from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
from src.modules.inventory.models import ExistenciaModel, LoteModel
from src.modules.sales.models import VentaModel

pytestmark = [pytest.mark.system, pytest.mark.performance, pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(not os.environ.get("QA_K6_BINARY"), reason="Requiere QA_K6_BINARY")]


def test_k6_cobra_con_sesiones_aisladas_y_stock_consistente(live_server):
    prefix = "k6_" + uuid4().hex[:8] + "_"
    password = secrets.token_urlsafe(24)
    for index in (1, 2):
        CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(UsuarioInputDTO(
            username=f"{prefix}{index}", password=password, nombre_completo="Cajero carga QA", rol="CAJERO"))
    producto = ProductoModel.objects.create(id=uuid4(), nombre="Arroz QA carga", codigo_barras="7751234567999",
        costo="5.00", precio_venta="8.50", estado="ACTIVO", stock_minimo=0)
    ExistenciaModel.objects.create(id=uuid4(), producto_id=producto.id, cantidad=20)
    LoteModel.objects.create(id=uuid4(), producto_id=producto.id, numero_lote="QA-K6", cantidad_inicial=20,
        cantidad_restante=20, fecha_recepcion=date.today())
    root = Path(__file__).resolve().parents[2]
    summary = root / "reports/k6-pos-summary.json"
    summary.parent.mkdir(exist_ok=True)
    env = dict(os.environ, BASE_URL=live_server.url.replace("localhost", "127.0.0.1"),
        PMV_USERNAME_PREFIX=prefix, PMV_PASSWORD=password, PMV_CODIGO=producto.codigo_barras,
        VUS="2", ITERATIONS="3", K6_NO_USAGE_REPORT="true")
    result = subprocess.run([os.environ["QA_K6_BINARY"], "run", "--summary-export", str(summary),
        "tests/performance/k6_cobro.js"], cwd=root, env=env, capture_output=True, text=True, timeout=120)
    (root / "reports/k6-pos-output.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr
    evidence = json.loads(summary.read_text())
    assert evidence["metrics"]["checks"]["value"] == 1
    assert VentaModel.objects.filter(estado="PAGADA").count() == 6
    assert ExistenciaModel.objects.get(producto_id=producto.id).cantidad == 14
    assert LoteModel.objects.get(producto_id=producto.id).cantidad_restante == 14
