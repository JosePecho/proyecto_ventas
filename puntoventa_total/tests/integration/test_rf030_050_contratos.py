"""RF-045/046/048: fronteras del día local, rankings y último administrador."""
from datetime import datetime, timezone as utc
from decimal import Decimal
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone

from src.modules.customers.models import ClienteModel
from src.modules.identity.infrastructure.factories import construir_repositorio
from src.modules.sales.models import VentaModel
from tests.integration.test_rf038_050 import compra, staff

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@timezone.override("America/Lima")
def test_reporte_incluye_dia_local_completo_y_excluye_dias_adyacentes(client):
    staff(client)
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Fronteras Lima")
    for instante, total, estado in [
        (datetime(2026, 10, 17, 4, 59, 59, 999999, tzinfo=utc.utc), 100, "PAGADA"),
        (datetime(2026, 10, 17, 5, tzinfo=utc.utc), 20, "PAGADA"),
        (datetime(2026, 10, 18, 4, 59, 59, 999999, tzinfo=utc.utc), 30, "PAGADA"),
        (datetime(2026, 10, 18, 5, tzinfo=utc.utc), 200, "PAGADA"),
        (datetime(2026, 10, 17, 12, tzinfo=utc.utc), 999, "ANULADA"),
    ]:
        venta = compra(cliente, total=total, estado=estado)
        VentaModel.objects.filter(pk=venta.id).update(fecha_creacion=instante)
    respuesta = client.get(reverse("reporting:ventas"), {"desde": "2026-10-17", "hasta": "2026-10-17"})
    assert respuesta.status_code == 200
    assert respuesta.context["reporte"].cantidad_tickets == 2
    assert respuesta.context["reporte"].total_ventas == 50
    assert respuesta.context["metodos"] == {"EFECTIVO": 50}


def sembrar_ranking():
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Ranking contrato")
    barato, caro = uuid4(), uuid4()
    mas_unidades = compra(cliente, total=10, producto_id=barato)
    mas_unidades.detalles.update(cantidad=5, precio_unitario=Decimal("2"))
    compra(cliente, total=30, producto_id=caro)
    compra(cliente, total=999, producto_id=barato, estado="ANULADA")
    return barato, caro


@pytest.mark.parametrize("orden", ["cantidad", "monto"])
def test_ranking_cambia_segun_criterio_sin_incluir_anuladas(client, orden):
    staff(client)
    barato, caro = sembrar_ranking()
    hoy = timezone.localdate().isoformat()
    respuesta = client.get(reverse("reporting:productos"), {"desde": hoy, "hasta": hoy, "orden": orden})
    assert respuesta.status_code == 200
    filas = respuesta.context["productos"]
    assert [f["producto_id"] for f in filas] == [str(p) for p in (
        (barato, caro) if orden == "cantidad" else (caro, barato)
    )]
    assert sum(f["unidades"] for f in filas) == 6
    assert sum(Decimal(str(f["ingresos"])) for f in filas) == Decimal("40")


@pytest.mark.parametrize("accion", ["desactivar", "quitar_rol"])
def test_ultimo_administrador_conserva_acceso(client, accion):
    administrador = staff(client)
    if accion == "desactivar":
        respuesta = client.post(reverse("identity:usuario_desactivar", args=[administrador.id]))
    else:
        respuesta = client.post(reverse("identity:usuario_editar", args=[administrador.id]), {
            "nombre_completo": "Administrador protegido", "email": "", "rol": "CAJERO", "password": "",
        })
    assert respuesta.status_code in (200, 302)
    actual = construir_repositorio().buscar_por_id(administrador.id)
    assert actual.activo
    assert actual.rol.value == "ADMINISTRADOR"
    assert client.get(reverse("identity:usuarios")).status_code == 200
