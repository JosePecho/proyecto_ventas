from typing import Optional
from uuid import UUID

from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel


class DjangoStockRepository(StockRepository):
    def obtener(self, producto_id: str) -> Optional[Existencia]:
        m = ExistenciaModel.objects.filter(producto_id=producto_id).first()
        if m is None:
            return None
        return Existencia(
            id=m.id,
            producto_id=str(m.producto_id),
            cantidad=m.cantidad,
            reservada=m.reservada,
            activo=m.activo,
            fecha_creacion=m.fecha_creacion,
            fecha_actualizacion=m.fecha_actualizacion,
        )

    def disponible(self, producto_id: str) -> int:
        m = ExistenciaModel.objects.filter(producto_id=producto_id).first()
        return (m.cantidad - m.reservada) if m else 0

    def guardar(self, existencia: Existencia) -> Existencia:
        m = ExistenciaModel.objects.filter(id=existencia.id).first()
        m = m or ExistenciaModel(id=existencia.id)
        m.producto_id = UUID(str(existencia.producto_id))
        m.cantidad = existencia.cantidad
        m.reservada = existencia.reservada
        m.activo = existencia.activo
        m.save()
        return existencia

    def productos_bajo_minimo(self, umbral: int) -> list[dict]:
        filas = ExistenciaModel.objects.filter(activo=True, cantidad__lte=umbral).values(
            "producto_id", "cantidad", "reservada"
        )
        return [
            {"producto_id": str(f["producto_id"]), "disponible": f["cantidad"] - f["reservada"]}
            for f in filas
        ]

