from src.modules.customers.application.dto.cliente_input import ActualizarClienteDTO
from src.modules.customers.application.dto.cliente_output import ClienteOutputDTO
from src.modules.customers.domain.exceptions.cliente_exceptions import ClienteNoEncontrado
from src.modules.customers.domain.repositories.cliente_repository import ClienteRepository


class ActualizarCliente:
    def __init__(self, repo: ClienteRepository):
        self._repo = repo

    def ejecutar(self, datos: ActualizarClienteDTO) -> ClienteOutputDTO:
        cliente = self._repo.buscar_por_id(datos.cliente_id)
        if cliente is None:
            raise ClienteNoEncontrado(datos.cliente_id)
        if datos.nombre:
            cliente.nombre = datos.nombre
        cliente.actualizar_contacto(
            email=datos.email or "", telefono=datos.telefono or "", direccion=datos.direccion or ""
        )
        self._repo.guardar(cliente)
        return ClienteOutputDTO.desde_entidad(cliente)

