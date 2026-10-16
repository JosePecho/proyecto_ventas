from src.modules.customers.application.ports.historial_compras_port import HistorialComprasPort
from src.modules.customers.domain.repositories.cliente_repository import ClienteRepository


class ConsultarHistorialCompras:
    def __init__(self, repo: ClienteRepository, historial: HistorialComprasPort):
        self._repo = repo
        self._historial = historial

    def ejecutar(self, cliente_id: str) -> dict:
        if self._repo.buscar_por_id(cliente_id) is None:
            from src.modules.customers.domain.exceptions.cliente_exceptions import ClienteNoEncontrado

            raise ClienteNoEncontrado(cliente_id)
        compras = self._historial.compras_del_cliente(cliente_id)
        return {
            "cliente_id": cliente_id,
            "compras": list(compras),
            "cantidad": len(compras),
            "total_gastado": self._historial.total_gastado(cliente_id),
        }

