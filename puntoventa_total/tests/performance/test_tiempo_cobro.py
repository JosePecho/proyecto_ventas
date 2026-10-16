import time
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.performance


def test_cobro_en_menos_de_100ms():
    agregado = VentaAggregate(venta=Venta(numero_ticket="TPERF", cajero_id="c"))
    agregado.agregar_producto("p1", "Item", 1, Monto(Decimal("10.00")))

    repo = MagicMock()
    repo.buscar_por_id.return_value = agregado

    caso = ProcesarPago(repo, MagicMock(), MagicMock())
    inicio = time.perf_counter()
    caso.ejecutar(ProcesarPagoDTO(venta_id="v", metodo="EFECTIVO", monto=10.0))
    duracion = time.perf_counter() - inicio
    assert duracion < 0.1, f"El cobro tomo {duracion:.3f}s (max 100ms)"

