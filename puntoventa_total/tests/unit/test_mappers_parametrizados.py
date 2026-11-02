"""Persistencia sin conexion: precision, identificadores y actualizacion en sitio."""
from datetime import date
from decimal import Decimal
from importlib import import_module
from uuid import UUID

import pytest

from src.modules.catalog.domain.value_objects.precio import Precio
from src.modules.promotions.domain.value_objects.descuento import Descuento
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit
ID = "12345678-1234-5678-1234-567812345678"


def cargar(ruta):
    modulo, nombre = ruta.rsplit(".", 1)
    return getattr(import_module("src.modules." + modulo), nombre)


CASOS = [
    ("catalog", "categoria", "Categoria", {"nombre": "Bebidas", "descripcion": "Sin azúcar", "orden": 2}, ["nombre", "slug", "descripcion", "orden", "activo"]),
    ("catalog", "producto", "Producto", {
        "nombre": "Agua", "descripcion": "Sin gas", "codigo_barras": "12345678",
        "precio": Precio(Monto("5.01"), Monto("9.99")), "stock_minimo": 0,
        "fecha_vencimiento": date(2030, 1, 1), "categoria_id": ID,
    }, ["nombre", "descripcion", "codigo_barras", "precio", "stock_minimo", "fecha_vencimiento", "categoria_id", "activo"]),
    ("customers", "cliente", "Cliente", {
        "nombre": "María", "dni": "00123456", "email": "ana@example.test",
        "telefono": "987654321", "direccion": "Local 1", "puntos_fidelidad": 10, "usuario_id": ID,
    }, ["nombre", "dni", "email", "telefono", "direccion", "puntos_fidelidad", "usuario_id", "activo"]),
    ("identity", "usuario", "Usuario", {
        "username": "ana1", "nombre_completo": "Ana Pérez", "password_hash": "hash-no-real",
        "email": "ana@example.test", "intentos_fallidos": 4,
    }, ["username", "nombre_completo", "password_hash", "email", "rol", "estado", "intentos_fallidos", "activo"]),
    ("inventory", "lote", "Lote", {
        "producto_id": ID, "numero_lote": "L1", "cantidad_inicial": 10, "cantidad_restante": 7,
        "costo_unitario": Monto("5.01"), "proveedor": "Proveedor 1", "fecha_vencimiento": date(2030, 1, 1),
    }, ["producto_id", "numero_lote", "cantidad_inicial", "cantidad_restante", "costo_unitario", "proveedor", "fecha_vencimiento", "fecha_recepcion", "activo"]),
    ("promotions", "promocion", "Promocion", {
        "nombre": "Oferta", "tipo": "PORCENTAJE", "descuento": Descuento.porcentaje(Decimal("12.50"), Decimal("5.01")),
        "producto_id": ID,
    }, ["nombre", "tipo", "estado", "descuento", "producto_id", "activo"]),
]


@pytest.mark.parametrize("caso", CASOS, ids=[c[2] for c in CASOS])
@pytest.mark.parametrize("activo", [False, True])
@pytest.mark.parametrize("existente", [False, True])
def test_conversion_ida_y_vuelta(caso, activo, existente):
    modulo, archivo, nombre, datos, campos = caso
    entidad = cargar(f"{modulo}.domain.entities.{archivo}.{nombre}")(**datos, activo=activo)
    mapper = cargar(f"{modulo}.infrastructure.persistence.mappers.{archivo}_mapper.{nombre}Mapper")
    modelo_cls = cargar(f"{modulo}.infrastructure.persistence.django_models.{archivo}_model.{nombre}Model")
    anterior = modelo_cls(id=entidad.id) if existente else None

    modelo = mapper.a_modelo(entidad, anterior)
    if existente:
        assert modelo is anterior
    assert isinstance(modelo.id, UUID)
    recuperada = mapper.a_dominio(modelo)
    assert recuperada.id == entidad.id
    for campo in campos:
        assert getattr(recuperada, campo) == getattr(entidad, campo), campo


@pytest.mark.parametrize("cierre", [None, "0.00", "110.01"])
def test_turno_mapper_preserva_cero_y_nulos(cierre):
    from src.modules.cash_register.domain.entities.turno_caja import TurnoCaja
    from src.modules.cash_register.infrastructure.persistence.mappers.turno_mapper import TurnoMapper

    turno = TurnoCaja(cajero_id=ID, monto_apertura=Monto("100.01"), monto_cierre=Monto(cierre) if cierre is not None else None)
    recuperado = TurnoMapper.turno_a_dominio(TurnoMapper.turno_a_modelo(turno))
    assert recuperado.cajero_id == ID
    assert recuperado.monto_apertura == Monto("100.01")
    assert recuperado.monto_cierre == turno.monto_cierre


@pytest.mark.parametrize("detalle,esperado", [({"cantidad": 2}, {"cantidad": 2}), ('{"cantidad": 2}', {"cantidad": 2}), ("no-json", {"crudo": "no-json"})])
def test_auditoria_mapper_lee_detalle_estructurado_o_historico(detalle, esperado):
    from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
    from src.modules.auditing.infrastructure.persistence.mappers.auditoria_mapper import AuditoriaMapper

    modelo = AuditoriaModel(accion="CREAR", entidad="Producto", entidad_id=ID, detalle=detalle)
    entidad = AuditoriaMapper.a_dominio(modelo)
    assert entidad.detalle == esperado
    assert entidad.entidad_id == ID


@pytest.mark.parametrize("tipo", ["ENTRADA", "SALIDA_VENTA"])
@pytest.mark.parametrize("cantidad", [1, 3])
def test_movimiento_mapper_y_dto_conservan_trazabilidad(tipo, cantidad):
    from src.modules.inventory.application.dto.movimiento_dto import MovimientoDTO
    from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock
    from src.modules.inventory.infrastructure.persistence.mappers.movimiento_mapper import MovimientoMapper

    movimiento = MovimientoStock(producto_id=ID, tipo=tipo, cantidad=cantidad, stock_resultante=10,
                                 referencia="VENTA:T1", usuario_id=ID)
    recuperado = MovimientoMapper.a_dominio(MovimientoMapper.a_modelo(movimiento))
    dto = MovimientoDTO.desde_entidad(recuperado)
    assert dto.producto_id == ID
    assert dto.cantidad == cantidad
    assert dto.tipo == tipo
    assert dto.referencia == "VENTA:T1"
