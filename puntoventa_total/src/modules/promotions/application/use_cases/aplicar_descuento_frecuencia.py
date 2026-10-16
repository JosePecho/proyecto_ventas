"""Descuento por fidelizacion: clientes frecuentes obtienen mejor precio."""
from __future__ import annotations

from decimal import Decimal

from src.modules.promotions.application.ports.frecuencia_cliente_port import FrecuenciaClientePort
from src.modules.promotions.domain.repositories.promocion_repository import PromocionRepository
from src.shared.domain.value_objects.monto import Monto

PCT_FRECUENTE = Decimal("10")
PCT_HABITUAL = Decimal("5")


class AplicarDescuentoFrecuencia:
    def __init__(self, repo: PromocionRepository, puerto: FrecuenciaClientePort | None = None):
        self._repo = repo
        self._puerto = puerto

    def ejecutar(self, cliente_id: str, subtotal: Monto) -> Monto:
        clasificacion = self._puerto.clasificacion(cliente_id) if self._puerto else "SIN_DATOS"
        pct = PCT_FRECUENTE if clasificacion == "FRECUENTE" else (PCT_HABITUAL if clasificacion == "OCASIONAL" else Decimal("0"))
        if pct == 0:
            return Monto(0, subtotal.moneda)

        # solo aplica si el cliente tiene promociones de fidelizacion vigentes
        vigentes = [p for p in self._repo.listar_activas() if p.aplica_clientes_frecuentes and p.esta_vigente()]
        if not vigentes:
            return Monto(0, subtotal.moneda)
        return subtotal.porcentaje(pct)

