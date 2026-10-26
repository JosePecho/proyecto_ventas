"""RF-030..037: HTTP, ORM, stock y correo reales (MySQL en el gate)."""
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import LoteModel
from src.modules.inventory.infrastructure.persistence.django_models.reserva_model import ReservaModel
from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
from src.modules.orders.infrastructure.tasks.enviar_notificacion_pedido import run

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
PASSWORD = "Panaderia!Segura#725"


def registrar(client, email="ana@example.com", dni="12345678"):
    return client.post(reverse("customers:registro"), {
        "nombre": "Ana Cliente", "dni": dni, "email": email, "telefono": "987654321",
        "password": PASSWORD, "password_confirmacion": PASSWORD,
    })


def iniciar(client, email="ana@example.com", password=PASSWORD):
    return client.post(reverse("identity:login"), {"username": email, "password": password})


def producto():
    p = ProductoModel.objects.create(id=uuid.uuid4(), nombre="Pan de recojo", codigo_barras="7751234567890",
                                     costo=Decimal("1"), precio_venta=Decimal("2"), estado="ACTIVO")
    ExistenciaModel.objects.create(id=uuid.uuid4(), producto_id=p.id, cantidad=10, reservada=0)
    LoteModel.objects.create(id=uuid.uuid4(), producto_id=p.id, numero_lote="PEDIDOS-1", cantidad_inicial=10,
                             cantidad_restante=10, fecha_recepcion=date.today())
    return p


def carrito(client):
    assert registrar(client).status_code == 302
    assert iniciar(client).status_code == 302
    p = producto()
    assert client.post(reverse("orders:agregar", args=[p.id]), {"cantidad": 2}).status_code == 302
    return PedidoModel.objects.get(), p


def confirmar(client):
    hora = (timezone.localtime() + timedelta(days=1)).replace(minute=30, second=0, microsecond=0)
    return client.post(reverse("orders:checkout"), {
        "cliente_nombre": "Ana Recojo", "cliente_dni": "12345678", "cliente_telefono": "987654321",
        "hora_recojo": hora.strftime("%Y-%m-%dT%H:%M"), "modalidad": "RECOJO", "observaciones": "Sin bolsa",
    })


def test_registro_publico_login_email_y_password_hash(client):
    assert registrar(client, "ANA@EXAMPLE.COM").status_code == 302
    usuario = UsuarioModel.objects.get()
    assert usuario.rol == "CLIENTE"
    assert usuario.email == "ana@example.com"
    assert usuario.password_hash != PASSWORD
    assert ClienteModel.objects.get().usuario_id == usuario.id
    assert iniciar(client, "ANA@example.com").status_code == 302
    assert client.session["usuario_id"] == str(usuario.id)


@pytest.mark.parametrize("cambio", [
    {"dni": "abc"}, {"email": "invalido"}, {"telefono": ""}, {"telefono": "abcdefghi"},
    {"password": "123", "password_confirmacion": "123"}, {"password_confirmacion": "otra"},
])
def test_registro_invalido_no_crea_cuentas(client, cambio):
    datos = {"nombre": "Ana", "dni": "12345678", "email": "ana@example.com", "telefono": "987654321",
             "password": PASSWORD, "password_confirmacion": PASSWORD}
    datos.update(cambio)
    respuesta = client.post(reverse("customers:registro"), datos)
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    assert UsuarioModel.objects.count() == ClienteModel.objects.count() == 0


def test_email_duplicado_y_dni_duplicado_no_dejan_cuentas_huerfanas(client):
    registrar(client)
    assert registrar(client, "ANA@EXAMPLE.COM", "87654321").status_code == 200
    assert registrar(client, "otra@example.com").status_code == 200
    assert UsuarioModel.objects.count() == ClienteModel.objects.count() == 1


def test_login_incorrecto_no_crea_sesion(client):
    registrar(client)
    assert iniciar(client, password="incorrecta").status_code == 200
    assert "usuario_id" not in client.session
    assert UsuarioModel.objects.get().intentos_fallidos == 1


