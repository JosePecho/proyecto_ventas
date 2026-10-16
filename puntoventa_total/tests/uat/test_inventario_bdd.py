"""Nivel 4: criterios de negocio sobre vistas y persistencia reales."""
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.core import mail
from django.db import transaction
from pytest_bdd import given, parsers, scenarios, then, when

from src.modules.catalog.models import ProductoModel
from src.modules.inventory.application.dto.lote_dto import RecepcionLoteDTO
from src.modules.inventory.application.use_cases.recibir_mercaderia import RecibirMercaderia
from src.modules.inventory.infrastructure.factories import (
    construir_lote_repository, construir_movimiento_repository, construir_stock_repository,
)
from src.modules.inventory.models import ExistenciaModel, LoteModel, MovimientoModel

pytestmark = [pytest.mark.uat, pytest.mark.django_db]
scenarios("features/inventario.feature")


@given("un almacenero autenticado con un producto y minimo de 5 unidades", target_fixture="contexto")
def almacen(client, django_user_model):
    user = django_user_model.objects.create_user(username="almacen_bdd")
    client.force_login(user)
    session = client.session
    session["rol"] = "ALMACENERO"
    session["usuario_id"] = str(uuid4())
    session.save()
    p = ProductoModel.objects.create(id=uuid4(), nombre="Leche UAT", codigo_barras="7751234567802",
                                    costo=Decimal("5"), precio_venta=Decimal("10"), estado="ACTIVO", stock_minimo=5)
    return {"client": client, "producto": p}


def recepcion(contexto, cantidad, numero="UAT-PREVIO", dias=20):
    return RecibirMercaderia(construir_stock_repository(), construir_lote_repository(), construir_movimiento_repository(),
                            uow=transaction.atomic()).ejecutar(
        RecepcionLoteDTO(str(contexto["producto"].id), numero, cantidad, 5,
                        fecha_vencimiento=date.today() + timedelta(days=dias)))


@when(parsers.parse('registra una recepcion de {cantidad:d} unidades con lote "{numero}"'))
def registrar_recepcion(contexto, cantidad, numero):
    contexto["respuesta"] = contexto["client"].post("/inventario/recepcion/", {
        "producto_id": str(contexto["producto"].id), "numero_lote": numero,
        "cantidad": cantidad, "costo_unitario": "5",
        "fecha_vencimiento": (date.today() + timedelta(days=20)).isoformat(),
    })
    assert contexto["respuesta"].status_code == 302


@given(parsers.parse("una recepcion previa de {cantidad:d} unidades"))
def recepcion_previa(contexto, cantidad):
    recepcion(contexto, cantidad)


@when(parsers.parse('registra una merma de {cantidad:d} unidades por "{motivo}"'))
def registrar_merma(contexto, cantidad, motivo, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        contexto["respuesta"] = contexto["client"].post("/inventario/mermas/", {
            "producto_id": str(contexto["producto"].id), "cantidad": cantidad, "motivo": motivo,
        })


@then(parsers.parse("el stock fisico es de {cantidad:d} unidades"))
def verificar_stock(contexto, cantidad):
    assert ExistenciaModel.objects.get(producto_id=contexto["producto"].id).cantidad == cantidad
    assert sum(LoteModel.objects.filter(producto_id=contexto["producto"].id).values_list("cantidad_restante", flat=True)) == cantidad


@then(parsers.parse("el kardex contiene una entrada de {cantidad:d} unidades"))
def verificar_entrada(contexto, cantidad):
    assert MovimientoModel.objects.filter(producto_id=contexto["producto"].id, tipo="ENTRADA", cantidad=cantidad).count() == 1


@then(parsers.parse('el kardex conserva el motivo "{motivo}"'))
def verificar_motivo(contexto, motivo):
    assert MovimientoModel.objects.filter(producto_id=contexto["producto"].id, tipo="MERMA", referencia=motivo).exists()


@then("la operacion muestra un error de validacion")
def verificar_error(contexto):
    assert contexto["respuesta"].status_code == 200
    assert contexto["respuesta"].context["form"].errors


@then("no hay movimientos de merma")
def verificar_sin_merma(contexto):
    assert not MovimientoModel.objects.filter(producto_id=contexto["producto"].id, tipo="MERMA").exists()


@then("recibe una notificacion de stock minimo")
def verificar_notificacion(contexto):
    assert len(mail.outbox) == 1
    assert str(contexto["producto"].id) in mail.outbox[0].body


@given("un lote que vence en 30 dias y otro en 31 dias")
def lotes_limite(contexto):
    recepcion(contexto, 2, "UAT-30", 30)
    recepcion(contexto, 2, "UAT-31", 31)


@when("consulta las alertas de inventario")
def consultar_alertas(contexto):
    contexto["respuesta"] = contexto["client"].get("/inventario/alertas/")
    assert contexto["respuesta"].status_code == 200


@then("ve solo el lote que vence en 30 dias")
def verificar_alertas(contexto):
    assert [l.numero_lote for l in contexto["respuesta"].context["por_vencer"]] == ["UAT-30"]


@given("otro producto con margen mayor y sin ventas")
def producto_mayor_margen(contexto):
    contexto["otro"] = ProductoModel.objects.create(id=uuid4(), nombre="Mayor margen UAT", codigo_barras="7751234567803",
                                                   costo=Decimal("5"), precio_venta=Decimal("15"), estado="ACTIVO")


@when("consulta los reportes de inventario")
def consultar_reportes(contexto):
    contexto["respuesta"] = contexto["client"].get("/reportes/inventario/")
    assert contexto["respuesta"].status_code == 200


@then("ambos productos aparecen en baja rotacion")
def verificar_baja_rotacion(contexto):
    ids = {p["producto_id"] for p in contexto["respuesta"].context["baja_rotacion"]}
    assert ids == {str(contexto["producto"].id), str(contexto["otro"].id)}


@then("el producto con mayor margen encabeza el ranking")
def verificar_ranking(contexto):
    assert contexto["respuesta"].context["mayor_ganancia"][0]["producto_id"] == str(contexto["otro"].id)
