"""Plugin optativo: PYTEST_PLUGINS=scripts.qa_profile_pos con MySQL efimero.

Genera el perfil de un POST de cobro sin modificar su logica ni sus assertions.
No usar estas mediciones instrumentadas como evidencia del presupuesto HTTP.
"""
import cProfile
from functools import wraps
import json
import os
from pathlib import Path
import time

import pytest


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    if os.environ.get("INVENTORY_EPHEMERAL_MYSQL") != "1":
        raise RuntimeError("El perfil requiere el wrapper de MySQL efimero")
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago

    original = ProcesarPago.ejecutar

    @wraps(original)
    def ejecutar(self, datos):
        perfil = cProfile.Profile()
        inicio = time.perf_counter()
        with CaptureQueriesContext(connection) as consultas:
            resultado = perfil.runcall(original, self, datos)
        carpeta = Path("reports/pos-profile")
        carpeta.mkdir(parents=True, exist_ok=True)
        perfil.dump_stats(str(carpeta / "payment.pstats"))
        (carpeta / "queries.json").write_text(json.dumps({
            "elapsed_ms": (time.perf_counter() - inicio) * 1000,
            "queries": list(consultas), "count": len(consultas),
        }, indent=2), encoding="utf-8")
        return resultado

    ProcesarPago.ejecutar = ejecutar