def test_carrito_confirmacion_datos_recojo_y_cancelacion_libera_stock(client):
    pedido, p = carrito(client)
    assert pedido.cliente_id == UsuarioModel.objects.get().id
    assert client.get(reverse("orders:carrito")).context["total"] == 4
    assert confirmar(client).status_code == 302
    pedido.refresh_from_db()
    assert pedido.estado == "CONFIRMADO"
    assert pedido.cliente_nombre == "Ana Recojo"
    assert pedido.cliente_email == "ana@example.com"
    assert pedido.hora_recojo is not None
    assert pedido.observaciones == "Sin bolsa"
    assert "pedido_web" not in client.session
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 2
    assert ReservaModel.objects.get().permanente
    respuesta = client.get(reverse("orders:detalle", args=[pedido.id]))
    assert b"Pendiente" in respuesta.content
    assert client.post(reverse("orders:cancelar", args=[pedido.id])).status_code == 302
    pedido.refresh_from_db()
    assert pedido.estado == "CANCELADO"
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 0


@pytest.mark.parametrize("estado", ["EN_PREPARACION", "LISTO", "ENTREGADO", "CANCELADO"])
def test_cancelacion_tardia_no_modifica_stock(client, estado):
    pedido, p = carrito(client)
    confirmar(client)
    PedidoModel.objects.filter(pk=pedido.id).update(estado=estado)
    client.post(reverse("orders:cancelar", args=[pedido.id]))
    pedido.refresh_from_db()
    assert pedido.estado == estado
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 2


def test_aislamiento_cliente_y_permisos_cocina(client):
    pedido, _ = carrito(client)
    otro = Client()
    registrar(otro, "otro@example.com", "87654321")
    iniciar(otro, "otro@example.com")
    for ruta in ("detalle", "cancelar"):
        assert otro.post(reverse(f"orders:{ruta}", args=[pedido.id])).status_code == 404
    assert otro.get(reverse("orders:seguimiento"), {"numero": pedido.numero}).status_code == 404
    session = otro.session
    session["pedido_web"] = str(pedido.id)
    session.save()
    assert otro.get(reverse("orders:checkout")).status_code == 404
    assert otro.get(reverse("orders:carrito")).status_code == 404
    respuesta = otro.post(reverse("orders:cambiar_estado", args=[pedido.id]), {"estado": "LISTO"})
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("catalog:catalogo")
    pedido.refresh_from_db()
    assert pedido.estado == "BORRADOR"


def test_preparar_listo_notifica_una_vez_y_entrega_descuenta_stock(client, django_capture_on_commit_callbacks):
    pedido, p = carrito(client)
    confirmar(client)
    session = client.session
    session["rol"] = "CAJERO"
    session.save()
    for estado in ("EN_PREPARACION", "LISTO"):
        with django_capture_on_commit_callbacks(execute=True):
            assert client.post(reverse("orders:cambiar_estado", args=[pedido.id]), {"estado": estado}).status_code == 302
    pedido.refresh_from_db()
    assert pedido.estado == "LISTO"
    assert pedido.notificado_listo
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["ana@example.com"]
    assert pedido.numero in mail.outbox[0].subject
    assert run(str(pedido.id)) is True
    assert len(mail.outbox) == 1
    client.post(reverse("orders:cambiar_estado", args=[pedido.id]), {"estado": "ENTREGADO"})
    pedido.refresh_from_db()
    assert pedido.estado == "ENTREGADO"
    stock = ExistenciaModel.objects.get(producto_id=p.id)
    assert (stock.cantidad, stock.reservada) == (8, 0)
    assert LoteModel.objects.get(producto_id=p.id).cantidad_restante == 8


@pytest.mark.parametrize("datos_hora", [{}, {"hora_recojo": ""}])
def test_checkout_confirma_con_horario_automatico(client, datos_hora):
    pedido, p = carrito(client)
    respuesta = client.get(reverse("orders:checkout"))
    assert respuesta.context["form"]["hora_recojo"].value() is not None
    antes = timezone.now()
    respuesta = client.post(reverse("orders:checkout"), {
        "cliente_nombre": "Ana", "modalidad": "RECOJO", **datos_hora,
    })
    assert respuesta.status_code == 302
    pedido.refresh_from_db()
    assert pedido.estado == "CONFIRMADO"
    assert antes < pedido.hora_recojo <= antes + timedelta(minutes=30)
    assert timezone.localtime(pedido.hora_recojo).minute in (0, 30)
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 2


