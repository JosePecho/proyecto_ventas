"""Entidad Pedido (cabecera)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.modules.orders.domain.enums.estado_pedido import EstadoPedido
from src.shared.domain.entities.base_entity import BaseEntity
from src.shared.domain.value_objects.dni import DNI


@dataclass
class Pedido(BaseEntity):
    numero: str = ""
    cliente_id: Optional[str] = None
    cliente_nombre: str = ""
    cliente_dni: Optional[DNI] = None
    cliente_telefono: str = ""
    cliente_email: str = ""
    estado: EstadoPedido = EstadoPedido.BORRADOR
    total: float = 0.0
    moneda: str = "PEN"
    hora_recojo: Optional[datetime] = None
    observaciones: str = ""

    def __post_init__(self) -> None:
        self._requerir(self.cliente_nombre, "cliente_nombre", 120)
        if not isinstance(self.estado, EstadoPedido):
            self.estado = EstadoPedido(self.estado)
        if self.cliente_dni and not isinstance(self.cliente_dni, DNI):
            self.cliente_dni = DNI(self.cliente_dni)

    @property
    def es_cancelable(self) -> bool:
        return self.estado in (EstadoPedido.BORRADOR, EstadoPedido.CONFIRMADO)

    def transicionar_a(self, nuevo_estado: EstadoPedido) -> None:
        if not self.estado.puede_transicion_a(nuevo_estado):
            raise TransicionInvalida(self.estado.value, nuevo_estado.value)
        self.estado = nuevo_estado
        self.marcar_actualizado()

    def asignar_hora_recojo(self, hora: datetime) -> None:
        if hora < datetime.now(tz=hora.tzinfo):
            raise HoraRecojoInvalida("no puede ser en el pasado")
        if hora.minute not in (0, 30) or hora.second or hora.microsecond:
            raise HoraRecojoInvalida("solo franjas de 30 minutos")
        self.hora_recojo = hora
        self.marcar_actualizado()

    def cancelar(self, motivo: str = "") -> None:
        self.transicionar_a(EstadoPedido.CANCELADO)
        self.observaciones = motivo
        self.marcar_actualizado()

from src.modules.orders.domain.exceptions.pedido_exceptions import (  # noqa: E402
    HoraRecojoInvalida,
    TransicionInvalida,
)

