"""Aceptacion RF-016..RF-024 con vistas, repositorios y transacciones reales."""
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core import mail
from django.db import transaction
from django.utils import timezone

from src.modules.catalog.infrastructure.persistence.django_models.categoria_model import CategoriaModel
from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
from src.modules.catalog.infrastructure.factories import construir_producto_repository
from src.modules.inventory.application.dto.lote_dto import RecepcionLoteDTO
from src.modules.inventory.application.use_cases.consultar_kardex import ConsultarKardex
from src.modules.inventory.application.use_cases.consultar_stock import ConsultarStock
from src.modules.inventory.application.use_cases.recibir_mercaderia import RecibirMercaderia
from src.modules.inventory.infrastructure.factories import (
    construir_lote_repository, construir_movimiento_repository, construir_stock_repository,
)
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import LoteModel
from src.modules.inventory.infrastructure.persistence.django_models.movimiento_model import MovimientoModel
from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente
from src.modules.reporting.application.use_cases.reporte_baja_rotacion import ReporteBajaRotacion
from src.modules.reporting.infrastructure.factories import construir_reporte_repository
from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoModificable
from src.modules.sales.infrastructure.factories import (
    construir_auditoria_port, construir_inventario_port, construir_venta_repository,
)
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_reserva_orm_aware_y_liberacion_idempotente():
    from src.modules.inventory.application.use_cases.liberar_reserva import LiberarReserva
    from src.modules.inventory.domain.entities.reserva_stock import ReservaStock
    from src.modules.inventory.infrastructure.persistence.repositories.django_reserva_repository import DjangoReservaRepository

    p = producto()
    ExistenciaModel.objects.create(id=uuid.uuid4(), producto_id=p.id, cantidad=10, reservada=5)
    reservas = DjangoReservaRepository()
    primera = reservas.guardar(ReservaStock(producto_id=str(p.id), cantidad=3))
    segunda = reservas.guardar(ReservaStock(producto_id=str(p.id), cantidad=2))
    cargada = reservas.buscar_por_id(primera.id)
    assert timezone.is_aware(cargada.expira_en)
    assert cargada.activa
    cargada.extender(30)
    reservas.guardar(cargada)
    liberar = LiberarReserva(construir_stock_repository(), reservas, uow=transaction.atomic())
    liberar.ejecutar(str(primera.id))
    liberar.ejecutar(str(primera.id))
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 2
    assert reservas.buscar_por_id(segunda.id).activa
    assert reservas.listar_activas_expiradas() == []
    vencida = reservas.buscar_por_id(segunda.id)
    vencida.expira_en = timezone.now() - timedelta(seconds=1)
    reservas.guardar(vencida)
    assert [r.id for r in reservas.listar_activas_expiradas()] == [segunda.id]
    assert liberar.liberar_expiradas() == 1
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 0
    assert liberar.liberar_expiradas() == 0


@pytest.fixture
def almacen(client, django_user_model):
    user = django_user_model.objects.create_user(username="almacen_inventario", password="test")
    client.force_login(user)
    session = client.session
    session["rol"] = "ALMACENERO"
    session["usuario_id"] = str(uuid.uuid4())
    session.save()
    return client


def producto(**kwargs):
    datos = dict(id=uuid.uuid4(), nombre="Producto inventario", codigo_barras=f"{uuid.uuid4().int % 10**13:013d}",
                 costo=Decimal("5"), precio_venta=Decimal("10"), estado="ACTIVO", stock_minimo=5)
    datos.update(kwargs)
    return ProductoModel.objects.create(**datos)


def recibir(p, cantidad=10, dias=20):
    return RecibirMercaderia(
        construir_stock_repository(), construir_lote_repository(), construir_movimiento_repository(),
        uow=transaction.atomic(),
    ).ejecutar(RecepcionLoteDTO(producto_id=str(p.id), numero_lote=f"L-{uuid.uuid4().hex[:8]}",
                              cantidad=cantidad, costo_unitario=Decimal("5"),
                              fecha_vencimiento=date.today() + timedelta(days=dias)))


def venta_guardada(*productos, cantidad=2):
    agregado = VentaAggregate(venta=Venta(numero_ticket=f"INV-{uuid.uuid4().hex[:12]}", cajero_id=str(uuid.uuid4())))
    for p in productos:
        agregado.agregar_producto(str(p.id), p.nombre, cantidad, Monto(p.precio_venta))
    agregado.calcular_totales()
    construir_venta_repository().guardar(agregado)
    return agregado


