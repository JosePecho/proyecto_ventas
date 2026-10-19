import json
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.infrastructure.factories import construir_repositorio, construir_hasher
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.promotions.infrastructure.persistence.django_models.promocion_model import PromocionModel
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.modules.sales.infrastructure.persistence.django_models.detalle_venta_model import DetalleVentaModel
from src.modules.sales.infrastructure.persistence.django_models.pago_model import PagoModel
from src.modules.catalog.infrastructure.persistence.django_models.categoria_model import CategoriaModel
from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
from src.modules.reporting.infrastructure.factories import construir_reporte_repository
from src.modules.promotions.infrastructure.tasks.actualizar_estado_promociones import run as actualizar_promos
from tests.integration.test_pedidos_online import producto

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
PASSWORD = "Clave!Arquitectura#275"


def staff(client, rol="ADMINISTRADOR"):
    username = "qa_" + uuid4().hex[:12]
    usuario = CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(
        UsuarioInputDTO(username=username, password=PASSWORD, nombre_completo="Personal QA", rol=rol))
    client.force_login(User.objects.create_user(username=username))
    session = client.session
    session["rol"], session["usuario_id"] = rol, usuario.id
    session.save()
    return usuario


def compra(cliente, total=10, dias=0, estado="PAGADA", producto_id=None, costo=3):
    p = producto_id or uuid4()
    venta = VentaModel.objects.create(id=uuid4(), numero_ticket="T" + uuid4().hex[:15], cajero_id=uuid4(),
        cliente_id=cliente.id, estado=estado, subtotal=total, total=total, moneda="PEN")
    VentaModel.objects.filter(pk=venta.id).update(fecha_creacion=timezone.now() - timedelta(days=dias))
    DetalleVentaModel.objects.create(id=uuid4(), venta=venta, producto_id=p, producto_nombre="Pan auditado",
        cantidad=1, precio_unitario=total, subtotal=total, total=total, costo_unitario=costo)
    PagoModel.objects.create(id=uuid4(), venta=venta, metodo="EFECTIVO", monto=total)
    return venta


def promo_payload(tipo="PORCENTAJE", **extra):
    datos = {"nombre": "Promo QA", "tipo": tipo, "descuento_valor": "10", "accion": "crear"}
    datos.update(extra)
    return datos


def test_rf038_cajero_registra_dni_telefono_sin_asociarse_como_dueno(client):
    staff(client, "CAJERO")
    respuesta = client.post(reverse("customers:registro"), {"nombre": "Cliente frecuente", "dni": "12345678", "telefono": "987654321"})
    assert respuesta.status_code == 302
    cliente = ClienteModel.objects.get()
    assert cliente.usuario_id is None
    assert cliente.dni == "12345678"
    assert cliente.telefono == "987654321"
    assert AuditoriaModel.objects.filter(entidad="ClienteModel", entidad_id=str(cliente.id), accion="CREAR").exists()


def test_rf039_y_rf043_historial_propio_suma_solo_pagadas(client):
    usuario = staff(client, "CLIENTE")
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Ana", usuario_id=usuario.id)
    compra(cliente, total=10, dias=2)
    compra(cliente, total=20)
    compra(cliente, total=999, estado="ANULADA")
    respuesta = client.get(reverse("customers:historial", args=[cliente.id]))
    assert respuesta.status_code == 200
    assert respuesta.context["historial"]["cantidad"] == 2
    assert respuesta.context["historial"]["total_gastado"] == 30
    assert respuesta.context["frecuencia"]["clasificacion"] == "FRECUENTE"
    otro = ClienteModel.objects.create(id=uuid4(), nombre="Ajeno", usuario_id=uuid4())
    assert client.get(reverse("customers:historial", args=[otro.id])).status_code == 403


