from decimal import Decimal

from src.modules.sales.application.dto.venta_output import VentaOutputDTO
from src.modules.sales.application.ports.promociones_port import PromocionesPort
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.shared.domain.exceptions.validation_exception import ValidationException


class AplicarPromocion:
    def __init__(self, repo: VentaRepository, promociones: PromocionesPort):
        self._repo = repo
        self._promociones = promociones

    def ejecutar(self, venta_id: str, pct_descuento: Decimal | None = None) -> VentaOutputDTO:
        agregado = self._repo.buscar_por_id(venta_id)
        if agregado is None:
            from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada

            raise VentaNoEncontrada(venta_id)

        if pct_descuento is not None:
            agregado.aplicar_descuento_venta(pct_descuento)
        else:
            sugerido = self._promociones.descuento_venta(
                venta_id, Monto(agregado.venta.subtotal, agregado.venta.moneda), agregado.venta.cliente_id
            )
            if sugerido.valor <= 0:
                raise ValidationException("No hay promociones aplicables a esta venta")
            pct = (sugerido.valor / Decimal(str(agregado.venta.subtotal)) * Decimal("100")).quantize(Decimal("0.01"))
            agregado.aplicar_descuento_venta(pct)

        agregado.calcular_totales()
        self._repo.guardar(agregado)
        return VentaOutputDTO.desde_agregado(agregado)

from src.shared.domain.value_objects.monto import Monto  # noqa: E402