def cobrar(venta, monto):
    return ProcesarPago(construir_venta_repository(), construir_inventario_port(), construir_auditoria_port(),
                        uow=transaction.atomic()).ejecutar(
        ProcesarPagoDTO(venta_id=str(venta.venta.id), metodo="EFECTIVO", monto=monto))


def datos_producto(categoria, **kwargs):
    datos = {"nombre": "Leche", "codigo_barras": "7751234567890", "costo": "5", "precio_venta": "8",
             "categoria_id": str(categoria.id), "stock_minimo": "8",
             "fecha_vencimiento": (date.today() + timedelta(days=20)).isoformat()}
    datos.update(kwargs)
    return datos


def test_rf016_almacenero_crea_y_edita_todos_los_campos(almacen):
    categoria = CategoriaModel.objects.create(id=uuid.uuid4(), nombre="Lacteos", slug="lacteos")
    datos = datos_producto(categoria)
    respuesta = almacen.post("/catalogo/productos/nuevo/", datos)
    assert respuesta.status_code == 302
    p = ProductoModel.objects.get(codigo_barras=datos["codigo_barras"])
    entidad = construir_producto_repository().buscar_por_id(str(p.id))
    assert entidad.categoria_id == str(categoria.id)
    assert entidad.stock_minimo == 8
    assert entidad.fecha_vencimiento == date.fromisoformat(datos["fecha_vencimiento"])
    form = almacen.get(f"/catalogo/productos/{p.id}/editar/").context["form"]
    assert form.initial["nombre"] == "Leche"
    assert form.initial["stock_minimo"] == 8
    datos.update(nombre="Leche entera", stock_minimo="3", fecha_vencimiento="", codigo_barras="7751234567891")
    assert almacen.post(f"/catalogo/productos/{p.id}/editar/", datos).status_code == 302
    p.refresh_from_db()
    assert (p.nombre, p.stock_minimo, p.fecha_vencimiento, p.codigo_barras) == ("Leche entera", 3, None, "7751234567891")


@pytest.mark.parametrize("campo,valor", [("stock_minimo", "-1"), ("categoria_id", ""), ("codigo_barras", "abc"),
                                         ("precio_venta", "5.01"), ("fecha_vencimiento", "2026-02-30")])
def test_rf016_datos_invalidos_no_crean_producto(almacen, campo, valor):
    categoria = CategoriaModel.objects.create(id=uuid.uuid4(), nombre="Categoria", slug="categoria")
    respuesta = almacen.post("/catalogo/productos/nuevo/", datos_producto(categoria, **{campo: valor}))
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    assert not ProductoModel.objects.exists()


def test_rf016_codigo_duplicado_no_deja_actualizacion_parcial(almacen):
    categoria = CategoriaModel.objects.create(id=uuid.uuid4(), nombre="Categoria", slug="categoria")
    primero, segundo = producto(categoria=categoria), producto(categoria=categoria, nombre="Original")
    respuesta = almacen.post(f"/catalogo/productos/{segundo.id}/editar/",
                             datos_producto(categoria, nombre="No guardar", codigo_barras=primero.codigo_barras))
    assert respuesta.context["form"].non_field_errors()
    segundo.refresh_from_db()
    assert segundo.nombre == "Original"


def test_rf017_cobro_parcial_total_y_reintento(almacen):
    p = producto()
    recibir(p)
    venta = venta_guardada(p)
    assert cobrar(venta, 5)["estado"] == "PENDIENTE"
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 10
    assert cobrar(venta, 15)["estado"] == "PAGADA"
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 8
    assert LoteModel.objects.get(producto_id=p.id).cantidad_restante == 8
    salida = MovimientoModel.objects.get(producto_id=p.id, tipo="SALIDA_VENTA")
    assert salida.cantidad == 2 and salida.stock_resultante == 8
    assert str(salida.usuario_id) == venta.venta.cajero_id
    with pytest.raises(VentaNoModificable):
        cobrar(venta, 20)
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 8


def test_rf017_segunda_linea_sin_stock_revierte_venta_lotes_y_kardex(django_capture_on_commit_callbacks):
    p, otro = producto(), producto()
    recibir(p, cantidad=6)
    recibir(otro, cantidad=1)
    venta = venta_guardada(p, otro)
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        with pytest.raises(StockInsuficiente):
            cobrar(venta, 40)
    assert callbacks == []
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 6
    assert LoteModel.objects.get(producto_id=p.id).cantidad_restante == 6
    assert not MovimientoModel.objects.filter(tipo="SALIDA_VENTA").exists()
    recuperada = construir_venta_repository().buscar_por_id(str(venta.venta.id))
    assert recuperada.venta.es_borrador and not recuperada.pagos


