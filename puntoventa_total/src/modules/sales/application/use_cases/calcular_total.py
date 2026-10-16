from src.modules.sales.application.dto.venta_output import VentaOutputDTO
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.modules.sales.domain.services.calculadora_venta import CalculadoraVenta


class CalcularTotal:
    def __init__(self, repo: VentaRepository):
        self._repo = repo

    def ejecutar(self, venta_id: str) -> dict:
        agregado = self._repo.buscar_por_id(venta_id)
        if agregado is None:
            from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada

            raise VentaNoEncontrada(venta_id)
        totales = agregado.calcular_totales()
        totales.update({"numero_ticket": agregado.venta.numero_ticket})
        return totales

    def desglose(self, venta_id: str) -> dict:
        agregado = self._repo.buscar_por_id(venta_id)
        from src.shared.domain.value_objects.monto import Monto

        return CalculadoraVenta.desglose_igv(Monto(agregado.venta.total, agregado.venta.moneda))

