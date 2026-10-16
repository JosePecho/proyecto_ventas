"""Puerto de consultas agregadas (la capa de dominio no ve SQL)."""
from abc import ABC, abstractmethod
from datetime import date
from typing import Sequence


class ReporteRepository(ABC):
    @abstractmethod
    def ventas_por_dia(self, desde: date, hasta: date) -> Sequence[dict]:
        """[{fecha, cantidad, total, igv}, ...]"""
        ...

    @abstractmethod
    def productos_mas_vendidos(self, desde: date, hasta: date, limite: int = 10) -> Sequence[dict]:
        """[{producto_id, producto_nombre, unidades, ingresos}, ...]"""
        ...

    @abstractmethod
    def utilidad_por_producto(self, desde: date, hasta: date) -> Sequence[dict]:
        """[{producto_id, producto_nombre, ingresos, costo, utilidad}, ...]"""
        ...

    @abstractmethod
    def rotacion_inventario(self, desde: date, hasta: date, dias_umbral: int = 90) -> Sequence[dict]:
        """Productos sin movimiento en el umbral dado."""
        ...

    @abstractmethod
    def resumen_stock(self) -> Sequence[dict]:
        """[{producto_id, producto_nombre, disponible}, ...]"""
        ...

    @abstractmethod
    def totales_por_metodo_pago(self, desde: date, hasta: date) -> dict:
        ...

