"""RF-044/047/050 por HTTP y persistencia real; MySQL en el gate."""
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone

from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
from src.modules.customers.models import ClienteModel
from src.modules.sales.infrastructure.persistence.django_models.pago_model import PagoModel
from tests.integration.test_rf038_050 import compra, staff

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def datos_utilidad(total=10, costo=6):
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente reportes RF047")
    venta = compra(cliente, total=total, costo=costo)
    venta.detalles.update(producto_nombre="Pan RF047")
    return venta


def test_dashboard_del_dia_excluye_ayer_y_anuladas_y_desglosa_pagos(client):
    staff(client)
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente día")
    compra(cliente, total=10)
    tarjeta = compra(cliente, total=30)
    PagoModel.objects.filter(venta=tarjeta).update(metodo="TARJETA")
    compra(cliente, total=777, dias=1)
    compra(cliente, total=999, estado="ANULADA")
    respuesta = client.get(reverse("reporting:dashboard"))
    assert respuesta.status_code == 200
    assert respuesta.context["ventas_hoy"]["total"] == 40
    assert respuesta.context["ventas_hoy"]["tickets"] == 2
    assert respuesta.context["ventas_hoy"]["metodos_pago"] == {"EFECTIVO": 10, "TARJETA": 30}


@pytest.mark.parametrize("total,costo,margen", [(10, 6, 40), (32, 31, 3.13)])
def test_utilidad_muestra_margen_por_producto_y_total(client, total, costo, margen):
    staff(client)
    datos_utilidad(total, costo)
    respuesta = client.get(reverse("reporting:utilidad"))
    assert respuesta.status_code == 200
    reporte = respuesta.context["reporte"]
    assert reporte.por_producto[0]["margen_pct"] == margen
    assert reporte.margen_pct == margen
    assert reporte.utilidad_total == total - costo
    porcentaje = f"{margen:.2f}%"
    assert porcentaje.encode() in respuesta.content or porcentaje.replace(".", ",").encode() in respuesta.content


@pytest.mark.parametrize("consulta", [
    {"pagina": "abc"}, {"pagina": "0"}, {"pagina": "-1"}, {"pagina": "1.5"},
    {"desde": "mal"}, {"hasta": "2026-02-30"},
    {"desde": "2026-10-20", "hasta": "2026-10-19"}, {"usuario_id": "no-uuid"},
])
def test_auditoria_rechaza_filtros_invalidos_sin_500(client, consulta):
    staff(client)
    client.raise_request_exception = False
    respuesta = client.get(reverse("auditing:registros"), consulta)
    assert respuesta.status_code == 400
    assert respuesta.context["form"].errors


def test_auditoria_filtra_actor_accion_y_fecha_sin_exponer_secretos(client):
    admin = staff(client)
    secreto = "NoRegistrar#DatoPrivado456"
    assert client.post(reverse("catalog:categorias"), {
        "nombre": "Categoría auditable RF050", "password": secreto, "dni": "12345678",
    }).status_code == 302
    registro = AuditoriaModel.objects.get(entidad="CategoriaModel", accion="CREAR")
    AuditoriaModel.objects.create(id=uuid4(), accion="CREAR", entidad="CategoriaModel", entidad_id=str(uuid4()),
                                 usuario_id=uuid4(), detalle={"campos": ["nombre"]})
    hoy = timezone.localdate().isoformat()
    respuesta = client.get(reverse("auditing:registros"), {"usuario_id": admin.id, "accion": "CREAR",
                          "entidad": "CategoriaModel", "desde": hoy, "hasta": hoy})
    assert respuesta.status_code == 200
    filas = respuesta.context["pagina_dto"].items
    assert len(filas) == 1
    assert filas[0].id == str(registro.id)
    assert str(filas[0].usuario_id) == admin.id
    assert filas[0].fecha
    assert secreto not in respuesta.content.decode()
    assert "12345678" not in str(filas[0].detalle)


@pytest.mark.parametrize("rol", ["CLIENTE", "CAJERO", "ALMACENERO", "GERENTE"])
def test_auditoria_solo_es_visible_para_administrador(client, rol):
    staff(client, rol)
    respuesta = client.get(reverse("auditing:registros"))
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("catalog:catalogo")
