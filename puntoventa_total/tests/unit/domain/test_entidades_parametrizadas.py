"""Contratos compartidos y fronteras de las entidades de todos los modulos."""
from datetime import UTC, datetime
from decimal import Decimal
from importlib import import_module

import pytest

from src.modules.catalog.domain.value_objects.precio import Precio
from src.modules.sales.domain.value_objects.metodo_pago import MetodoPago
from src.shared.domain.events.domain_event import DomainEvent
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit

# Datos explicitos: no se omiten clases con constructores que exigen argumentos.
ENTIDADES = [
    ("shared.domain.entities.base_entity.BaseEntity", {}),
    ("modules.catalog.domain.entities.categoria.Categoria", {"nombre": "Bebidas"}),
    ("modules.catalog.domain.entities.producto.Producto", {
        "nombre": "Agua", "codigo_barras": "12345678",
        "precio": Precio(Monto(5), Monto(10)),
    }),
    ("modules.customers.domain.entities.cliente.Cliente", {"nombre": "Ana"}),
    ("modules.identity.domain.entities.usuario.Usuario", {"username": "ana1", "nombre_completo": "Ana"}),
    ("modules.inventory.domain.entities.existencia.Existencia", {"producto_id": "p1"}),
    ("modules.inventory.domain.entities.lote.Lote", {
        "producto_id": "p1", "numero_lote": "L1", "cantidad_inicial": 10, "cantidad_restante": 10,
    }),
    ("modules.inventory.domain.entities.movimiento_stock.MovimientoStock", {
        "producto_id": "p1", "cantidad": 1, "stock_resultante": 1,
    }),
    ("modules.inventory.domain.entities.reserva_stock.ReservaStock", {"producto_id": "p1", "cantidad": 1}),
    ("modules.orders.domain.entities.pedido.Pedido", {"cliente_nombre": "Ana"}),
    ("modules.orders.domain.entities.detalle_pedido.DetallePedido", {
        "producto_id": "p1", "producto_nombre": "Agua", "precio_unitario": Monto(10),
    }),
    ("modules.promotions.domain.entities.promocion.Promocion", {"nombre": "Oferta"}),
    ("modules.sales.domain.entities.venta.Venta", {}),
    ("modules.sales.domain.entities.detalle_venta.DetalleVenta", {
        "producto_id": "p1", "producto_nombre": "Agua", "precio_unitario": Monto(10),
    }),
    ("modules.sales.domain.entities.pago.Pago", {"metodo": MetodoPago("EFECTIVO", Monto(10))}),
    ("modules.cash_register.domain.entities.turno_caja.TurnoCaja", {
        "cajero_id": "c1", "monto_apertura": Monto(100),
    }),
    ("modules.cash_register.domain.entities.movimiento_caja.MovimientoCaja", {
        "turno_id": "t1", "monto": Monto(10),
    }),
]


def construir(ruta, datos):
    modulo, nombre = ("src." + ruta).rsplit(".", 1)
    return getattr(import_module(modulo), nombre)(**datos)


@pytest.fixture(params=ENTIDADES, ids=lambda caso: caso[0].rsplit(".", 1)[1])
def entidad(request):
    return construir(*request.param)


@pytest.mark.parametrize("cantidad", [0, 1, 3])
def test_eventos_aislados_y_limpieza(entidad, cantidad):
    eventos = [DomainEvent(entidad=str(entidad.id)) for _ in range(cantidad)]
    for evento in eventos:
        entidad._publicar(evento)
    copia = entidad.eventos_pendientes()
    assert copia == eventos
    copia.clear()
    assert entidad.eventos_pendientes() == eventos
    entidad.limpiar_eventos()
    assert entidad.eventos_pendientes() == []


@pytest.mark.parametrize("ruta,datos", ENTIDADES, ids=[c[0].rsplit(".", 1)[1] for c in ENTIDADES])
def test_identidad_y_eventos_no_se_comparten(ruta, datos):
    primera, segunda = construir(ruta, datos), construir(ruta, datos)
    assert primera.id != segunda.id
    primera._publicar(DomainEvent())
    assert segunda.eventos_pendientes() == []


@pytest.mark.parametrize("activo", [False, True])
def test_actualizacion_preserva_identidad_y_creacion(entidad, activo, monkeypatch):
    instante = datetime(2030, 1, 1, tzinfo=UTC)
    monkeypatch.setattr("src.shared.domain.entities.base_entity.utc_now", lambda: instante)
    identidad, creacion = entidad.id, entidad.fecha_creacion
    entidad.activo = activo
    entidad.marcar_actualizado()
    assert entidad.id == identidad
    assert entidad.fecha_creacion == creacion
    assert entidad.fecha_actualizacion == instante
    assert entidad.activo is activo


@pytest.mark.parametrize("ruta,datos,campo", [
    (ruta, datos, campo)
    for ruta, datos in ENTIDADES
    for campo in ("nombre", "username", "nombre_completo", "producto_id", "producto_nombre", "cliente_nombre", "numero_lote", "cajero_id", "turno_id")
    if campo in datos
])
@pytest.mark.parametrize("invalido", [None, "", "   "])
def test_campos_obligatorios(ruta, datos, campo, invalido):
    with pytest.raises(ValidationException):
        construir(ruta, {**datos, campo: invalido})


