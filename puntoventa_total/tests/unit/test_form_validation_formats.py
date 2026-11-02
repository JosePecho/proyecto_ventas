import importlib
import inspect
from pathlib import Path

import pytest
from django import forms

from src.modules.customers.presentation.forms.perfil_cliente_form import PerfilClienteForm
from src.modules.customers.presentation.forms.registro_cliente_form import RegistroClienteForm
from src.modules.customers.presentation.forms.registro_web_form import RegistroWebForm
from src.modules.orders.presentation.forms.pedido_form import PedidoForm
from src.shared.infrastructure.form_validation import ValidatedForm


@pytest.mark.parametrize("dni,valid", [
    ("", True), ("12345678", True), ("+12345678", False),
    ("1234567", False), ("123456789", False),
])
def test_registro_cliente_conserva_dni_opcional(dni, valid):
    form = RegistroClienteForm({"nombre": "Cliente de prueba", "dni": dni})
    assert form.is_valid() == valid
    if valid:
        assert form.cleaned_data["dni"] == dni


@pytest.mark.parametrize("form_class,field", [
    (PerfilClienteForm, "telefono"), (RegistroClienteForm, "telefono"),
    (PedidoForm, "cliente_telefono"), (RegistroWebForm, "telefono"),
])
@pytest.mark.parametrize("value,valid", [
    ("+51987654321", False), ("987654321", True), ("", True),
    ("900000000", True), ("999999999", True),
    ("98765432", False), ("9876543210", False),
    ("123456789", False), ("887654321", False),
    ("987 654 321", False), ("987-654-321", False),
    ("123456", False), ("1234567890123456", False), ("987ABC321", False),
    ("++51987654321", False), ("٩٨٧٦٥٤٣٢١", False),
])
def test_phone_consistent_across_forms(form_class, field, value, valid):
    form = form_class({"nombre": "María O’Connor", "cliente_nombre": "María O’Connor", field: value})
    form.is_valid()
    esperado = valid and (bool(value) or not form.fields[field].required)
    assert (field not in form.errors) == esperado
    assert form.fields[field].widget.attrs["maxlength"] == 9
    assert form.fields[field].widget.attrs["minlength"] == 9
    assert form.fields[field].widget.attrs["pattern"] == r"9[0-9]{8}"
    assert "data-phone-peru" in form.fields[field].widget.attrs


@pytest.mark.parametrize("field,value,valid", [
    ("dni", "12345678", True), ("dni", "１２３４５６７８", False),
    ("dni", "1234567a", False), ("dni", "123456789", False),
    ("codigo_barras", "7751234567890", True), ("codigo_barras", "12345678", True),
    ("codigo_barras", "ABC12345", False), ("codigo_barras", "123456789", False),
])
def test_formats_on_server(field, value, valid):
    form_type = type("ExampleForm", (ValidatedForm,), {field: forms.CharField()})
    assert form_type({field: value}).is_valid() == valid


def test_text_and_password_are_preserved():
    class ExampleForm(ValidatedForm):
        nombre = forms.CharField()
        password = forms.CharField(widget=forms.PasswordInput)

    form = ExampleForm({"nombre": "María O’Connor 王", "password": " secret "})
    assert form.is_valid()
    assert form.cleaned_data["password"] == " secret "
    assert not ExampleForm({"nombre": "bad\x01text", "password": "secret"}).is_valid()


def test_every_declared_form_uses_shared_validation():
    for path in Path("src/modules").glob("*/presentation/forms/*.py"):
        module = importlib.import_module(".".join(path.with_suffix("").parts))
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ == module.__name__ and issubclass(cls, forms.Form):
                assert issubclass(cls, ValidatedForm), path
