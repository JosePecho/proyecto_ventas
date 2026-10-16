from src.modules.promotions.domain.entities.promocion import Promocion
from src.modules.promotions.domain.services.motor_promociones import MotorPromociones
from src.modules.promotions.domain.services.politica_promociones import PoliticaPromociones
from src.shared.domain.value_objects.monto import Monto


class ValidarPromocion:
    """Valida que una promocion pueda aplicarse antes de cobrar."""

    def ejecutar(self, promocion: Promocion, monto_base: Monto) -> dict:
        vigente = promocion.esta_vigente()
        descuento = promocion.calcular_descuento(monto_base) if vigente else Monto(0, monto_base.moneda)
        pct = (descuento.valor / monto_base.valor * 100) if not monto_base.es_cero() else 0
        PoliticaPromociones.validar_tope_venta(pct)
        return {
            "aplicable": vigente and descuento.valor > 0,
            "descuento": descuento.a_float(),
            "motivo": "" if vigente else "fuera de vigencia",
        }

