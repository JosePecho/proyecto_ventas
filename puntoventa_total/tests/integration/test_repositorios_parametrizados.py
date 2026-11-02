"""Contratos de persistencia con BD de pruebas aislada de pytest-django."""
from importlib import import_module
from uuid import uuid4

import pytest

from src.modules.auditing.domain.entities.registro_auditoria import RegistroAuditoria
from src.modules.cash_register.domain.entities.turno_caja import TurnoCaja
from src.modules.catalog.domain.entities.categoria import Categoria
from src.modules.catalog.domain.entities.producto import Producto
from src.modules.catalog.domain.value_objects.precio import Precio
from src.modules.customers.domain.entities.cliente import Cliente
from src.modules.identity.domain.entities.usuario import Usuario
from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.entities.lote import Lote
from src.modules.inventory.domain.entities.reserva_stock import ReservaStock
from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate
from src.modules.orders.domain.entities.pedido import Pedido
from src.modules.promotions.domain.entities.promocion import Promocion
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def producto():
    return Producto(nombre="Agua", codigo_barras="12345678", precio=Precio(Monto("5.01"), Monto("9.99")))


CASOS = [
    ("catalog", "categoria", "Categoria", lambda: Categoria(nombre="Categoria parametrizada", slug="categoria-parametrizada"), "buscar_por_id", "nombre", "orden", 3),
    ("catalog", "producto", "Producto", producto, "buscar_por_id", "nombre", "stock_minimo", 0),
    ("customers", "cliente", "Cliente", lambda: Cliente(nombre="Ana", dni="00123456"), "buscar_por_id", "nombre", "puntos_fidelidad", 25),
    ("identity", "usuario", "Usuario", lambda: Usuario(username="ana1", nombre_completo="Ana"), "buscar_por_id", "username", "intentos_fallidos", 4),
    ("promotions", "promocion", "Promocion", lambda: Promocion(nombre="Oferta"), "buscar_por_id", "nombre", "nombre", "Oferta actualizada"),
    ("cash_register", "turno", "Turno", lambda: TurnoCaja(cajero_id=str(uuid4()), monto_apertura=Monto("100.01")), "buscar_por_id", "cajero_id", "observaciones", "Revisado"),
    ("inventory", "lote", "Lote", lambda: Lote(producto_id=str(uuid4()), numero_lote="L1", cantidad_inicial=10, cantidad_restante=10), "buscar_por_id", "numero_lote", "cantidad_restante", 7),
    ("inventory", "reserva", "Reserva", lambda: ReservaStock(producto_id=str(uuid4()), cantidad=2), "buscar_por_id", "cantidad", "liberada", True),
    ("inventory", "stock", "Stock", lambda: Existencia(producto_id=str(uuid4()), cantidad=10), "obtener", "cantidad", "reservada", 3),
]


def repositorio(modulo, archivo, nombre):
    ruta = f"src.modules.{modulo}.infrastructure.persistence.repositories.django_{archivo}_repository"
    return getattr(import_module(ruta), f"Django{nombre}Repository")()


@pytest.mark.parametrize("caso", CASOS, ids=[f"{c[0]}.{c[2]}" for c in CASOS])
@pytest.mark.parametrize("actualizar", [False, True])
def test_guardar_recuperar_y_actualizar(caso, actualizar):
    modulo, archivo, nombre, crear, consulta, campo, cambio, valor = caso
    repo, entidad = repositorio(modulo, archivo, nombre), crear()
    repo.guardar(entidad)
    if actualizar:
        setattr(entidad, cambio, valor)
        repo.guardar(entidad)
    clave = entidad.producto_id if archivo == "stock" else entidad.id
    recuperada = getattr(repo, consulta)(clave)
    assert recuperada is not None
    assert getattr(recuperada, campo) == getattr(entidad, campo)
    assert getattr(recuperada, cambio) == getattr(entidad, cambio)
    if archivo != "stock":
        assert recuperada.id == entidad.id


@pytest.mark.parametrize("caso", CASOS, ids=[f"{c[0]}.{c[2]}" for c in CASOS])
@pytest.mark.parametrize("identificador", ["00000000-0000-0000-0000-000000000000", "11111111-1111-1111-1111-111111111111"])
def test_busqueda_inexistente_devuelve_none(caso, identificador):
    modulo, archivo, nombre, _, consulta, *_ = caso
    assert getattr(repositorio(modulo, archivo, nombre), consulta)(identificador) is None


@pytest.mark.parametrize("clase", ["venta", "pedido"])
@pytest.mark.parametrize("cantidad", [1, 2, 100])
def test_agregados_preservan_lineas_y_decimales(clase, cantidad):
    if clase == "venta":
        repo = repositorio("sales", "venta", "Venta")
        agregado = VentaAggregate(Venta(numero_ticket="T-PARAM-1", cajero_id=str(uuid4())))
    else:
        repo = repositorio("orders", "pedido", "Pedido")
        agregado = PedidoAggregate(Pedido(numero="P-PARAM-1", cliente_nombre="Ana"))
    producto_id = str(uuid4())
    agregado.agregar_producto(producto_id, "Agua", cantidad, Monto("9.99"))
    repo.guardar(agregado)
    entidad = agregado.venta if clase == "venta" else agregado.pedido
    recuperado = repo.buscar_por_id(entidad.id)
    assert len(recuperado.lineas) == 1
    linea = recuperado.lineas[0]
    assert linea.producto_id == producto_id
    assert linea.cantidad == cantidad
    assert linea.precio_unitario == Monto("9.99")
    assert linea.subtotal == Monto("9.99") * cantidad


@pytest.mark.parametrize("accion", ["CREAR", "ACTUALIZAR", "ELIMINAR"])
@pytest.mark.parametrize("detalle", [{}, {"nombre": "María", "cantidad": 2}])
def test_auditoria_persistida_conserva_detalle(accion, detalle):
    repo = repositorio("auditing", "auditoria", "Auditoria")
    registro = RegistroAuditoria.crear(accion, "Producto", str(uuid4()), detalle=detalle)
    repo.guardar(registro)
    recuperado = repo.buscar_por_id(registro.id)
    assert recuperado.accion == accion
    assert recuperado.detalle == detalle
    assert recuperado.entidad_id == registro.entidad_id