@pytest.mark.parametrize("tipo", ["PORCENTAJE", "NX1", "COMBO"])
def test_rf041_admin_crea_tipos_reales_y_edita(client, tipo):
    staff(client)
    p = producto()
    extra = {"producto_id": str(p.id)} if tipo == "NX1" else {}
    if tipo == "NX1":
        extra["descuento_valor"] = "0"
    if tipo == "COMBO":
        from src.modules.catalog.models import ProductoModel
        segundo = ProductoModel.objects.create(id=uuid4(), nombre="Jugo", codigo_barras="7751234567891", costo=1, precio_venta=5, estado="ACTIVO")
        extra["componentes"] = json.dumps([{"producto_id": str(p.id), "cantidad": 1}, {"producto_id": str(segundo.id), "cantidad": 1}])
    respuesta = client.post(reverse("promotions:crear"), promo_payload(tipo, **extra))
    assert respuesta.status_code == 302
    promocion = PromocionModel.objects.get()
    assert promocion.tipo == tipo
    assert client.get(reverse("promotions:editar", args=[promocion.id])).status_code == 200
    respuesta = client.post(reverse("promotions:editar", args=[promocion.id]), promo_payload(tipo, nombre="Editada", **extra))
    assert respuesta.status_code == 302
    promocion.refresh_from_db()
    assert promocion.nombre == "Editada"


@pytest.mark.parametrize("extra", [{"descuento_valor": "150"}, {"vigencia_desde": "mal"}, {"vigencia_hasta": "2099-01-01T10:00"}])
def test_rf041_042_entrada_invalida_se_muestra_sin_500(client, extra):
    staff(client)
    respuesta = client.post(reverse("promotions:crear"), promo_payload(**extra))
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    assert PromocionModel.objects.count() == 0


def test_rf042_programada_ya_vencida_no_se_activa_temporalmente(client):
    staff(client)
    ahora = timezone.localtime()
    datos = promo_payload(vigencia_desde=(ahora + timedelta(days=1)).isoformat(), vigencia_hasta=(ahora + timedelta(days=2)).isoformat())
    assert client.post(reverse("promotions:crear"), datos).status_code == 302
    promocion = PromocionModel.objects.get()
    assert promocion.estado == "PROGRAMADA"
    PromocionModel.objects.filter(pk=promocion.id).update(vigencia_desde=ahora - timedelta(days=2), vigencia_hasta=ahora - timedelta(days=1))
    resultado = actualizar_promos()
    assert resultado == {"activadas": 0, "finalizadas": 1}
    promocion.refresh_from_db()
    assert promocion.estado == "FINALIZADA"
    assert client.get(reverse("promotions:activas"), HTTP_ACCEPT="application/json").json() == {"promociones": []}


def test_rf042_admin_cancela_vencida_sin_reactivarla_y_audita(client):
    administrador = staff(client)
    promocion = PromocionModel.objects.create(id=uuid4(), nombre="Vencida cancelable", tipo="PORCENTAJE",
                                            estado="FINALIZADA", descuento_valor=10)
    respuesta = client.post(reverse("promotions:promociones"), {"accion": "cancelar", "promocion_id": str(promocion.id)})
    assert respuesta.status_code == 302
    promocion.refresh_from_db()
    assert promocion.estado == "CANCELADA"
    assert AuditoriaModel.objects.filter(entidad_id=str(promocion.id), usuario_id=administrador.id, accion="ACTUALIZAR").exists()
    respuesta = client.post(reverse("promotions:promociones"), {"accion": "activar", "promocion_id": str(promocion.id)})
    assert respuesta.status_code == 200 and respuesta.context["form"].errors
    promocion.refresh_from_db()
    assert promocion.estado == "CANCELADA"
    assert client.get(reverse("promotions:activas"), HTTP_ACCEPT="application/json").json() == {"promociones": []}


@pytest.mark.parametrize("vista", ["ventas", "utilidad", "productos"])
@pytest.mark.parametrize("datos", [{"desde": "mal"}, {"desde": "2026-05-02", "hasta": "2026-05-01"}])
def test_rf045_filtros_invalidos_retornan_400(client, vista, datos):
    staff(client)
    assert client.get(reverse(f"reporting:{vista}"), datos).status_code == 400


