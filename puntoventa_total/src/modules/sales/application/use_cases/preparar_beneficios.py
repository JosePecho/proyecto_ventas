from decimal import Decimal

from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada
from src.shared.domain.value_objects.monto import Monto


class PrepararBeneficiosVenta:
    def __init__(self, repo, promociones):
        self.repo, self.promociones = repo, promociones

    def aplicar(self, agregado):
        agregado.venta.verificar_modificable()
        if agregado.pagos:
            return
        agregado.calcular_totales()
        base = Monto(agregado.venta.subtotal, agregado.venta.moneda)
        beneficio = self.promociones.descuento_venta(str(agregado.venta.id), base, agregado.venta.cliente_id)
        if base.valor and beneficio.valor:
            from src.shared.domain.exceptions.validation_exception import ValidationException
            if beneficio.valor > base.valor:
                raise ValidationException("El beneficio supera el subtotal")
            pct = (beneficio.valor * 100 / base.valor).quantize(Decimal("0.01"))
            agregado.descuento_venta_pct = max(agregado.descuento_venta_pct, pct)
        agregado.calcular_totales()

    def ejecutar(self, venta_id):
        agregado = self.repo.buscar_por_id(venta_id)
        if agregado is None:
            raise VentaNoEncontrada(venta_id)
        self.aplicar(agregado)
        self.repo.guardar(agregado)
        return agregado
