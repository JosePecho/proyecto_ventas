"""Unit of Work concreto sobre `transaction.atomic` de Django."""
from __future__ import annotations

from typing import Callable

from django.db import transaction

from src.shared.application.interfaces.unit_of_work import IUnitOfWork


class MySQLUnitOfWork(IUnitOfWork):
    """Reposicion el registro de repositorios y gestiona la transaccion.

    Cada modulo registra sus fabricas de repositorio en el constructor
    para no violar las reglas de dependencias (la infra conoce al dominio).
    """

    def __init__(self, usando: str = "default"):
        self._usando = usando
        self._fabricas: dict[type, Callable] = {}
        self._cache: dict[type, object] = {}
        self._transaccion = None

    def registrar(self, tipo_repositorio: type, fabrica: Callable) -> None:
        self._fabricas[tipo_repositorio] = fabrica

    def repositorio(self, tipo: type):
        if tipo not in self._cache:
            if tipo not in self._fabricas:
                raise KeyError(f"Repositorio no registrado: {tipo.__name__}")
            self._cache[tipo] = self._fabricas[tipo]()
        return self._cache[tipo]

    def __enter__(self) -> "MySQLUnitOfWork":
        self._transaccion = transaction.atomic(using=self._usando)
        self._transaccion.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # `transaction.atomic` resuelve commit/rollback al salir; solo delegamos.
        transaccion, self._transaccion = self._transaccion, None
        if transaccion is not None:
            transaccion.__exit__(exc_type, exc, tb)

    def commit(self) -> None:
        """Sin efecto: la confirmacion la resuelve `__exit__` de la transaccion."""
        return None

    def rollback(self) -> None:
        if self._transaccion is not None:
            transaction.set_rollback(True)

    def guardar_punto(self) -> object:
        """Savepoint para operaciones parciales dentro de la transaccion."""
        return transaction.savepoint(using=self._usando)

    def restaurar_punto(self, savepoint) -> None:
        transaction.savepoint_rollback(savepoint, using=self._usando)

