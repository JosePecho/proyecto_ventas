from src.modules.customers.application.dto.cliente_output import ClienteOutputDTO
from src.modules.customers.domain.repositories.cliente_repository import ClienteRepository


class ConsultarCliente:
    def __init__(self, repo: ClienteRepository):
        self._repo = repo

    def por_id(self, cliente_id: str) -> ClienteOutputDTO:
        cliente = self._repo.buscar_por_id(cliente_id)
        if cliente is None:
            from src.modules.customers.domain.exceptions.cliente_exceptions import ClienteNoEncontrado

            raise ClienteNoEncontrado(cliente_id)
        return ClienteOutputDTO.desde_entidad(cliente)

    def por_dni(self, dni: str) -> ClienteOutputDTO:
        cliente = self._repo.buscar_por_dni(dni)
        if cliente is None:
            from src.modules.customers.domain.exceptions.cliente_exceptions import ClienteNoEncontrado

            raise ClienteNoEncontrado(dni)
        return ClienteOutputDTO.desde_entidad(cliente)

    def listar(self, termino: str | None = None) -> list[ClienteOutputDTO]:
        return [ClienteOutputDTO.desde_entidad(c) for c in self._repo.listar(termino)]

