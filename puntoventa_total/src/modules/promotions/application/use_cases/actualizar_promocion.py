from src.modules.promotions.application.dto.promocion_output import PromocionOutputDTO
from src.modules.promotions.domain.exceptions.promocion_exceptions import PromocionNoEncontrada
from src.modules.promotions.domain.repositories.promocion_repository import PromocionRepository


class ActualizarPromocion:
    def __init__(self, repo: PromocionRepository, moneda: str = "PEN"):
        self._repo = repo
        self._moneda = moneda

    def ejecutar(self, promocion_id: str, nombre: str | None = None, descuento_valor: float | None = None) -> PromocionOutputDTO:
        from decimal import Decimal

        from src.modules.promotions.domain.enums.tipo_promocion import TipoPromocion
        from src.modules.promotions.domain.value_objects.descuento import Descuento
        from src.shared.domain.value_objects.monto import Monto

        promocion = self._repo.buscar_por_id(promocion_id)
        if promocion is None:
            raise PromocionNoEncontrada(promocion_id)
        if nombre:
            promocion.nombre = nombre
        if descuento_valor is not None:
            promocion.descuento = (
                Descuento.porcentaje(Decimal(str(descuento_valor)))
                if promocion.tipo == TipoPromocion.PORCENTAJE
                else Descuento.monto_fijo(Monto(descuento_valor, self._moneda))
            )
        promocion.marcar_actualizado()
        self._repo.guardar(promocion)
        return PromocionOutputDTO.desde_entidad(promocion)

