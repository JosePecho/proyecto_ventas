"""Puerto Repositorio de Usuario (implementado en infrastructure)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from src.modules.identity.domain.entities.usuario import Usuario


class UsuarioRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, usuario_id) -> Optional[Usuario]:
        ...

    @abstractmethod
    def buscar_por_username(self, username: str) -> Optional[Usuario]:
        ...

    @abstractmethod
    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        ...

    @abstractmethod
    def listar(self, incluir_inactivos: bool = False) -> Sequence[Usuario]:
        ...

    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario:
        ...

    @abstractmethod
    def eliminar(self, usuario: Usuario) -> None:
        ...

