"""Puerto Unit of Work: garantiza atomicidad entre repositorios de un caso de uso."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

T = TypeVar("T")


class UnitOfWork(ABC):
    """Expone los repositorios del modulo actual y gestiona la transaccion."""

    @abstractmethod
    def commit(self) -> None:
        """Confirma los cambios de la transaccion actual."""

    @abstractmethod
    def rollback(self) -> None:
        """Deshace los cambios pendientes."""

    @abstractmethod
    def __enter__(self) -> "UnitOfWork":
        ...

    @abstractmethod
    def __exit__(self, exc_type, exc, tb) -> None:
        """Realiza rollback automatico si ocurre una excepcion."""


class IUnitOfWork(ABC):
    """Interfaz generica para obtener repositorios por tipo."""

    @abstractmethod
    def repositorio(self, tipo: type[T]) -> T:
        """Devuelve el repositorio de dominio solicitado."""

    @abstractmethod
    def commit(self) -> None:
        ...

    @abstractmethod
    def rollback(self) -> None:
        ...


class NullUnitOfWork(UnitOfWork):
    """Transaccion nula: permite ejecutar casos de uso sin base de datos (pruebas unitarias)."""

    def commit(self) -> None:
        """Sin cambios que confirmar."""

    def rollback(self) -> None:
        """Sin cambios que deshacer."""

    def __enter__(self) -> "NullUnitOfWork":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