@pytest.mark.parametrize("hora", ["2000-01-01T10:00", "2099-01-01T10:15", "2099-01-01T10:30:01"])
def test_checkout_rechaza_hora_invalida_sin_reservar(client, hora):
    pedido, p = carrito(client)
    respuesta = client.post(reverse("orders:checkout"), {"cliente_nombre": "Ana", "modalidad": "RECOJO", "hora_recojo": hora})
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    pedido.refresh_from_db()
    assert pedido.estado == "BORRADOR"
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 0


def test_cantidad_acumulada_no_supera_disponible(client):
    pedido, p = carrito(client)
    client.post(reverse("orders:agregar", args=[p.id]), {"cantidad": 9})
    assert pedido.detalles.get().cantidad == 2
    client.post(reverse("orders:agregar", args=[p.id]), {"cantidad": -1})
    assert pedido.detalles.get().cantidad == 2


def test_quitar_producto_recalcula_total_persiste_y_permite_vaciar(client):
    pedido, p = carrito(client)
    otro = ProductoModel.objects.create(id=uuid.uuid4(), nombre="Servicio", codigo_barras="7751234567898",
                                        costo=1, precio_venta=3, estado="ACTIVO", requiere_stock=False)
    client.post(reverse("orders:agregar", args=[otro.id]), {"cantidad": 1})
    assert b"Quitar" in client.get(reverse("orders:carrito")).content
    ruta = reverse("orders:quitar", args=[p.id])
    assert client.post(ruta).status_code == 302
    pedido.refresh_from_db()
    assert pedido.total == 3
    assert list(pedido.detalles.values_list("producto_id", flat=True)) == [otro.id]
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 0
    assert client.post(ruta).status_code == 302  # Un doble clic no cambia otras lineas.
    client.post(reverse("orders:quitar", args=[otro.id]))
    respuesta = client.get(reverse("orders:carrito"))
    assert respuesta.context["lineas"] == []
    assert respuesta.context["total"] == 0
    assert not pedido.detalles.exists()
    assert b"Elegir hora" not in respuesta.content


@pytest.mark.parametrize("cantidad,restante", [(39, 1), (40, 0), (2, 38)])
def test_catalogo_descuenta_carrito_y_marca_stock_bajo(client, cantidad, restante):
    pedido, p = carrito(client)
    ExistenciaModel.objects.filter(producto_id=p.id).update(cantidad=40)
    client.post(reverse("orders:quitar", args=[p.id]))
    client.post(reverse("orders:agregar", args=[p.id]), {"cantidad": cantidad})
    respuesta = client.get(reverse("catalog:catalogo"))
    assert respuesta.context["items"][0].stock_disponible == restante
    if restante == 1:
        assert b'bg-danger ms-1">Stock bajo: 1 u.' in respuesta.content
    if restante == 0:
        assert b'bg-danger ms-1">Agotado' in respuesta.content
        assert b'Agregar al carrito' not in respuesta.content
    detalle = client.get(reverse("catalog:producto_detalle", args=[p.id]))
    assert detalle.context["disponibilidad"]["stock_disponible"] == restante
    if restante == 1:
        assert b'text-danger' in detalle.content
        assert b'max="1"' in detalle.content
    # El carrito de un cliente no reduce la disponibilidad visible de otro.
    assert Client().get(reverse("catalog:catalogo")).context["items"][0].stock_disponible == 40
    client.post(reverse("orders:quitar", args=[p.id]))
    assert client.get(reverse("catalog:catalogo")).context["items"][0].stock_disponible == 40


def test_catalogo_no_descuenta_dos_veces_un_pedido_confirmado(client):
    pedido, p = carrito(client)
    confirmar(client)
    session = client.session
    session["pedido_web"] = str(pedido.id)
    session.save()
    assert client.get(reverse("catalog:catalogo")).context["items"][0].stock_disponible == 8


