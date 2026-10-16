"""Reproduce riesgos de dominio detectados; no modifica BD ni codigo.

Exit 1 = hay hallazgos reproducidos. No es una prueba de aceptacion aprobada.
"""
from datetime import datetime, timezone
import json
from unittest.mock import Mock

from src.modules.inventory.application.use_cases.liberar_reserva import LiberarReserva
from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.entities.reserva_stock import ReservaStock
from src.modules.inventory.domain.exceptions.stock_exceptions import StockException
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.modules.inventory.domain.repositories.reserva_repository import ReservaRepository


def main():
    existencia = Existencia(producto_id="p1", cantidad=10, reservada=2)
    reserva = ReservaStock(producto_id="p1", cantidad=3, liberada=True)
    stock, reservas = Mock(spec=StockRepository), Mock(spec=ReservaRepository)
    stock.obtener.return_value = existencia
    reservas.buscar_por_id.return_value = reserva
    LiberarReserva(stock, reservas).ejecutar("reserva_ya_liberada")
    resultados = {
        "QA-INV-01": {"descripcion": "Liberar dos veces puede consumir la reserva de otro pedido",
                      "reservada_esperada": 2, "reservada_observada": existencia.reservada,
                      "reproducido": existencia.reservada != 2},
    }
    r = ReservaStock(producto_id="p1", cantidad=1, expira_en=datetime.now(timezone.utc))
    try:
        r.expirada
    except TypeError:
        resultados["QA-INV-02"] = {"descripcion": "Expiracion mezcla datetime naive y aware", "reproducido": True}
    else:
        resultados["QA-INV-02"] = {"reproducido": False}
    e = Existencia(producto_id="p1")
    try:
        e.aplicar_entrada(0.5)
    except StockException:
        fraccion_aceptada = False
    else:
        fraccion_aceptada = e.cantidad == 0.5
    resultados["QA-INV-03"] = {"descripcion": "El dominio admite cantidad fraccionaria pese al contrato entero",
                               "reproducido": fraccion_aceptada}
    print(json.dumps(resultados, ensure_ascii=False, indent=2))
    return int(any(r["reproducido"] for r in resultados.values()))


if __name__ == "__main__":
    raise SystemExit(main())
