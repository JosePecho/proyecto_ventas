"""HTTP real bajo concurrencia acotada y controles basicos del navegador."""
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from django.test import Client

from scripts.qa_inventory_load import ejecutar_carga
from src.modules.catalog.models import ProductoModel
from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
from src.modules.inventory.models import MovimientoModel

pytestmark = [pytest.mark.system, pytest.mark.django_db(transaction=True)]


def test_formularios_rechazan_post_sin_csrf_y_escapan_html(django_user_model):
    usuario = django_user_model.objects.create_user(username="qa_seguridad")
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(usuario)
    sesion = cliente.session
    sesion["rol"] = "ALMACENERO"
    sesion.save()
    for ruta in ("/inventario/recepcion/", "/inventario/mermas/", "/catalogo/productos/nuevo/"):
        assert cliente.post(ruta, {"cantidad": 1}).status_code == 403
    assert not MovimientoModel.objects.exists()
    ProductoModel.objects.create(id=uuid4(), nombre='<script>alert("x")</script>', codigo_barras="7751234567804",
                                 costo=5, precio_venta=10, estado="ACTIVO")
    respuesta = cliente.get("/inventario/")
    assert respuesta.status_code == 200
    assert b"<script>alert(" not in respuesta.content
    assert b"&lt;script&gt;" in respuesta.content
    assert respuesta.headers["X-Frame-Options"] == "DENY"


@pytest.mark.performance
def test_carga_http_autenticada_sin_errores(live_server):
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(
        UsuarioInputDTO(username="qa_carga", password="PruebaInventario2026", nombre_completo="QA Carga", rol="ALMACENERO")
    )
    ProductoModel.objects.create(id=uuid4(), nombre="Carga QA", codigo_barras="7751234567805",
                                 costo=5, precio_venta=10, estado="ACTIVO")
    # El servidor de prueba escucha IPv4. Evita medir el fallback IPv6 de localhost.
    url = live_server.url.replace("http://localhost:", "http://127.0.0.1:")
    resultado = ejecutar_carga(url, "qa_carga", "PruebaInventario2026", usuarios=4, peticiones=20,
                              p95_max_ms=float(os.environ.get("INVENTORY_P95_MAX_MS", "2000")))
    print(json.dumps(resultado))
    Path("reports").mkdir(exist_ok=True)
    Path("reports/inventory-load.json").write_text(json.dumps(resultado), encoding="utf-8")
    assert resultado["aprobado"], resultado