def test_quitar_exige_post_csrf_propietario_y_borrador(client):
    pedido, p = carrito(client)
    ruta = reverse("orders:quitar", args=[p.id])
    assert client.get(ruta).status_code == 405
    seguro = Client(enforce_csrf_checks=True)
    seguro.cookies = client.cookies
    assert seguro.post(ruta).status_code == 403
    otro = Client()
    registrar(otro, "otro@example.com", "87654321")
    iniciar(otro, "otro@example.com")
    session = otro.session
    session["pedido_web"] = str(pedido.id)
    session.save()
    assert otro.post(ruta).status_code == 404
    confirmar(client)
    session = client.session
    session["pedido_web"] = str(pedido.id)
    session.save()
    assert client.post(ruta).status_code == 302
    assert pedido.detalles.get().cantidad == 2
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 2


def test_confirmacion_revierte_todas_las_reservas_si_una_linea_se_agota(client):
    pedido, p = carrito(client)
    segundo = ProductoModel.objects.create(id=uuid.uuid4(), nombre="Otro pan", codigo_barras="7751234567891",
                                           costo=1, precio_venta=2, estado="ACTIVO")
    stock = ExistenciaModel.objects.create(id=uuid.uuid4(), producto_id=segundo.id, cantidad=5)
    client.post(reverse("orders:agregar", args=[segundo.id]), {"cantidad": 2})
    stock.cantidad = 0
    stock.save()
    assert confirmar(client).status_code == 200
    pedido.refresh_from_db()
    assert pedido.estado == "BORRADOR"
    assert pedido.hora_recojo is None
    assert ReservaModel.objects.count() == 0
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 0


def test_entrega_antes_de_listo_no_consume_stock(client):
    pedido, p = carrito(client)
    confirmar(client)
    sesion = client.session
    sesion["rol"] = "CAJERO"
    sesion.save()
    client.post(reverse("orders:cambiar_estado", args=[pedido.id]), {"estado": "ENTREGADO"})
    pedido.refresh_from_db()
    assert pedido.estado == "CONFIRMADO"
    stock = ExistenciaModel.objects.get(producto_id=p.id)
    assert (stock.cantidad, stock.reservada) == (10, 2)


def test_reserva_confirmada_no_expira_antes_del_recojo(client):
    from src.modules.inventory.infrastructure.factories import construir_reserva_repository
    pedido, _ = carrito(client)
    confirmar(client)
    ReservaModel.objects.update(expira_en=timezone.now() - timedelta(days=1))
    repo = construir_reserva_repository()
    assert repo.buscar_por_id(ReservaModel.objects.get().id).activa
    assert repo.listar_activas_expiradas() == []


def test_producto_sin_stock_se_confirma_sin_reserva(client):
    pedido, p = carrito(client)
    # Un servicio no requiere existencia física.
    servicio = ProductoModel.objects.create(id=uuid.uuid4(), nombre="Personalización", codigo_barras="7751234567892",
                                            costo=1, precio_venta=2, estado="ACTIVO", requiere_stock=False)
    client.post(reverse("orders:agregar", args=[servicio.id]), {"cantidad": 1})
    assert confirmar(client).status_code == 302
    assert pedido.detalles.get(producto_id=servicio.id).requiere_stock is False
    assert ReservaModel.objects.count() == 1
    assert ReservaModel.objects.get().producto_id == p.id


def test_cambios_requieren_post_y_csrf(client):
    pedido, _ = carrito(client)
    assert client.get(reverse("orders:cancelar", args=[pedido.id])).status_code == 405
    seguro = Client(enforce_csrf_checks=True)
    seguro.cookies = client.cookies
    assert seguro.post(reverse("orders:cancelar", args=[pedido.id])).status_code == 403
    pedido.refresh_from_db()
    assert pedido.estado == "BORRADOR"


def test_email_no_enviado_queda_pendiente_y_se_recupera(client, monkeypatch):
    from src.modules.orders.infrastructure.notifications.email_notifier import EmailNotifier
    pedido, _ = carrito(client)
    confirmar(client)
    PedidoModel.objects.filter(pk=pedido.id).update(estado="LISTO")
    with monkeypatch.context() as contexto:
        contexto.setattr(EmailNotifier, "_enviar", lambda *args: False)
        assert run(str(pedido.id)) is False
    pedido.refresh_from_db()
    assert not pedido.notificado_listo
    assert run(str(pedido.id)) is True
    pedido.refresh_from_db()
    assert pedido.notificado_listo
    assert mail.outbox[-1].to == ["ana@example.com"]
