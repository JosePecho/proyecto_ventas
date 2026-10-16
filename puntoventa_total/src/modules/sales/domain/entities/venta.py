"""Entidad Venta (lineas de nivel bajo). La orquestacion vive en el agregado."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.shared.domain.entities.base_entity import BaseEntity


@dataclass
class Venta(BaseEntity):
    numero_ticket: str = ""
    cajero_id: str = ""
    turno_caja_id: Optional[str] = None
    cliente_id: Optional[str] = None
    estado: EstadoVenta = EstadoVenta.BORRADOR
    subtotal: float = 0.0
    descuento: float = 0.0
    total: float = 0.0
    igv: float = 0.0
    moneda: str = "PEN"
    observacion: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.estado, EstadoVenta):
            self.estado = EstadoVenta(self.estado)

    @property
    def es_borrador(self) -> bool:
        return self.estado == EstadoVenta.BORRADOR

    @property
    def es_pagada(self) -> bool:
        return self.estado == EstadoVenta.PAGADA

    def verificar_modificable(self) -> None:
        if not self.es_borrador:
            raise VentaNoModificable(self.estado.value)

    def marcar_pagada(self) -> None:
        self.estado = EstadoVenta.PAGADA
        self.marcar_actualizado()

    def anular(self, motivo: str = "") -> None:
        if self.estado == EstadoVenta.ANULADA:
            raise VentaException("La venta ya esta anulada")
        self.estado = EstadoVenta.ANULADA
        self.observacion = motivo
        self.marcar_actualizado()

    def puede_anularse(self) -> bool:
        return self.estado in (EstadoVenta.BORRADOR, EstadoVenta.PAGADA)

from src.modules.sales.domain.exceptions.venta_exceptions import (  # noqa: E402
    VentaException,
    VentaNoModificable,
)

