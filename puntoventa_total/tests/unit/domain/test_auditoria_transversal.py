"""Reglas de clientes y reportes fuera del flujo principal del POS."""
from datetime import date, timedelta

import pytest

from src.modules.customers.domain.entities.cliente import Cliente
from src.modules.reporting.domain.value_objects.rango_fechas import RangoFechas
from src.shared.domain.exceptions.validation_exception import ValidationException

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("campo,valor", [("email", "sin-arroba"), ("telefono", "abc"), ("puntos_fidelidad", -1)])
def test_cliente_rechaza_datos_invalidos(campo, valor):
    with pytest.raises(ValidationException):
        Cliente(nombre="Ana", **{campo: valor})


def test_canje_descuenta_saldo_y_rechaza_exceso_sin_mutarlo():
    cliente = Cliente(nombre="Ana", puntos_fidelidad=20)
    cliente.canjear_puntos(15)
    assert cliente.puntos_fidelidad == 5
    with pytest.raises(ValidationException):
        cliente.canjear_puntos(6)
    assert cliente.puntos_fidelidad == 5


def test_anonimizar_elimina_contacto_y_desactiva_cliente():
    cliente = Cliente(nombre="Ana", email="ana@example.test", telefono="999888777", direccion="Local 1")
    cliente.anonimizar()
    assert cliente.nombre == "CLIENTE ELIMINADO"
    assert (cliente.email, cliente.telefono, cliente.direccion, cliente.dni) == ("", "", "", None)
    assert not cliente.activo


def test_rango_mes_bisiesto_incluye_29_febrero():
    rango = RangoFechas.del_mes(date(2024, 2, 15))
    assert rango.desde == date(2024, 2, 1)
    assert rango.hasta == date(2024, 2, 29)
    assert len(rango.en_dias()) == 29


@pytest.mark.parametrize("dias", [-1, 367])
def test_rango_rechaza_inversion_y_exceso(dias):
    inicio = date(2026, 1, 1)
    with pytest.raises(ValidationException):
        RangoFechas(inicio, inicio + timedelta(days=dias))
