"""Regresiones de la revision transversal: interfaz, permisos y formularios."""
import uuid

import pytest
from django.contrib.auth.models import User
from django.test import Client

from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.modules.sales.presentation.forms.pago_form import PagoForm
from tests.system.test_flujo_pos_sistema import cajero, producto_con_stock, _abrir_caja, _venta_actual

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@pytest.fixture
def carrito(client, cajero, producto_con_stock):
    _abrir_caja(client)
    venta_id = _venta_actual(client)
    producto_id = str(producto_con_stock.id)
    assert client.post(f"/pos/venta/{venta_id}/agregar/{producto_id}/", {"cantidad": 2}).status_code == 200
    return venta_id, producto_id


def test_carrito_muestra_lineas_total_y_enlace_de_cobro(client, carrito):
    venta_id, producto_id = carrito
    respuesta = client.get("/pos/")
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert f'data-producto="{producto_id}"' in html
    assert "Arroz 1kg" in html
    assert "17,00" in html or "17.00" in html
    assert f'href="/pos/venta/{venta_id}/pago/"' in html


def test_cambiar_y_eliminar_linea_persiste_tras_recarga(client, carrito):
    venta_id, producto_id = carrito
    base = f"/pos/venta/{venta_id}"
    respuesta = client.post(f"{base}/cantidad/{producto_id}/", {"cantidad": 3})
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 25.5
    assert VentaModel.objects.get(pk=venta_id).detalles.get().cantidad == 3
    assert client.post(f"{base}/eliminar/{producto_id}/").status_code == 200
    venta = VentaModel.objects.get(pk=venta_id)
    assert venta.detalles.count() == 0
    assert venta.total == 0
    assert f'data-producto="{producto_id}"' not in client.get("/pos/").content.decode()


@pytest.mark.parametrize("accion", ["agregar", "cantidad", "eliminar"])
def test_mutaciones_pos_rechazan_get(client, carrito, accion):
    venta_id, producto_id = carrito
    assert client.get(f"/pos/venta/{venta_id}/{accion}/{producto_id}/").status_code == 405
    assert VentaModel.objects.get(pk=venta_id).detalles.get().cantidad == 2


@pytest.mark.parametrize("cantidad", ["abc", "", "0", "-1", "1.5"])
def test_cantidad_invalida_no_produce_500_ni_modifica_venta(client, carrito, cantidad):
    venta_id, producto_id = carrito
    respuesta = client.post(f"/pos/venta/{venta_id}/cantidad/{producto_id}/", {"cantidad": cantidad})
    assert respuesta.status_code == 400
    assert VentaModel.objects.get(pk=venta_id).detalles.get().cantidad == 2


@pytest.mark.parametrize("accion", ["agregar", "cantidad", "eliminar", "pago", "ticket"])
def test_cajero_no_accede_a_venta_ajena(client, carrito, accion):
    venta_id, producto_id = carrito
    VentaModel.objects.filter(pk=venta_id).update(cajero_id=uuid.uuid4())
    url = f"/pos/venta/{venta_id}/{accion}/"
    if accion in {"agregar", "cantidad", "eliminar"}:
        url += f"{producto_id}/"
    respuesta = client.get(url) if accion == "ticket" else client.post(url, {"cantidad": 4})
    assert respuesta.status_code == 404
    assert VentaModel.objects.get(pk=venta_id).detalles.get().cantidad == 2


def test_pago_parcial_conserva_carrito_en_sesion(client, carrito):
    venta_id, _ = carrito
    respuesta = client.post(f"/pos/venta/{venta_id}/pago/", {
        "metodo": "EFECTIVO", "monto": "5.00", "monto_entregado": "5.00",
    })
    assert respuesta.status_code == 302
    assert client.session["venta_actual"] == venta_id
    assert client.get("/pos/").status_code == 200
    assert VentaModel.objects.count() == 1


