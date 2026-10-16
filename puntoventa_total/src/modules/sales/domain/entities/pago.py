from dataclasses import dataclass

from src.modules.sales.domain.value_objects.metodo_pago import MetodoPago
from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.value_objects.monto import Monto


@dataclass
class Pago(BaseEntity):
    venta_id: str = ""
    metodo: MetodoPago = None
    vuelto: Monto = None

    def __post_init__(self) -> None:
        if self.metodo is None:
            raise TypeError("Pago requiere un MetodoPago")

    @classmethod
    def efectivo(cls, venta_id: str, monto: Monto, monto_entregado: Monto | None = None) -> "Pago":
        metodo = MetodoPago(tipo="EFECTIVO", monto=monto)
        vuelto = None
        if monto_entregado:
            vuelto = CalculadoraVenta.vuelto(monto, monto_entregado)
        return cls(venta_id=venta_id, metodo=metodo, vuelto=vuelto)

    @property
    def monto(self) -> Monto:
        return self.metodo.monto

from src.modules.sales.domain.services.calculadora_venta import CalculadoraVenta  # noqa: E402

