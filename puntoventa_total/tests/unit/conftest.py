"""Aislamiento de infraestructura para el nivel unit.

Deuda de testabilidad (ver docs/testing/test_master_plan.md, seccion 1.3):
los casos de usos de la capa `application` (ProcesarPago, AnularVenta,
ConfirmarPedido, ReservarStock, DescontarStock...) usan
`django.db.transaction.atomic()` como frontera transaccional hardcodeada.

En el nivel unit no debe tocarse ninguna base de datos, pero el context
manager intenta abrir una conexion al entrar. Este conftest (aplica solo a
tests bajo tests/unit/) sustituye `transaction.atomic` por un context manager
neutro, de modo que la logica de negocio se ejercite completa sin infra.

Refactor definitivo (pendiente): inyectar un puerto UnitOfWork en los casos
de uso en lugar de importar django.db directamente.
"""
from __future__ import annotations

from contextlib import contextmanager

import pytest


@contextmanager
def _atomic_sin_base_de_datos(*args, **kwargs):
    yield


@pytest.fixture(autouse=True)
def transaction_aislada(monkeypatch):
    from django.db import transaction

    monkeypatch.setattr(transaction, "atomic", _atomic_sin_base_de_datos)