def test_rf017_consultas_stock_sin_cache_obsoleta_ni_cruce_entre_productos():
    p, otro = producto(), producto()
    recibir(p, 10)
    recibir(otro, 20)
    consulta = ConsultarStock(construir_stock_repository())
    assert consulta.ejecutar(str(p.id)).disponible == 10
    assert consulta.ejecutar(str(otro.id)).disponible == 20
    construir_inventario_port().descontar(str(p.id), 2, "VENTA:consulta")
    assert consulta.ejecutar(str(p.id)).disponible == 8
    assert consulta.ejecutar(str(otro.id)).disponible == 20


def test_rf017_peps_omite_vencidos_y_salida_conserva_trazabilidad():
    p = producto()
    vencido, cercano, lejano = recibir(p, 5, -1), recibir(p, 2, 3), recibir(p, 8, 90)
    construir_inventario_port().descontar(str(p.id), 4, "VENTA:PEPS")
    assert LoteModel.objects.get(pk=vencido.id).cantidad_restante == 5
    assert LoteModel.objects.get(pk=cercano.id).cantidad_restante == 0
    assert LoteModel.objects.get(pk=lejano.id).cantidad_restante == 6
    salidas = list(MovimientoModel.objects.filter(tipo="SALIDA_VENTA").order_by("fecha"))
    assert [s.cantidad for s in salidas] == [2, 2]
    assert [s.stock_resultante for s in salidas] == [13, 11]
    assert {str(s.lote_id) for s in salidas} == {cercano.id, lejano.id}


def test_rf017_stock_solo_vencido_no_se_vende():
    p = producto()
    recibir(p, 5, -1)
    with pytest.raises(StockInsuficiente):
        construir_inventario_port().descontar(str(p.id), 2, "VENTA:vencido")
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 5
    assert not MovimientoModel.objects.filter(tipo="SALIDA_VENTA").exists()


def test_anular_venta_repone_lotes_y_permite_otra_venta():
    from src.modules.sales.application.use_cases.anular_venta import AnularVenta
    p = producto()
    lote = recibir(p, 2)
    venta = venta_guardada(p)
    cobrar(venta, 20)
    AnularVenta(construir_venta_repository(), construir_inventario_port(), construir_auditoria_port(),
                uow=transaction.atomic()).ejecutar(str(venta.venta.id), "Error", venta.venta.cajero_id)
    assert LoteModel.objects.get(pk=lote.id).cantidad_restante == 2
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 2
    assert cobrar(venta_guardada(p), 20)["estado"] == "PAGADA"


def test_salida_reservada_descuenta_lotes_y_no_se_confirma_dos_veces():
    from src.modules.orders.infrastructure.adapters.inventario_adapter import InventarioAdapter
    from src.modules.inventory.domain.exceptions.stock_exceptions import ReservaYaConfirmada
    p = producto()
    lote = recibir(p, 10)
    adapter = InventarioAdapter()
    reserva_id = adapter.reservar(str(p.id), 3, "PEDIDO:inventario")
    assert adapter.confirmar_reserva(reserva_id, "PEDIDO:inventario") == 7
    existencia = ExistenciaModel.objects.get(producto_id=p.id)
    assert existencia.reservada == 0 and existencia.cantidad == 7
    assert LoteModel.objects.get(pk=lote.id).cantidad_restante == 7
    with pytest.raises(ReservaYaConfirmada):
        adapter.confirmar_reserva(reserva_id, "PEDIDO:inventario")
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 7


def test_rf018_igualdad_no_alerta_cruce_notifica_tras_commit(django_capture_on_commit_callbacks):
    p = producto(stock_minimo=5)
    recibir(p, 6)
    with django_capture_on_commit_callbacks(execute=True):
        construir_inventario_port().descontar(str(p.id), 1, "VENTA:igual")
    assert not mail.outbox
    assert not construir_stock_repository().productos_bajo_minimo()
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        construir_inventario_port().descontar(str(p.id), 1, "VENTA:cruce")
        assert not mail.outbox
    assert len(callbacks) == 1 and len(mail.outbox) == 1
    assert str(p.id) in mail.outbox[0].body
    with django_capture_on_commit_callbacks(execute=True):
        construir_inventario_port().descontar(str(p.id), 1, "VENTA:ya-bajo")
    assert len(mail.outbox) == 1


