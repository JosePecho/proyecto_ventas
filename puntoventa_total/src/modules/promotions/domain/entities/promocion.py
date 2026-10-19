from __future__ import annotations

from dataclasses import dataclass, field
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
    componentes: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._requerir(self.nombre, "nombre", 120)
        if not isinstance(self.tipo, TipoPromocion):
            self.tipo = TipoPromocion(self.tipo)
        if not isinstance(self.estado, EstadoPromocion):
            self.estado = EstadoPromocion(self.estado)
        if self.tipo == TipoPromocion.NX1 and (self.cantidad_requerida < 2 or self.cantidad_gratuita < 1):
            raise ValidationException("Promocion NX1 requiere cantidad_requerida >= 2 y cantidad_gratuita >= 1")
        if self.tipo == TipoPromocion.NX1 and self.cantidad_gratuita >= self.cantidad_requerida:
            raise ValidationException("Las unidades gratuitas deben ser menores al paquete")
        if self.tipo == TipoPromocion.COMBO:
            if not isinstance(self.componentes, list) or any(not isinstance(c, dict) for c in self.componentes):
                raise ValidationException("Componentes debe ser una lista de productos y cantidades")
            if len(self.componentes) < 2 or len({c.get("producto_id") for c in self.componentes}) != len(self.componentes):
                raise ValidationException("Un combo requiere al menos dos productos distintos")
            from uuid import UUID
            for componente in self.componentes:
                try:
                    UUID(str(componente["producto_id"]))
                    cantidad = componente["cantidad"]
                    if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
                        raise ValueError
                except (KeyError, TypeError, ValueError) as exc:
                    raise ValidationException("Componente de combo inválido") from exc

    def esta_vigente(self, momento: datetime | None = None) -> bool:
        referencia = self.vigencia_desde or self.vigencia_hasta
        momento = momento or datetime.now(tz=referencia.tzinfo if referencia else None)
        if self.estado != EstadoPromocion.ACTIVA:
            return False
        if self.vigencia_desde and momento < self.vigencia_desde:
            return False
        if self.vigencia_hasta and momento >= self.vigencia_hasta:
            return False
        return True

    def programar(self, desde: datetime, hasta: datetime) -> None:
        if hasta <= desde:
            raise VigenciaInvalida()
        if desde < datetime.now(tz=desde.tzinfo):
            raise VigenciaInvalida()
        self.vigencia_desde, self.vigencia_hasta = desde, hasta
        self.estado = EstadoPromocion.PROGRAMADA
        self.marcar_actualizado()

    def activar(self) -> None:
        if self.estado not in (EstadoPromocion.PROGRAMADA, EstadoPromocion.BORRADOR):
            raise PromocionException(f"No se puede activar desde {self.estado.value}")
        ahora = datetime.now(tz=self.vigencia_hasta.tzinfo if self.vigencia_hasta else None)
        if self.vigencia_hasta and ahora >= self.vigencia_hasta:
            raise VigenciaInvalida()
        self.estado = EstadoPromocion.ACTIVA
        self.marcar_actualizado()

    def cancelar(self, motivo: str = "") -> None:
        if self.estado == EstadoPromocion.CANCELADA:
            raise PromocionException("La promocion ya fue cancelada")
        self.estado = EstadoPromocion.CANCELADA
        self.marcar_actualizado()

    def finalizar(self) -> None:
        if self.estado not in (EstadoPromocion.ACTIVA, EstadoPromocion.PROGRAMADA):
            raise PromocionException("Solo puede vencer una promoción activa o programada")
        self.estado = EstadoPromocion.FINALIZADA
        self.marcar_actualizado()

    def cubre_producto(self, producto_id: str) -> bool:
        return self.tipo != TipoPromocion.COMBO and not self.aplica_clientes_frecuentes and (
            self.producto_id == producto_id or self.producto_id is None and self.categoria_id is None)

    @property
    def estado_label(self):
        return {"BORRADOR": "Borrador", "PROGRAMADA": "Borrador", "ACTIVA": "Activa",
                "FINALIZADA": "Vencida", "CANCELADA": "Cancelada"}[self.estado.value]

    def descuento_combo(self, lineas) -> Monto:
        moneda = lineas[0].precio_unitario.moneda if lineas else "PEN"
        cero = Monto(0, moneda)
        if self.tipo != TipoPromocion.COMBO or not self.esta_vigente() or not self.descuento:
            return cero
        por_producto = {l.producto_id: l for l in lineas}
        if any(c["producto_id"] not in por_producto for c in self.componentes):
            return cero
        paquetes = min(por_producto[c["producto_id"]].cantidad // c["cantidad"] for c in self.componentes)
        precio_normal = sum((por_producto[c["producto_id"]].precio_unitario.valor * c["cantidad"] for c in self.componentes), Decimal(0))
        return Monto(max(Decimal(0), precio_normal - self.descuento.valor) * paquetes, moneda)

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

