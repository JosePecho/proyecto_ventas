"""Puerto Repositorio de Usuario (implementado en infrastructure)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.modules.identity.domain.entities.usuario import Usuario


class UsuarioRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, usuario_id) -> Usuario | None:
        ...

    @abstractmethod
    def buscar_por_username(self, username: str) -> Usuario | None:
        ...

    @abstractmethod
    def buscar_por_email(self, email: str) -> Usuario | None:
        ...

    def buscar_por_email_unico(self, email: str) -> Usuario | None:
        """Rechaza coincidencias ambiguas, incluso con cuentas inactivas."""
        coincidencias = [u for u in self.listar(incluir_inactivos=True) if u.email.casefold() == email.casefold()]
        return coincidencias[0] if len(coincidencias) == 1 else None

    @abstractmethod
    def listar(self, incluir_inactivos: bool = False) -> Sequence[Usuario]:
        ...

    @abstractmethod
    def guardar(self, usuario: Usuario) -> Usuario:
        ...

    @abstractmethod
    def eliminar(self, usuario: Usuario) -> None:
        ...

