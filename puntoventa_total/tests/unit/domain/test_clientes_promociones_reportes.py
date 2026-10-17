from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import given, settings, strategies as st

from src.modules.customers.domain.services.frecuencia_compra import FrecuenciaCompra
from src.modules.promotions.domain.entities.promocion import Promocion
from src.modules.promotions.domain.value_objects.descuento import Descuento
from src.modules.sales.domain.entities.detalle_venta import DetalleVenta
from src.modules.reporting.domain.value_objects.utilidad_historica import agrupar_utilidad
from src.shared.domain.value_objects.monto import Monto
from src.shared.domain.exceptions.domain_exception import DomainException

pytestmark = pytest.mark.unit


def test_compras_del_mismo_dia_son_recurrentes():
    ahora = datetime.now(timezone.utc)
    dias = FrecuenciaCompra.dias_entre_compras([ahora, ahora])
    assert FrecuenciaCompra.clasificar(dias) == "FRECUENTE"
    assert FrecuenciaCompra.clasificar(FrecuenciaCompra.dias_entre_compras([ahora])) == "SIN_DATOS"


@pytest.mark.parametrize("dias,esperado", [(7, "FRECUENTE"), (7.01, "OCASIONAL"), (30, "OCASIONAL")])
def test_fronteras_fidelizacion(dias, esperado):
    assert FrecuenciaCompra.clasificar(dias) == esperado


def test_combo_requiere_todos_los_productos_y_precio_congelado():
    a, b = str(uuid4()), str(uuid4())
    promo = Promocion(nombre="Combo desayuno", tipo="COMBO", estado="ACTIVA",
        descuento=Descuento(Decimal("12"), "COMBO"),
        componentes=[{"producto_id": a, "cantidad": 1}, {"producto_id": b, "cantidad": 1}])
    pan = DetalleVenta(producto_id=a, producto_nombre="Pan", cantidad=3, precio_unitario=Monto(10))
    jugo = DetalleVenta(producto_id=b, producto_nombre="Jugo", cantidad=2, precio_unitario=Monto(5))
    assert promo.descuento_combo([pan, jugo]).valor == Decimal("6")
    assert promo.descuento_combo([pan]).valor == 0


@pytest.mark.parametrize("componentes", [[], [{"producto_id": "no-uuid", "cantidad": 1}], ["malformado"]])
def test_combo_invalido_no_se_construye(componentes):
    with pytest.raises(DomainException):
        Promocion(nombre="Combo", tipo="COMBO", componentes=componentes)


def test_promocion_no_vigente_en_instante_final():
    fin = datetime.now(timezone.utc)
    promo = Promocion(nombre="10%", estado="ACTIVA", vigencia_hasta=fin)
    assert not promo.esta_vigente(fin)


@given(st.integers(min_value=1, max_value=10000), st.integers(min_value=0, max_value=100), st.integers(min_value=2, max_value=20))
@settings(derandomize=True, deadline=None)
def test_utilidad_conserva_total_de_venta_al_distribuir_centavos(centavos, descuento, cantidad):
    base = Decimal(centavos) / 100
    total = (base * (100 - descuento) / 100).quantize(Decimal("0.01"))
    lineas = [{"venta_id": "v1", "producto_id": str(i), "producto_nombre": f"Pan {i}",
               "cantidad": 1, "importe": base / cantidad, "total_venta": total, "costo_unitario": Decimal("0.1")}
              for i in range(cantidad)]
    filas = agrupar_utilidad(lineas)
    assert sum(Decimal(str(f["ingresos"])) for f in filas) == total
    assert all(f["ingresos"] >= 0 for f in filas)


def test_utilidad_antigua_declara_costo_desconocido():
    filas = agrupar_utilidad([{"venta_id": "v", "producto_id": "pan", "producto_nombre": "Pan",
        "cantidad": 1, "importe": 10, "total_venta": 10, "costo_unitario": None}])
    assert filas[0]["estimado"] is True
