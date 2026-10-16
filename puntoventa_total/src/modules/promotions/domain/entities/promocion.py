from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from src.modules.promotions.domain.enums.estado_promocion import EstadoPromocion
from src.modules.promotions.domain.enums.tipo_promocion import TipoPromocion
from src.modules.promotions.domain.value_objects.descuento import Descuento
from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.value_objects.monto import Monto


@dataclass
class Promocion(BaseEntity):
    nombre: str = ""
    tipo: TipoPromocion = TipoPromocion.PORCENTAJE
    estado: EstadoPromocion = EstadoPromocion.BORRADOR
    producto_id: Optional[str] = None
    categoria_id: Optional[str] = None
    descuento: Optional[Descuento] = None
    cantidad_requerida: int = 0
    cantidad_gratuita: int = 0
    vigencia_desde: Optional[datetime] = None
    vigencia_hasta: Optional[datetime] = None
    aplica_clientes_frecuentes: bool = False

    def __post_init__(self) -> None:
        self._requerir(self.nombre, "nombre", 120)
        if not isinstance(self.tipo, TipoPromocion):
            self.tipo = TipoPromocion(self.tipo)
        if not isinstance(self.estado, EstadoPromocion):
            self.estado = EstadoPromocion(self.estado)
        if self.tipo == TipoPromocion.NX1 and (self.cantidad_requerida < 2 or self.cantidad_gratuita < 1):
            raise ValidationException("Promocion NX1 requiere cantidad_requerida >= 2 y cantidad_gratuita >= 1")

    def esta_vigente(self, momento: datetime | None = None) -> bool:
        momento = momento or datetime.now()
        if self.estado != EstadoPromocion.ACTIVA:
            return False
        if self.vigencia_desde and momento < self.vigencia_desde:
            return False
        if self.vigencia_hasta and momento > self.vigencia_hasta:
            return False
        return True

    def programar(self, desde: datetime, hasta: datetime) -> None:
        if hasta <= desde:
            raise VigenciaInvalida()
        if desde < datetime.now():
            raise VigenciaInvalida()
        self.vigencia_desde, self.vigencia_hasta = desde, hasta
        self.estado = EstadoPromocion.PROGRAMADA
        self.marcar_actualizado()

    def activar(self) -> None:
        if self.estado not in (EstadoPromocion.PROGRAMADA, EstadoPromocion.BORRADOR):
            raise PromocionException(f"No se puede activar desde {self.estado.value}")
        self.estado = EstadoPromocion.ACTIVA
        self.marcar_actualizado()

    def cancelar(self, motivo: str = "") -> None:
        if self.estado == EstadoPromocion.FINALIZADA:
            raise PromocionException("La promocion ya finalizo")
        self.estado = EstadoPromocion.CANCELADA
        self.marcar_actualizado()

    def finalizar(self) -> None:
        self.estado = EstadoPromocion.FINALIZADA
        self.marcar_actualizado()

    def cubre_producto(self, producto_id: str) -> bool:
        return self.producto_id == producto_id

    def calcular_descuento(self, monto_base: Monto, cantidad: int = 1) -> Monto:
        if not self.esta_vigente() or self.descuento is None:
            return Monto(0, monto_base.moneda)
        if self.tipo == TipoPromocion.NX1:
            packs = cantidad // self.cantidad_requerida
            unidades_gratis = packs * self.cantidad_gratuita
            if unidades_gratis == 0:
                return Monto(0, monto_base.moneda)
            unitario = monto_base.valor / cantidad if cantidad else monto_base.valor
            return Monto(min(unitario * unidades_gratis, monto_base.valor), monto_base.moneda)
        return self.descuento.aplicar_a(monto_base)

from src.modules.promotions.domain.exceptions.promocion_exceptions import (  # noqa: E402
    PromocionException,
    VigenciaInvalida,
)
from src.shared.domain.exceptions.validation_exception import ValidationException  # noqa: E402

