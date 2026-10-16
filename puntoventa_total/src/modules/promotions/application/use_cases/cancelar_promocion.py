from src.modules.promotions.application.dto.promocion_output import PromocionOutputDTO
from src.modules.promotions.domain.exceptions.promocion_exceptions import PromocionNoEncontrada
from src.modules.promotions.domain.repositories.promocion_repository import PromocionRepository


class CancelarPromocion:
    def __init__(self, repo: PromocionRepository):
        self._repo = repo

    def ejecutar(self, promocion_id: str, motivo: str = "") -> PromocionOutputDTO:
        promocion = self._repo.buscar_por_id(promocion_id)
        if promocion is None:
            raise PromocionNoEncontrada(promocion_id)
        promocion.cancelar(motivo)
        self._repo.guardar(promocion)
        return PromocionOutputDTO.desde_entidad(promocion)

