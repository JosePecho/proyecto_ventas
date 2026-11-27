"""Los identificadores de registros deben ser reconocibles en listados de administracion."""
from importlib import import_module

import pytest

pytestmark = pytest.mark.unit

MODELOS = [
    ("auditing", "auditoria", "Auditoria", "entidad_id"),
    ("cash_register", "turno_caja", "TurnoCaja", "estado"),
    ("cash_register", "movimiento_caja", "MovimientoCaja", "tipo"),
    ("catalog", "categoria", "Categoria", "nombre"),
    ("catalog", "producto", "Producto", "nombre"),
    ("customers", "cliente", "Cliente", "nombre"),
    ("identity", "usuario", "Usuario", "username"),
    ("inventory", "existencia", "Existencia", "producto_id"),
    ("inventory", "lote", "Lote", "numero_lote"),
    ("inventory", "movimiento", "Movimiento", "tipo"),
    ("inventory", "reserva", "Reserva", "referencia"),
    ("orders", "pedido", "Pedido", "numero"),
    ("orders", "detalle_pedido", "DetallePedido", "producto_nombre"),
    ("promotions", "promocion", "Promocion", "nombre"),
    ("sales", "venta", "Venta", "numero_ticket"),
    ("sales", "detalle_venta", "DetalleVenta", "producto_nombre"),
    ("sales", "pago", "Pago", "metodo"),
]


@pytest.mark.parametrize("modulo,archivo,nombre,campo", MODELOS, ids=[c[2] for c in MODELOS])
@pytest.mark.parametrize("identificador", ["registro-1", "registro-ñ-2"])
def test_etiqueta_modelo_identifica_registro_sin_consultar_bd(modulo, archivo, nombre, campo, identificador):
    modulo_python = import_module(f"src.modules.{modulo}.infrastructure.persistence.django_models.{archivo}_model")
    modelo = getattr(modulo_python, nombre + "Model")(**{campo: identificador})
    assert identificador in str(modelo)

