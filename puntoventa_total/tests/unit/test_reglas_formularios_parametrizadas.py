"""Reglas cruzadas de formularios: fechas, pagos, ajustes y contrasenas."""
from datetime import date, timedelta

import pytest

from src.modules.auditing.presentation.forms.filtro_auditoria_form import FiltroAuditoriaForm
from src.modules.identity.presentation.forms.usuario_form import UsuarioForm
from src.modules.inventory.presentation.forms.ajuste_stock_form import AjusteStockForm
from src.modules.reporting.presentation.forms.filtro_reporte_form import FiltroReporteForm
from src.modules.reporting.presentation.forms.rango_reporte_form import RangoReporteForm
from src.modules.sales.presentation.forms.pago_form import PagoForm

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("clase", [FiltroAuditoriaForm, RangoReporteForm])
@pytest.mark.parametrize("desde,hasta,valido", [("2026-10-01", "2026-10-30", True), ("2026-10-30", "2026-10-30", True), ("2026-10-30", "2026-10-01", False)])
def test_formularios_rangos_fechas(clase, desde, hasta, valido):
    assert clase({"desde": desde, "hasta": hasta}).is_valid() is valido


@pytest.mark.parametrize("rango", ["hoy", "7", "30", "mes", "personalizado"])
def test_filtro_reporte_produce_rango_inclusivo(rango):
    form = FiltroReporteForm({"rango": rango, "desde": "2026-10-01", "hasta": "2026-10-30"})
    resultado = form.limpiar_a_rango()
    if rango == "personalizado":
        assert resultado.desde == date(2026, 10, 1)
        assert resultado.hasta == date(2026, 10, 30)
    elif rango in ("7", "30"):
        assert resultado.hasta - resultado.desde == timedelta(days=int(rango))
    elif rango == "hoy":
        assert resultado.desde == resultado.hasta == date.today()
    else:
        assert resultado.desde.day == 1
        assert resultado.desde.month == resultado.hasta.month


@pytest.mark.parametrize("tipo,signo", [("AJUSTE_POSITIVO", 1), ("AJUSTE_NEGATIVO", -1)])
@pytest.mark.parametrize("cantidad", [1, 2, 100])
def test_ajuste_stock_conserva_signo(tipo, signo, cantidad):
    form = AjusteStockForm({"producto_id": "00000000-0000-0000-0000-000000000001", "tipo": tipo, "cantidad": cantidad})
    assert form.is_valid(), form.errors
    assert form.a_diferencia() == cantidad * signo


@pytest.mark.parametrize("metodo,entregado,referencia,valido", [
    ("EFECTIVO", 10, "", True), ("EFECTIVO", 9, "", False),
    ("EFECTIVO", 20, "", True), ("YAPE", None, "ref-1", True),
    ("YAPE", None, "", False), ("TARJETA", None, "ref-1", True),
])
def test_formulario_pago_valida_efectivo_y_referencia(metodo, entregado, referencia, valido):
    datos = {"metodo": metodo, "monto": 10, "referencia": referencia}
    if entregado is not None:
        datos["monto_entregado"] = entregado
    assert PagoForm(datos).is_valid() is valido


@pytest.mark.parametrize("password,valido", [("123", False), ("12345678", False), ("Frase-Compleja!2026-X", True)])
def test_usuario_form_valida_password_real(password, valido):
    form = UsuarioForm({"username": "ana1", "nombre_completo": "Ana", "rol": "CAJERO", "password": password})
    assert form.is_valid() is valido
    if valido:
        assert form.cleaned_data["password"] == password
