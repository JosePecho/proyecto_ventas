from src.modules.promotions.domain.entities.promocion import Promocion
from src.modules.promotions.domain.repositories.promocion_repository import PromocionRepository
from src.modules.promotions.domain.services.motor_promociones import MotorPromociones
from src.shared.domain.value_objects.monto import Monto


class CalcularDescuento:
    def __init__(self, repo: PromocionRepository):
        self._repo = repo

    def por_producto(self, producto_id: str, monto_base: Monto, cantidad: int = 1) -> Monto:
        """Uso por el adaptador de ventas del POS."""
        activas = self._repo.listar_activas()
        _, descuento = MotorPromociones.mejor_para_producto(activas, producto_id, monto_base, cantidad)
        return descuento

    def ejecutar(self, promocion_id: str, monto_base: Monto, cantidad: int = 1) -> dict:
        promocion = self._repo.buscar_por_id(promocion_id)
        if promocion is None:
            from src.modules.promotions.domain.exceptions.promocion_exceptions import PromocionNoEncontrada

            raise PromocionNoEncontrada(promocion_id)
        descuento = promocion.calcular_descuento(monto_base, cantidad)
        return {"promocion_id": promocion_id, "descuento": descuento.a_float(), "monto_final": (monto_base - descuento).a_float()}

