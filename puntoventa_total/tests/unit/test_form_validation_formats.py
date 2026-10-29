import importlib
import inspect
from pathlib import Path

import pytest
from django import forms

from src.modules.customers.presentation.forms.perfil_cliente_form import PerfilClienteForm
from src.modules.customers.presentation.forms.registro_cliente_form import RegistroClienteForm
from src.modules.orders.presentation.forms.pedido_form import PedidoForm
from src.shared.infrastructure.form_validation import ValidatedForm


@pytest.mark.parametrize("form_class,field", [
    (PerfilClienteForm, "telefono"), (RegistroClienteForm, "telefono"),
    (PedidoForm, "cliente_telefono"),
])
@pytest.mark.parametrize("value,valid", [
    ("+51987654321", True), ("987654321", True), ("", True),
    ("123456", False), ("1234567890123456", False), ("987ABC321", False),
    ("++51987654321", False), ("٩٨٧٦٥٤٣٢١", False),
])
def test_phone_consistent_across_forms(form_class, field, value, valid):
    form = form_class({"nombre": "María O’Connor", "cliente_nombre": "María O’Connor", field: value})
    form.is_valid()
    assert (field not in form.errors) == valid
    assert form.fields[field].widget.attrs["maxlength"] == 16
    assert "pattern" in form.fields[field].widget.attrs


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
