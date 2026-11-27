"""Dos altas simultáneas: comprobar restricciones y atomicidad en InnoDB real."""
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import IntegrityError, close_old_connections, connection

from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.identity.application.dto.google_identity import GoogleIdentity
from src.modules.identity.infrastructure.google_registration_service import completar_google
from src.modules.identity.infrastructure.persistence.django_models.google_vinculo_model import (
    GoogleVinculoModel,
)
from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel
from src.shared.domain.exceptions.domain_exception import DomainException


@pytest.mark.integration
@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != "mysql", reason="Concurrencia de alta requiere InnoDB aislado")
def test_dos_registros_simultaneos_no_duplican_cuenta():
    identidad = GoogleIdentity(uid="uid-concurrente", email="concurrente@gmail.com", nombre="Cliente QA",
                               proyecto="puntoventa-a7f93", auth_time=int(time.time()))
    barrera = Barrier(2)

    def ejecutar():
        close_old_connections()
        try:
            barrera.wait(timeout=10)
            completar_google(identidad, {"nombre": "Cliente QA", "dni": "87654321", "telefono": "987654321"})
            return "ok"
        except (DomainException, IntegrityError):
            return "conflicto"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(lambda _: ejecutar(), range(2)))
    assert "ok" in resultados
    assert UsuarioModel.objects.count() == ClienteModel.objects.count() == GoogleVinculoModel.objects.count() == 1