def test_pos_recupera_turno_abierto_despues_de_perder_id_de_sesion(client, carrito):
    sesion = client.session
    turno = sesion.pop("turno_caja_id")
    sesion.save()
    assert client.get("/pos/").status_code == 200
    assert client.session["turno_caja_id"] == turno


@pytest.mark.parametrize("monto", ["", "abc", "-1", "1000000000000"])
def test_formulario_pago_valida_importe_sin_typeerror(monto):
    form = PagoForm({"metodo": "EFECTIVO", "monto": monto, "monto_entregado": "10"})
    assert not form.is_valid()
    assert "monto" in form.errors


def test_logout_requiere_post_con_csrf():
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(User.objects.create_user(username="salida_segura"))
    assert cliente.get("/logout/").status_code == 405
    assert cliente.post("/logout/").status_code == 403
    cliente.get("/catalogo/")
    respuesta = cliente.post("/logout/", {"csrfmiddlewaretoken": cliente.cookies["csrftoken"].value})
    assert respuesta.status_code == 302
    assert "_auth_user_id" not in cliente.session


def test_service_worker_tiene_alcance_raiz_y_no_cachea_paginas_privadas(client):
    respuesta = client.get("/service-worker.js")
    assert respuesta.status_code == 200
    assert respuesta["Service-Worker-Allowed"] == "/"
    codigo = b"".join(respuesta.streaming_content).decode()
    assert 'url.pathname.startsWith("/static/")' in codigo


def test_cliente_solo_ve_navegacion_de_cliente(client):
    client.force_login(User.objects.create_user(username="menu_cliente"))
    sesion = client.session
    sesion["rol"] = "CLIENTE"
    sesion.save()
    html = client.get("/catalogo/").content.decode()
    assert 'href="/reportes/"' not in html
    assert 'href="/inventario/"' not in html
    assert 'href="/pos/"' not in html
    assert 'href="/pedidos/mis-pedidos/"' in html or "Mis pedidos" in html


@pytest.mark.parametrize("accion", ["agregar", "cantidad", "eliminar"])
def test_carrito_con_pago_parcial_no_admite_mutaciones(client, carrito, accion):
    venta_id, producto_id = carrito
    client.post(f"/pos/venta/{venta_id}/pago/", {
        "metodo": "EFECTIVO", "monto": "5", "monto_entregado": "5",
    })
    respuesta = client.post(f"/pos/venta/{venta_id}/{accion}/{producto_id}/", {"cantidad": 3})
    assert respuesta.status_code == 400
    venta = VentaModel.objects.get(pk=venta_id)
    assert venta.detalles.get().cantidad == 2
    assert venta.total == 17
    assert venta.pagos.count() == 1


def test_venta_sin_stock_se_cobra_y_anula_sin_crear_existencias(client, cajero, producto_con_stock):
    from src.modules.inventory.models import ExistenciaModel, LoteModel, MovimientoModel
    producto_con_stock.requiere_stock = False
    producto_con_stock.save(update_fields=["requiere_stock"])
    ExistenciaModel.objects.all().delete()
    LoteModel.objects.all().delete()
    _abrir_caja(client)
    venta_id = _venta_actual(client)
    producto_id = str(producto_con_stock.id)
    assert client.post(f"/pos/venta/{venta_id}/agregar/{producto_id}/").status_code == 200
    assert not VentaModel.objects.get(pk=venta_id).detalles.get().requiere_stock
    respuesta = client.post(f"/pos/venta/{venta_id}/pago/", {
        "metodo": "EFECTIVO", "monto": "8.50", "monto_entregado": "10",
    })
    assert respuesta.status_code == 302
    assert VentaModel.objects.get(pk=venta_id).estado == "PAGADA"
    sesion = client.session
    sesion["rol"] = "GERENTE"
    sesion.save()
    assert client.post(f"/pos/venta/{venta_id}/anular/", {"motivo": "Error de pedido"}).status_code == 302
    assert VentaModel.objects.get(pk=venta_id).estado == "ANULADA"
    assert ExistenciaModel.objects.count() == MovimientoModel.objects.count() == 0


