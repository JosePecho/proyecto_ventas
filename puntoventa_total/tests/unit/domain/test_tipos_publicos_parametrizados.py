"""Contratos publicos de enums y errores consumidos por formularios y vistas."""
import inspect
import re
from enum import Enum
from importlib import import_module
from pathlib import Path

import pytest

from src.shared.domain.exceptions.domain_exception import DomainException

pytestmark = pytest.mark.unit
RAIZ = Path(__file__).resolve().parents[3]


def descubrir(patron, base):
    clases = []
    for archivo in sorted((RAIZ / "src/modules").glob(patron)):
        modulo = import_module(".".join(archivo.relative_to(RAIZ).with_suffix("").parts))
        clases.extend(c for _, c in inspect.getmembers(modulo, inspect.isclass)
                      if c.__module__ == modulo.__name__ and issubclass(c, base))
    assert clases
    return clases


ENUMS = descubrir("*/domain/enums/*.py", Enum)
ERRORES = descubrir("*/domain/exceptions/*.py", DomainException)


@pytest.mark.parametrize("clase", ENUMS, ids=lambda c: c.__name__)
@pytest.mark.parametrize("invalido", ["ESTADO_INEXISTENTE", ""])
def test_enums_rechazan_valores_desconocidos_y_exponen_opciones(clase, invalido):
    with pytest.raises(ValueError):
        clase(invalido)
    opciones = clase.opciones()
    assert len(opciones) == len(clase)
    assert len({clave for clave, _ in opciones}) == len(clase)
    for clave, etiqueta in opciones:
        assert clase(clave).value == clave
        assert isinstance(etiqueta, str) and etiqueta.strip()


@pytest.mark.parametrize("clase", ERRORES, ids=lambda c: c.__name__)
@pytest.mark.parametrize("muestra", ["recurso-1", "recurso-ñ-2"])
def test_errores_conservan_mensaje_y_codigo_publico(clase, muestra):
    argumentos = {}
    for nombre, parametro in inspect.signature(clase).parameters.items():
        if parametro.default is not inspect.Parameter.empty:
            continue
        argumentos[nombre] = {"disponible": 1, "requerido": 2, "faltante": 0.01}.get(nombre, muestra)
    error = clase(**argumentos)
    assert isinstance(error, DomainException)
    assert re.fullmatch(r"[A-Z][A-Z0-9_]+", error.codigo)
    assert str(error) == error.mensaje
    assert error.mensaje.strip()
    if muestra in argumentos.values():
        assert muestra in str(error)