def test_rf018_minimo_individual_incluye_productos_sin_existencia(almacen):
    alto, bajo, cero = producto(stock_minimo=12), producto(stock_minimo=1), producto(stock_minimo=0)
    recibir(alto, 10)
    recibir(bajo, 10)
    faltante = producto(nombre="Sin recepcion", stock_minimo=3)
    ids = {f["producto_id"] for f in construir_stock_repository().productos_bajo_minimo()}
    assert ids == {str(alto.id), str(faltante.id)}
    respuesta = almacen.get("/inventario/")
    assert len(respuesta.context["existencias"]) == 4
    assert b"Sin recepcion" in respuesta.content
    assert not ConsultarStock(construir_stock_repository()).ejecutar(str(cero.id)).bajo_minimo


def test_rf019_limites_vencimiento_y_lotes_agotados(almacen):
    p = producto()
    esperados = set()
    for dias in (-1, 0, 30, 31):
        lote = recibir(p, dias=dias)
        if dias in (0, 30):
            esperados.add(lote.numero_lote)
    agotado = recibir(p, dias=10)
    LoteModel.objects.filter(pk=agotado.id).update(cantidad_restante=0)
    respuesta = almacen.get("/inventario/alertas/")
    assert {l.numero_lote for l in respuesta.context["por_vencer"]} == esperados
    assert len(respuesta.context["vencidos"]) == 1
    assert p.nombre.encode() in respuesta.content


def test_rf019_vencimiento_del_producto_sin_lote(almacen):
    p = producto(fecha_vencimiento=date.today() + timedelta(days=30))
    respuesta = almacen.get("/inventario/alertas/")
    assert respuesta.context["por_vencer"][0]["producto_nombre"] == p.nombre


def test_rf020_recepcion_http_guarda_fecha_lote_stock_y_entrada(almacen):
    p = producto()
    datos = dict(producto_id=str(p.id), numero_lote="LOTE-HTTP", cantidad=15, costo_unitario="5",
                 fecha_vencimiento=(date.today() + timedelta(days=25)).isoformat())
    respuesta = almacen.post("/inventario/recepcion/", datos)
    assert respuesta.status_code == 302
    lote = LoteModel.objects.get(numero_lote="LOTE-HTTP")
    assert lote.fecha_vencimiento == date.fromisoformat(datos["fecha_vencimiento"])
    assert lote.cantidad_restante == ExistenciaModel.objects.get(producto_id=p.id).cantidad == 15
    movimiento = MovimientoModel.objects.get(producto_id=p.id)
    assert movimiento.tipo == "ENTRADA" and movimiento.lote_id == lote.id


@pytest.mark.parametrize("campo,valor", [("cantidad", 0), ("cantidad", -1), ("producto_id", "inexistente"),
                                         ("fecha_vencimiento", "invalida")])
def test_rf020_recepcion_invalida_no_persiste(almacen, campo, valor):
    p = producto()
    datos = dict(producto_id=str(p.id), numero_lote="L", cantidad=2, costo_unitario="5")
    datos[campo] = valor
    respuesta = almacen.post("/inventario/recepcion/", datos)
    assert respuesta.context["form"].errors
    assert not LoteModel.objects.exists() and not ExistenciaModel.objects.exists()


@pytest.mark.parametrize("motivo", ["VENCIDO", "DANADO", "ROBO"])
def test_rf021_merma_descuenta_lote_y_registra_motivo(almacen, motivo):
    p = producto()
    lote = recibir(p, dias=-1 if motivo == "VENCIDO" else 10)
    respuesta = almacen.post("/inventario/mermas/", dict(producto_id=p.id, lote_id=lote.id, cantidad=3, motivo=motivo))
    assert respuesta.status_code == 302
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 7
    assert LoteModel.objects.get(pk=lote.id).cantidad_restante == 7
    movimiento = MovimientoModel.objects.get(tipo="MERMA")
    assert movimiento.referencia == f"MERMA:{motivo}" and movimiento.lote_id == uuid.UUID(lote.id)


def test_rf021_merma_sin_lote_distribuye_entre_lotes_incluidos_vencidos(almacen):
    p = producto()
    vencido, vigente = recibir(p, 2, -1), recibir(p, 5, 10)
    assert almacen.post("/inventario/mermas/", dict(producto_id=p.id, cantidad=4, motivo="DANADO")).status_code == 302
    assert LoteModel.objects.get(pk=vencido.id).cantidad_restante == 0
    assert LoteModel.objects.get(pk=vigente.id).cantidad_restante == 3
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 3