def test_arqueo_invalido_o_ajeno_no_produce_500(client, carrito):
    from src.modules.cash_register.models import TurnoCajaModel
    assert client.get("/caja/arqueo/?turno_id=incorrecto").status_code == 400
    turno = TurnoCajaModel.objects.get()
    turno.cajero_id = uuid.uuid4()
    turno.save(update_fields=["cajero_id"])
    assert client.get(f"/caja/arqueo/?turno_id={turno.pk}").status_code == 404


def test_auditoria_no_oculta_registros_despues_del_numero_cien(client):
    from src.modules.auditing.models import AuditoriaModel
    client.force_login(User.objects.create_user(username="auditor_paginacion"))
    sesion = client.session
    sesion["rol"] = "ADMINISTRADOR"
    sesion.save()
    AuditoriaModel.objects.bulk_create([
        AuditoriaModel(id=uuid.uuid4(), accion="CREAR", entidad="ProductoModel", entidad_id=str(i), detalle={})
        for i in range(120)
    ])
    respuesta = client.get("/auditoria/", {"pagina": 3, "entidad": "ProductoModel"})
    assert respuesta.status_code == 200
    assert respuesta.context["pagina_dto"].total == 120
    assert len(respuesta.context["pagina_dto"].items) == 20
    from html import unescape
    import re
    from urllib.parse import parse_qs, urlsplit
    enlaces = re.findall(r'<a class="page-link" href="([^"]+)"', respuesta.content.decode())
    assert enlaces
    for enlace in enlaces:
        assert parse_qs(urlsplit(unescape(enlace)).query)["entidad"] == ["ProductoModel"]


def test_auditoria_inmutable_no_sobrescribe_un_registro_existente():
    from dataclasses import replace
    from django.db import IntegrityError, transaction
    from src.modules.auditing.domain.entities.registro_auditoria import RegistroAuditoria
    from src.modules.auditing.infrastructure.factories import construir_auditoria_repository
    repo = construir_auditoria_repository()
    registro = RegistroAuditoria.crear("CREAR", "ProductoModel", str(uuid.uuid4()))
    repo.guardar(registro)
    with pytest.raises(IntegrityError), transaction.atomic():
        repo.guardar(replace(registro, accion="ELIMINAR"))
    assert repo.buscar_por_id(registro.id).accion == "CREAR"


def test_healthz_comprueba_servicios_reales(client):
    from unittest.mock import patch
    respuesta = client.get("/healthz")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}
    with patch("config.health.cache.get", side_effect=ConnectionError("detalle privado")):
        respuesta = client.get("/healthz")
    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "unavailable"}
    assert b"detalle privado" not in respuesta.content
    assert respuesta["Cache-Control"] == "no-store"


@pytest.mark.parametrize("cantidad,total", [(1, "8.50"), (2, "8.50"), (3, "17.00"), (4, "17.00")])
def test_cambiar_cantidad_recalcula_promocion_2x1(client, carrito, cantidad, total):
    from decimal import Decimal
    from src.modules.promotions.models import PromocionModel
    venta_id, producto_id = carrito
    PromocionModel.objects.create(id=uuid.uuid4(), nombre="Dos por uno", tipo="NX1", estado="ACTIVA",
                                  producto_id=producto_id, descuento_valor=0,
                                  cantidad_requerida=2, cantidad_gratuita=1)
    respuesta = client.post(f"/pos/venta/{venta_id}/cantidad/{producto_id}/", {"cantidad": cantidad})
    assert respuesta.status_code == 200
    assert VentaModel.objects.get(pk=venta_id).total == Decimal(total)


def test_aumentar_cantidad_no_supera_stock_disponible(client, carrito):
    venta_id, producto_id = carrito
    respuesta = client.post(f"/pos/venta/{venta_id}/cantidad/{producto_id}/", {"cantidad": 21})
    assert respuesta.status_code == 400
    assert VentaModel.objects.get(pk=venta_id).detalles.get().cantidad == 2
