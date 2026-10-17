import pytest
from django.core import mail
from django.urls import reverse
from pytest_bdd import given, when, then, scenarios

from tests.integration.test_pedidos_online import carrito, confirmar
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel

pytestmark = [pytest.mark.uat, pytest.mark.django_db]
scenarios("features/pedidos_online.feature")


@given("una cliente web autenticada con dos panes en su carrito", target_fixture="contexto")
def cliente(client):
    pedido, producto = carrito(client)
    return {"pedido": pedido, "producto": producto}


@when("confirma el pedido para recojo mañana en una franja válida")
def confirma(client):
    assert confirmar(client).status_code == 302


@when("solicita cancelar su pedido")
def cancela(client, contexto):
    assert client.post(reverse("orders:cancelar", args=[contexto["pedido"].id])).status_code == 302


def estado_tienda(client, contexto, estado):
    sesion = client.session
    sesion["rol"] = "CAJERO"
    sesion.save()
    assert client.post(reverse("orders:cambiar_estado", args=[contexto["pedido"].id]), {"estado": estado}).status_code == 302
    sesion = client.session
    sesion["rol"] = "CLIENTE"
    sesion.save()


@when("la tienda inicia la preparación")
def prepara(client, contexto):
    estado_tienda(client, contexto, "EN_PREPARACION")


@when("la tienda marca el pedido Listo")
def listo(client, contexto, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        estado_tienda(client, contexto, "LISTO")


def comprobar(contexto, estado, reservada):
    pedido = contexto["pedido"]
    pedido.refresh_from_db()
    assert pedido.estado == estado
    assert ExistenciaModel.objects.get(producto_id=contexto["producto"].id).reservada == reservada


@then("el pedido queda Pendiente con dos unidades reservadas")
def pendiente(contexto):
    comprobar(contexto, "CONFIRMADO", 2)
    assert contexto["pedido"].hora_recojo is not None


@then("el pedido queda Cancelado y el stock queda disponible")
def cancelado(contexto):
    comprobar(contexto, "CANCELADO", 0)


@then("el pedido sigue En preparación y conserva su reserva")
def preparando(contexto):
    comprobar(contexto, "EN_PREPARACION", 2)


@then("la cliente recibe un email con su número de pedido")
def notificada(contexto):
    comprobar(contexto, "LISTO", 2)
    assert contexto["pedido"].notificado_listo
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["ana@example.com"]
    assert contexto["pedido"].numero in mail.outbox[0].subject
