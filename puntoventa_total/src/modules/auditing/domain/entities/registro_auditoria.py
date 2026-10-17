"""Registro de auditoria inmutable: una vez escrito no se modifica."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from src.shared.domain.clock import utc_now

ACCIONES_VALIDAS = {
    "VENTA_PAGADA", "VENTA_ANULADA", "CAJA_ABIERTA", "CAJA_CERRADA",
    "STOCK_AJUSTADO", "MERMA_REGISTRADA", "PRODUCTO_CREADO", "PRODUCTO_MODIFICADO",
    "USUARIO_CREADO", "USUARIO_MODIFICADO", "PROMOCION_ACTIVADA", "PEDIDO_CONFIRMADO",
    "PEDIDO_CANCELADO", "CLIENTE_ANONIMIZADO", "LOGIN_EXITOSO", "LOGIN_FALLIDO",
}


@dataclass(frozen=True)
class RegistroAuditoria:
    accion: str
    entidad: str
    entidad_id: str
    usuario_id: str = ""
    detalle: dict = field(default_factory=dict)
    ip: str = ""
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    fecha: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.accion not in ACCIONES_VALIDAS:
            raise ValidationException(f"Accion de auditoria no reconocida: {self.accion}")
        if not self.entidad or not self.entidad_id:
            raise ValidationException("La auditoria requiere entidad y entidad_id")

    def detalle_json(self) -> str:
        return json.dumps(self.detalle, ensure_ascii=False, default=str)

    @classmethod
    def crear(cls, accion: str, entidad: str, entidad_id: str, usuario_id: str = "", detalle: dict | None = None, ip: str = "") -> "RegistroAuditoria":
        return cls(
            accion=accion,
            entidad=entidad,
            entidad_id=str(entidad_id),
            usuario_id=str(usuario_id) if usuario_id else "",
            detalle=detalle or {},
            ip=ip,
        )

from src.shared.domain.exceptions.validation_exception import ValidationException  # noqa: E402

