from datetime import datetime
from decimal import Decimal

from src.modules.promotions.application.dto.promocion_input import PromocionInputDTO
from src.modules.promotions.application.dto.promocion_output import PromocionOutputDTO
from src.modules.promotions.domain.entities.promocion import Promocion
from src.modules.promotions.domain.enums.tipo_promocion import TipoPromocion
from src.modules.promotions.domain.repositories.promocion_repository import PromocionRepository
from src.modules.promotions.domain.value_objects.descuento import Descuento
from src.shared.domain.value_objects.monto import Monto


class CrearPromocion:
    def __init__(self, repo: PromocionRepository, moneda: str = "PEN"):
        self._repo = repo
        self._moneda = moneda

    def ejecutar(self, datos: PromocionInputDTO) -> PromocionOutputDTO:
        tipo = TipoPromocion(datos.tipo)
        descuento = (
            Descuento.porcentaje(Decimal(str(datos.descuento_valor)))
            if tipo == TipoPromocion.PORCENTAJE
            else Descuento.monto_fijo(Monto(datos.descuento_valor, self._moneda))
        )
        promocion = Promocion(
            nombre=datos.nombre,
            tipo=tipo,
            producto_id=datos.producto_id,
            categoria_id=datos.categoria_id,
            descuento=descuento,
            cantidad_requerida=datos.cantidad_requerida,
            cantidad_gratuita=datos.cantidad_gratuita,
            aplica_clientes_frecuentes=datos.aplica_clientes_frecuentes,
        )
        if datos.vigencia_desde and datos.vigencia_hasta:
            promocion.programar(
                datetime.fromisoformat(datos.vigencia_desde), datetime.fromisoformat(datos.vigencia_hasta)
            )
        self._repo.guardar(promocion)
        return PromocionOutputDTO.desde_entidad(promocion)

