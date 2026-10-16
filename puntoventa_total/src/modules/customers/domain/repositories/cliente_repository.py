from abc import ABC, abstractmethod
from typing import Optional, Sequence

from src.modules.customers.domain.entities.cliente import Cliente


class ClienteRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, cliente_id) -> Optional[Cliente]:
        ...

    @abstractmethod
    def buscar_por_dni(self, dni: str) -> Optional[Cliente]:
        ...

    @abstractmethod
    def buscar_por_usuario(self, usuario_id: str) -> Optional[Cliente]:
        ...

    @abstractmethod
    def listar(self, termino: str | None = None) -> Sequence[Cliente]:
        ...

    @abstractmethod
    def guardar(self, cliente: Cliente) -> Cliente:
        ...