@pytest.mark.parametrize("clase", ["pedido", "venta"])
@pytest.mark.parametrize("cantidad", [1, 2, 100])
@pytest.mark.parametrize("precio", ["0.01", "9.99", "100.00"])
def test_detalles_recalculan_subtotal(clase, cantidad, precio):
    ruta = f"modules.{'orders' if clase == 'pedido' else 'sales'}.domain.entities.detalle_{clase}.Detalle{clase.title()}"
    detalle = construir(ruta, {"producto_id": "p1", "producto_nombre": "Agua", "precio_unitario": Monto(precio)})
    detalle.cambiar_cantidad(cantidad)
    assert detalle.subtotal == Monto(Decimal(precio) * cantidad)


@pytest.mark.parametrize("clase", ["pedido", "venta"])
@pytest.mark.parametrize("cantidad", [0, -1, -100])
def test_detalle_rechaza_cantidad_sin_mutar(clase, cantidad):
    ruta = f"modules.{'orders' if clase == 'pedido' else 'sales'}.domain.entities.detalle_{clase}.Detalle{clase.title()}"
    detalle = construir(ruta, {"producto_id": "p1", "producto_nombre": "Agua", "precio_unitario": Monto(10)})
    with pytest.raises(ValidationException):
        detalle.cambiar_cantidad(cantidad)
    assert detalle.cantidad == 1
    assert detalle.subtotal == Monto(10)


@pytest.mark.parametrize("intentos,bloqueado", [(0, False), (1, False), (4, False), (5, True), (6, True)])
def test_usuario_bloqueo_e_intentos(intentos, bloqueado):
    from src.modules.identity.domain.entities.usuario import Usuario
    from src.modules.identity.domain.enums.estado_usuario import EstadoUsuario

    usuario = Usuario(username="ana1", nombre_completo="Ana")
    for _ in range(intentos):
        usuario.registrar_intentofallido()
    assert usuario.intentos_fallidos == intentos
    assert (usuario.estado == EstadoUsuario.BLOQUEADO) is bloqueado
    assert usuario.puede_autenticarse() is (not bloqueado)


@pytest.mark.parametrize("saldo,canje,restante", [(0, 1, None), (10, 0, None), (10, -1, None), (10, 11, None), (10, 10, 0), (10, 1, 9)])
def test_cliente_canje_de_puntos(saldo, canje, restante):
    from src.modules.customers.domain.entities.cliente import Cliente

    cliente = Cliente(nombre="Ana", puntos_fidelidad=saldo)
    if restante is None:
        with pytest.raises(ValidationException):
            cliente.canjear_puntos(canje)
        assert cliente.puntos_fidelidad == saldo
    else:
        cliente.canjear_puntos(canje)
        assert cliente.puntos_fidelidad == restante


@pytest.mark.parametrize("tipo,ingreso,egreso", [
    ("VENTA", True, False), ("DEPOSITO", True, False),
    ("RETIRO", False, True), ("NOTA_CREDITO", False, True),
    ("ARQUEO_DIFERENCIA", False, False),
])
def test_clasificacion_movimientos_caja(tipo, ingreso, egreso):
    from src.modules.cash_register.domain.entities.movimiento_caja import MovimientoCaja

    movimiento = MovimientoCaja(turno_id="t1", tipo=tipo, monto=Monto(10))
    assert movimiento.es_ingreso is ingreso
    assert movimiento.es_egreso is egreso


@pytest.mark.parametrize("tipo,signo", [
    ("ENTRADA", 1), ("AJUSTE_POSITIVO", 1), ("DEVOLUCION", 1),
    ("SALIDA_VENTA", -1), ("SALIDA_PEDIDO", -1), ("AJUSTE_NEGATIVO", -1), ("MERMA", -1),
])
def test_signo_kardex(tipo, signo):
    from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock

    movimiento = MovimientoStock(producto_id="p1", tipo=tipo, cantidad=1, stock_resultante=10)
    assert movimiento.signo() == signo
    assert movimiento.es_entrada() is (signo == 1)


@pytest.mark.parametrize("accion", ["CREAR", "ACTUALIZAR", "ELIMINAR", "VENTA_PAGADA", "LOGIN_FALLIDO"])
@pytest.mark.parametrize("detalle", [{}, {"nombre": "María", "cantidad": 2}])
def test_auditoria_conserva_detalle_inmutable(accion, detalle):
    import json
    from dataclasses import FrozenInstanceError

    from src.modules.auditing.domain.entities.registro_auditoria import RegistroAuditoria

    registro = RegistroAuditoria.crear(accion, "Producto", "p1", detalle=detalle)
    assert json.loads(registro.detalle_json()) == detalle
    with pytest.raises(FrozenInstanceError):
        registro.accion = "ELIMINAR"
