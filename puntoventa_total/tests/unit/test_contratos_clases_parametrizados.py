"""Matrices de formularios y eventos; descubrimiento independiente del cwd."""
import inspect
from dataclasses import FrozenInstanceError
from importlib import import_module
from pathlib import Path

import pytest
from django import forms
from django.core.exceptions import ValidationError

from src.shared.domain.events.domain_event import DomainEvent

RAIZ = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.unit


def clases_en(patron, base):
    resultado = []
    for archivo in sorted((RAIZ / "src").glob(patron)):
        modulo = import_module(".".join(archivo.relative_to(RAIZ).with_suffix("").parts))
        for _, clase in inspect.getmembers(modulo, inspect.isclass):
            if clase.__module__ == modulo.__name__ and issubclass(clase, base):
                resultado.append(clase)
    assert resultado, f"No se encontraron clases para {patron}"
    return resultado


FORMULARIOS = clases_en("modules/*/presentation/forms/*.py", forms.Form)
EVENTOS = [DomainEvent, *clases_en("modules/*/domain/events/*.py", DomainEvent)]
TEXTOS = [
    pytest.param(clase, nombre, id=f"{clase.__name__}.{nombre}")
    for clase in FORMULARIOS
    for nombre, campo in clase.base_fields.items()
    if isinstance(campo, forms.CharField) and not isinstance(campo, forms.ChoiceField)
    and not isinstance(campo.widget, forms.PasswordInput)
]


@pytest.fixture(autouse=True)
def opciones_catalogo(monkeypatch):
    from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel

    # Solo el catalogo de opciones de PromocionForm; no se simulan validadores.
    monkeypatch.setattr(ProductoModel.objects, "filter", lambda **kwargs: ProductoModel.objects.none())


@pytest.mark.parametrize("clase,nombre", TEXTOS)
@pytest.mark.parametrize("valor", ["texto\x00invalido", "texto\x01invalido", "texto\x7finvalido"])
def test_formularios_rechazan_controles(clase, nombre, valor):
    # field.clean ejercita validadores reales sin consultar ORM en clean_email/clean_dni.
    campo = clase().fields[nombre]
    with pytest.raises(ValidationError):
        campo.clean(valor)


@pytest.mark.parametrize("clase", FORMULARIOS, ids=lambda c: c.__name__)
def test_formularios_no_comparten_campos_entre_instancias(clase):
    primero, segundo = clase(), clase()
    assert primero.fields, f"{clase.__name__} no declara campos"
    nombre = next(iter(primero.fields))
    primero.fields[nombre].widget.attrs["data-test"] = "solo-primero"
    assert "data-test" not in segundo.fields[nombre].widget.attrs


@pytest.mark.parametrize("clase", EVENTOS, ids=lambda c: c.__name__)
@pytest.mark.parametrize("entidad", ["Producto", "Pedido", "Venta"])
def test_eventos_serializacion_e_identidad(clase, entidad):
    primero, segundo = clase(entidad=entidad), clase(entidad=entidad)
    serializado = primero.a_dict()
    assert serializado["evento_id"] == str(primero.evento_id)
    assert serializado["nombre"] == clase.__name__
    assert serializado["entidad"] == entidad
    assert serializado["fecha"]  # Contrato actual: fecha serializada como texto.
    assert primero.evento_id != segundo.evento_id
    assert primero.fecha.utcoffset().total_seconds() == 0
    with pytest.raises(FrozenInstanceError):
        primero.entidad = "Alterada"
