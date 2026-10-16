from src.modules.customers.application.dto.cliente_input import ClienteInputDTO
from src.modules.customers.application.dto.cliente_output import ClienteOutputDTO
from src.modules.customers.domain.entities.cliente import Cliente
from src.modules.customers.domain.exceptions.cliente_exceptions import DNIYaRegistrado
from src.modules.customers.domain.repositories.cliente_repository import ClienteRepository


class RegistrarCliente:
    def __init__(self, repo: ClienteRepository):
        self._repo = repo

    def ejecutar(self, datos: ClienteInputDTO) -> ClienteOutputDTO:
        if datos.dni and self._repo.buscar_por_dni(datos.dni):
            raise DNIYaRegistrado(datos.dni)
        cliente = Cliente(
            nombre=datos.nombre,
            dni=datos.dni,
            email=datos.email,
            telefono=datos.telefono,
            direccion=datos.direccion,
            usuario_id=datos.usuario_id,
        )
        self._repo.guardar(cliente)
        return ClienteOutputDTO.desde_entidad(cliente)

