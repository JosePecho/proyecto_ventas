"""Gestion central de transacciones de base de datos."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Callable, Iterator

from django.db import transaction


class TransactionManager:
    """Envuelve atomicidad de Django y expone hooks para UoW/auditoria."""

    @staticmethod
    @contextmanager
    def atomico(using: str = "default") -> Iterator[None]:
        with transaction.atomic(using=using):
            yield

    @staticmethod
    def en_transaccion() -> bool:
        return transaction.get_connection().in_atomic_block

    @staticmethod
    def ejecutar_atomico(func: Callable, *args, **kwargs):
        with TransactionManager.atomico():
            return func(*args, **kwargs)

