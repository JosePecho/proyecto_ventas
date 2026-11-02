from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from src.modules.orders.presentation.forms.pedido_form import PedidoForm


@pytest.mark.unit
@pytest.mark.parametrize("hora,minuto,dia,siguiente_hora,siguiente_minuto", [
    (10, 12, 26, 10, 30),
    (10, 30, 26, 11, 0),
    (23, 59, 27, 0, 0),
])
def test_checkout_asigna_horario_sin_fecha_manual(hora, minuto, dia, siguiente_hora, siguiente_minuto):
    zona = ZoneInfo("America/Lima")
    ahora = datetime(2026, 10, 26, hora, minuto, tzinfo=zona)
    esperado = datetime(2026, 10, dia, siguiente_hora, siguiente_minuto, tzinfo=zona)
    with patch("src.modules.orders.presentation.forms.pedido_form.timezone.localtime", return_value=ahora), patch(
        "src.modules.orders.presentation.forms.pedido_form.timezone.now", return_value=ahora
    ):
        form = PedidoForm({"cliente_nombre": "Ana", "modalidad": "RECOJO"})
        assert form.is_valid(), form.errors
        assert form.cleaned_data["hora_recojo"] == esperado
        assert PedidoForm()["hora_recojo"].value() == esperado.replace(tzinfo=None)
