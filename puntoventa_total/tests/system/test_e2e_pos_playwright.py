"""Nivel 3 - Sistema (navegador): flujo real del POS en Chromium con Playwright.

Requisitos (seccion 6.3 del plan):
  pip install playwright && playwright install chromium
  pytest -m system tests/system/test_e2e_pos_playwright.py

Si Chromium no esta instalado o el modulo falta, el test se omite sin romper
la suite (el nivel 3 ya queda cubierto igualmente por test_flujo_pos_sistema).
"""
import os
import re
import uuid
from datetime import date
from decimal import Decimal

import pytest

# La API sincrona de Playwright mantiene un event loop de asyncio corriendo en
# el hilo principal mientras dura el contexto; Django bloquearia el ORM con
# SynchronousOnlyOperation. En un unico test de sistema este escape hatch es
# seguro (documentado por Django como "unsafe" solo para escenarios como este).
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")

playwright_sync = pytest.importorskip(
    "playwright.sync_api", reason="Requiere: pip install playwright"
)

from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO  # noqa: E402
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario  # noqa: E402
from src.modules.identity.domain.enums.rol_usuario import RolUsuario  # noqa: E402
from src.modules.identity.infrastructure.factories import (  # noqa: E402
    construir_hasher,
    construir_repositorio,
)
from src.modules.cash_register.infrastructure.persistence.django_models.turno_caja_model import (  # noqa: E402
    TurnoCajaModel,
)
from src.modules.catalog.infrastructure.persistence.django_models.producto_model import (  # noqa: E402
    ProductoModel,
)
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import (  # noqa: E402
    ExistenciaModel,
)
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import (  # noqa: E402
    LoteModel,
)
from src.modules.sales.infrastructure.persistence.django_models.venta_model import (  # noqa: E402
    VentaModel,
)

pytestmark = [pytest.mark.system, pytest.mark.e2e, pytest.mark.django_db]

CODIGO_BARRAS = "7759998887777"
USUARIO = "cajero_ui"
PASSWORD = "Secreta123"


@pytest.fixture
def navegador():
    try:
        with playwright_sync.sync_playwright() as p:
            navegador = p.chromium.launch()
            contexto = navegador.new_context()
            yield contexto
            contexto.close()
            navegador.close()
    except Exception as exc:  # noqa: BLE001 - chromium ausente/no instalable
        pytest.skip(f"Chromium no disponible (playwright install chromium): {exc}")


@pytest.fixture
def datos_pos():
    """Usuario cajero real (login por UI) + producto con stock sembrado."""
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(
        UsuarioInputDTO(
            username=USUARIO,
            password=PASSWORD,
            nombre_completo="Cajero UI",
            rol=RolUsuario.CAJERO.value,
        )
    )
    producto = ProductoModel.objects.create(
        id=uuid.uuid4(),
        nombre="Arroz 1kg",
        codigo_barras=CODIGO_BARRAS,
        costo=Decimal("5.00"),
        precio_venta=Decimal("8.50"),
        estado="ACTIVO",
    )
    ExistenciaModel.objects.create(
        id=uuid.uuid4(), producto_id=producto.id, cantidad=10, reservada=0
    )
    LoteModel.objects.create(
        id=uuid.uuid4(),
        producto_id=producto.id,
        numero_lote="L-UI-01",
        cantidad_inicial=10,
        cantidad_restante=10,
        fecha_recepcion=date.today(),
    )
    return producto


def _login(page, base_url: str):
    page.goto(f"{base_url}/")
    page.fill("input[name=username]", USUARIO)
    page.fill("input[name=password]", PASSWORD)
    page.click("button:has-text('Ingresar')")


def test_flujo_completo_del_pos_en_el_navegador(live_server, navegador, datos_pos):
    page = navegador.new_page()

    # 1. autenticacion por UI (login real del sistema)
    _login(page, live_server.url)

    # 2. apertura de caja
    page.goto(f"{live_server.url}/caja/apertura/")
    page.fill("input[name=monto_apertura]", "150.00")
    page.click("button:has-text('Abrir caja')")
    page.wait_for_url("**/pos/**")
    assert TurnoCajaModel.objects.count() == 1

    # 3. el POS crea la venta en sesion (se lee del encabezado)
    page.wait_for_selector("#buscador-pos")
    venta_id = re.search(r"Ticket en curso:\s*([0-9a-f-]{36})", page.content()).group(1)

    # 4. escanear codigo de barras -> un solo resultado -> auto-agrega al carrito
    page.fill("#buscador-pos", CODIGO_BARRAS)
    page.press("#buscador-pos", "Enter")
    page.wait_for_load_state("networkidle")
    assert VentaModel.objects.get(pk=venta_id).total == Decimal("8.50")

    # 5. cobrar en efectivo: 8.50 de 10.00 (vuelto 1.50)
    page.goto(f"{live_server.url}/pos/venta/{venta_id}/pago/")
    page.select_option("select[name=metodo]", "EFECTIVO")
    page.fill("input[name=monto]", "8.50")
    page.fill("input[name=monto_entregado]", "10.00")
    page.click("button:has-text('Confirmar cobro')")
    page.wait_for_url(f"**/pos/venta/{venta_id}/ticket/")

    # 6. verificacion de negocio directamente en la BD
    venta = VentaModel.objects.get(pk=venta_id)
    assert venta.estado == "PAGADA"
    assert venta.total == Decimal("8.50")
    assert ExistenciaModel.objects.get(producto_id=datos_pos.id).cantidad == 9

    # 7. el ticket abre como PDF en el navegador
    ticket = page.goto(f"{live_server.url}/pos/venta/{venta_id}/ticket/")
    assert ticket.status == 200
    assert ticket.headers["content-type"] == "application/pdf"
