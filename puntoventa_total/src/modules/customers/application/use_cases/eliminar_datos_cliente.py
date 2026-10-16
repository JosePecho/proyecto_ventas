"""Derecho al olvido (PDPA): anonimiza sin borrar la trazabilidad de ventas."""
from __future__ import annotations

from src.modules.customers.domain.exceptions.cliente_exceptions import ClienteNoEncontrado
from src.modules.customers.domain.repositories.cliente_repository import ClienteRepository
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork


class EliminarDatosCliente:
    def __init__(self, repo: ClienteRepository, uow: UnitOfWork | None = None):
        self._repo = repo
        self._uow = uow or NullUnitOfWork()

    def ejecutar(self, cliente_id: str, usuario_solicitante: str = "") -> dict:
        with self._uow:
            cliente = self._repo.buscar_por_id(cliente_id)
            if cliente is None:
                raise ClienteNoEncontrado(cliente_id)
            cliente.anonimizar()
            self._repo.guardar(cliente)
        return {"cliente_id": cliente_id, "anonimizado": True, "solicitado_por": usuario_solicitante}