def test_rf044_047_reportes_excluyen_anuladas_y_conservan_costo_historico(client):
    staff(client)
    p = producto()
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Ana")
    compra(cliente, total=20, producto_id=p.id, costo=3)
    compra(cliente, total=999, estado="ANULADA", producto_id=p.id)
    p.costo = 100
    p.save()
    hoy = timezone.localdate()
    repo = construir_reporte_repository()
    assert repo.ventas_por_dia(hoy, hoy)[0]["total"] == 20
    assert repo.totales_por_metodo_pago(hoy, hoy) == {"EFECTIVO": 20.0}
    assert repo.productos_mas_vendidos(hoy, hoy)[0]["unidades"] == 1
    utilidad = repo.utilidad_por_producto(hoy, hoy)[0]
    assert utilidad["costo"] == 3
    assert utilidad["utilidad"] == 17
    for vista in ("dashboard", "ventas", "utilidad", "productos"):
        assert client.get(reverse(f"reporting:{vista}")).status_code == 200


def test_rf048_crear_editar_desactivar_y_revocar_sesion(client):
    staff(client)
    payload = {"username": "nuevo_qa", "nombre_completo": "Cajero QA", "password": PASSWORD, "rol": "CAJERO"}
    assert client.post(reverse("identity:usuario_nuevo"), payload).status_code == 302
    nuevo = construir_repositorio().buscar_por_username("nuevo_qa")
    assert client.post(reverse("identity:usuario_nuevo"), dict(payload, username="NUEVO_QA")).status_code == 200
    datos_auditados = json.dumps(list(AuditoriaModel.objects.filter(entidad="UsuarioModel").values("detalle")))
    assert PASSWORD not in datos_auditados
    assert nuevo.password_hash not in datos_auditados
    otro = Client()
    assert otro.post(reverse("identity:login"), {"username": "nuevo_qa", "password": PASSWORD}).status_code == 302
    assert client.post(reverse("identity:usuario_editar", args=[nuevo.id]), dict(payload, nombre_completo="Nombre editado", rol="GERENTE")).status_code == 302
    assert construir_repositorio().buscar_por_id(nuevo.id).nombre_completo == "Nombre editado"
    assert otro.get(reverse("catalog:catalogo")).status_code == 302
    assert "usuario_id" not in otro.session
    assert otro.post(reverse("identity:login"), {"username": "nuevo_qa", "password": PASSWORD}).status_code == 302
    assert otro.session["rol"] == "GERENTE"
    assert client.post(reverse("identity:usuario_desactivar", args=[nuevo.id])).status_code == 302
    assert not construir_repositorio().buscar_por_id(nuevo.id).activo
    assert otro.get(reverse("catalog:catalogo")).status_code == 302
    assert "usuario_id" not in otro.session


def test_rf049_050_categoria_edicion_auditable_y_sin_secretos(client):
    usuario = staff(client)
    assert client.post(reverse("catalog:categorias"), {"nombre": "Panadería"}).status_code == 302
    categoria = CategoriaModel.objects.get(nombre="Panadería")
    assert client.post(reverse("catalog:categoria_editar", args=[categoria.id]), {"nombre": "Panes", "descripcion": "Frescos"}).status_code == 302
    categoria.refresh_from_db()
    assert categoria.nombre == "Panes"
    registros = AuditoriaModel.objects.filter(entidad="CategoriaModel", entidad_id=str(categoria.id))
    assert set(registros.values_list("accion", flat=True)) == {"CREAR", "ACTUALIZAR"}
    assert all(str(r.usuario_id) == usuario.id and r.fecha for r in registros)
    assert PASSWORD not in json.dumps(list(registros.values("detalle")))


@pytest.mark.parametrize("rol", ["CLIENTE", "CAJERO", "ALMACENERO"])
def test_no_administradores_no_mutan_usuarios_ni_reportes(client, rol):
    staff(client, rol)
    assert client.get(reverse("identity:usuarios")).status_code == 302
    assert client.get(reverse("reporting:ventas")).status_code == 302
    assert client.post(reverse("promotions:crear"), promo_payload()).status_code == 302
    assert PromocionModel.objects.count() == 0


