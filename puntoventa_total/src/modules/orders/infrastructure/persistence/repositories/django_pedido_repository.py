from typing import Optional, Sequence

from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate
from src.modules.orders.domain.repositories.pedido_repository import PedidoRepository
from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
from src.modules.orders.infrastructure.persistence.mappers.pedido_mapper import PedidoMapper


class DjangoPedidoRepository(PedidoRepository):
    def buscar_por_id(self, pedido_id) -> Optional[PedidoAggregate]:
        m = PedidoModel.objects.filter(pk=pedido_id).prefetch_related("detalles").first()
        return PedidoMapper.agregado_a_dominio(m) if m else None

    def buscar_por_numero(self, numero: str) -> Optional[PedidoAggregate]:
        m = PedidoModel.objects.filter(numero=numero).prefetch_related("detalles").first()
        return PedidoMapper.agregado_a_dominio(m) if m else None

    def guardar(self, agregado: PedidoAggregate) -> PedidoAggregate:
        PedidoMapper.guardar_agregado(agregado)
        return agregado

    def listar_por_cliente(self, cliente_id: str) -> Sequence[PedidoAggregate]:
        qs = PedidoModel.objects.filter(cliente_id=cliente_id).prefetch_related("detalles")
        return [PedidoMapper.agregado_a_dominio(m) for m in qs]

    def listar_por_estado(self, estado: str) -> Sequence[PedidoAggregate]:
        qs = PedidoModel.objects.filter(estado=estado).prefetch_related("detalles")
        return [PedidoMapper.agregado_a_dominio(m) for m in qs]

    def siguiente_numero(self) -> str:
        from datetime import date

        total = PedidoModel.objects.filter(fecha_creacion__date=date.today()).count()
        return f"P{date.today():%Y%m%d}{total + 1:04d}"

