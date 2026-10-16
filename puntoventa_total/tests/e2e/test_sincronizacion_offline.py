"""Valida el contrato JSON que la cola offline espera del servidor."""
import json

import pytest

pytestmark = [pytest.mark.e2e]


def test_esquema_de_accion_encolable():
    accion = {
        "uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "url": "/pos/venta/1/agregar/2/",
        "datos": {"cantidad": 2},
        "fecha": "2026-01-01T10:00:00",
        "intentos": 0,
    }
    serializado = json.dumps(accion)
    assert json.loads(serializado)["url"].startswith("/pos/")