def test_rf040_descuento_automatico_se_persiste_y_cobra_con_stock_real(client):
    from django.db import transaction
    from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
    from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
    from src.modules.sales.application.use_cases.agregar_producto import AgregarProducto
    from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
    from src.modules.sales.domain.entities.venta import Venta
    from src.modules.sales.infrastructure.factories import construir_venta_repository, construir_inventario_port, construir_auditoria_port, construir_promociones_port
    from src.modules.catalog.infrastructure.factories import construir_producto_repository
    usuario = staff(client, "CAJERO")
    p = producto()
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Recurrente", dni="12345678")
    compra(cliente, dias=2)
    compra(cliente, dias=1)
    PromocionModel.objects.create(id=uuid4(), nombre="Fidelización", tipo="PORCENTAJE", estado="ACTIVA",
        descuento_valor=10, aplica_clientes_frecuentes=True)
    repo = construir_venta_repository()
    venta = VentaAggregate(Venta(numero_ticket="T-FRECUENCIA", cajero_id=usuario.id))
    repo.guardar(venta)
    AgregarProducto(repo, construir_inventario_port(), construir_promociones_port()).ejecutar(
        str(venta.venta.id), construir_producto_repository().buscar_por_id(p.id), 2)
    assert client.post(reverse("sales:asignar_cliente", args=[venta.venta.id]), {"dni": cliente.dni}).status_code == 302
    recuperada = repo.buscar_por_id(venta.venta.id)
    assert recuperada.venta.total == 3.6
    assert recuperada.descuento_venta_pct == 10
    resultado = ProcesarPago(repo, construir_inventario_port(), construir_auditoria_port(),
        uow=transaction.atomic(), promociones=construir_promociones_port()).ejecutar(
            ProcesarPagoDTO(venta_id=str(venta.venta.id), metodo="EFECTIVO", monto=Decimal("3.60"), monto_entregado=Decimal("3.60")))
    assert resultado["estado"] == "PAGADA"
    hoy = timezone.localdate()
    utilidad = construir_reporte_repository().utilidad_por_producto(hoy, hoy)
    fila = next(f for f in utilidad if f["producto_id"] == str(p.id))
    assert fila["ingresos"] == 3.6
    assert fila["costo"] == 2
    assert fila["utilidad"] == 1.6


def test_rf050_fallo_de_auditoria_revierte_mutacion(client, monkeypatch):
    from django.db import DatabaseError
    staff(client)
    def fallo(*args, **kwargs):
        raise DatabaseError("Auditoría indisponible")
    monkeypatch.setattr(AuditoriaModel.objects, "create", fallo)
    client.raise_request_exception = False
    respuesta = client.post(reverse("catalog:categorias"), {"nombre": "No debe persistir"})
    assert respuesta.status_code == 500
    assert not CategoriaModel.objects.filter(nombre="No debe persistir").exists()


@pytest.mark.parametrize("telefono", ["abc", "123", "9" * 16])
def test_rf038_telefono_invalido_no_produce_500(client, telefono):
    staff(client, "CAJERO")
    respuesta = client.post(reverse("customers:registro"), {"nombre": "Cliente", "dni": "12345678", "telefono": telefono})
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    assert ClienteModel.objects.count() == 0


def test_migracion_preserva_descuento_global_y_no_inventa_costos():
    from importlib import import_module
    from django.apps import apps
    from src.modules.sales.infrastructure.factories import construir_venta_repository
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Venta histórica")
    historica = compra(cliente, total=20, costo=None, estado="BORRADOR")
    VentaModel.objects.filter(pk=historica.id).update(subtotal=20, descuento=2, total=18)
    import_module("src.modules.sales.migrations.0004_preservar_descuentos_existentes").preservar(apps, None)
    agregado = construir_venta_repository().buscar_por_id(historica.id)
    agregado.calcular_totales()
    assert agregado.venta.total == 18
    assert agregado.descuento_venta_pct == 10
    assert agregado.lineas[0].costo_unitario is None