@pytest.mark.parametrize("fallo", ["otro_lote", "exceso", "motivo", "cantidad"])
def test_rf021_merma_invalida_no_modifica_stock_ni_lotes(almacen, fallo):
    p, otro = producto(), producto()
    lote, otro_lote = recibir(p), recibir(otro)
    datos = dict(producto_id=p.id, lote_id=lote.id, cantidad=2, motivo="ROBO")
    if fallo == "otro_lote":
        datos["lote_id"] = otro_lote.id
    elif fallo == "exceso":
        datos["cantidad"] = 100
    elif fallo == "motivo":
        datos["motivo"] = "INVALIDO"
    else:
        datos["cantidad"] = 0
    respuesta = almacen.post("/inventario/mermas/", datos)
    assert respuesta.status_code == 200 and respuesta.context["form"].errors
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 10
    assert LoteModel.objects.get(pk=lote.id).cantidad_restante == 10
    assert not MovimientoModel.objects.filter(tipo="MERMA").exists()


def test_rf022_historial_paginado_completo_y_filtros(almacen):
    p = producto()
    for _ in range(52):
        recibir(p, 1)
    consulta = ConsultarKardex(construir_movimiento_repository())
    pagina = consulta.ejecutar(str(p.id))
    assert pagina.total == 52 and len(pagina.items) == 50 and pagina.tiene_siguiente
    assert len(consulta.ejecutar(str(p.id), pagina=2).items) == 2
    respuesta = almacen.get("/inventario/kardex/", {"producto_id": str(p.id), "pagina": 2,
                                                  "desde": date.today().isoformat()})
    assert respuesta.status_code == 200
    assert respuesta.context["pagina_dto"].total == 52
    assert str(p.id).encode() in respuesta.content
    assert b"desde=" in respuesta.content


@pytest.mark.parametrize("filtro", [{"pagina": "abc"}, {"pagina": "0"}, {"desde": "no-fecha"},
                                    {"desde": "2026-10-10", "hasta": "2026-01-01"}, {"producto_id": "abc"}])
def test_rf022_filtros_invalidos_muestran_error(almacen, filtro):
    p = producto()
    respuesta = almacen.get("/inventario/kardex/", {"producto_id": str(p.id), **filtro})
    assert respuesta.status_code == 200 and respuesta.context["form"].errors


def test_rf023_solo_ventas_pagadas_ventana_60_dias():
    recientes, limite, antigua, anulada, borrador, nunca = [producto() for _ in range(6)]
    for p, dias, estado in [(recientes, 59, "PAGADA"), (limite, 60, "PAGADA"),
                            (antigua, 61, "PAGADA"), (anulada, 1, "ANULADA"), (borrador, 1, "BORRADOR")]:
        venta = venta_guardada(p)
        VentaModel.objects.filter(pk=venta.venta.id).update(estado=estado, fecha_creacion=timezone.now() - timedelta(days=dias))
    ids = {f["producto_id"] for f in ReporteBajaRotacion(construir_reporte_repository()).ejecutar()}
    assert ids == {str(p.id) for p in (antigua, anulada, borrador, nunca)}


def test_rf024_orden_por_margen_y_no_por_ingresos(almacen):
    producto(nombre="Bajo margen", costo=Decimal("100"), precio_venta=Decimal("120"))
    producto(nombre="Alto margen", costo=Decimal("2"), precio_venta=Decimal("8"))
    producto(nombre="Costo cero", costo=Decimal("0"), precio_venta=Decimal("5"))
    producto(nombre="Inactivo", activo=False)
    respuesta = almacen.get("/reportes/inventario/")
    filas = respuesta.context["mayor_ganancia"]
    assert [f["producto_nombre"] for f in filas] == ["Alto margen", "Costo cero", "Bajo margen"]
    assert filas[0]["margen_pct"] == Decimal("300.00")
    assert filas[0]["ganancia_unitaria"] == Decimal("6")


def test_ranking_existente_del_dashboard_sigue_funcionando(almacen):
    sesion = almacen.session
    sesion["rol"] = "ADMINISTRADOR"
    sesion.save()
    assert almacen.get("/reportes/").status_code == 200


@pytest.mark.parametrize("ruta", ["/inventario/", "/inventario/recepcion/", "/inventario/mermas/",
                                  "/inventario/kardex/", "/inventario/alertas/", "/reportes/inventario/",
                                  "/catalogo/productos/nuevo/"])
def test_sin_permiso_no_se_accede_al_modulo(almacen, ruta):
    session = almacen.session
    session["rol"] = "CLIENTE"
    session.save()
    assert almacen.get(ruta).status_code == 302
    almacen.logout()
    assert almacen.get(ruta).status_code == 302
