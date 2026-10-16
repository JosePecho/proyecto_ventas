from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from django.core.cache import cache

from src.modules.orders.infrastructure.notifications.email_notifier import EmailNotifier
from src.modules.orders.infrastructure.notifications.sms_notifier import SmsNotifier
from src.shared.infrastructure.cache.redis_cache import cache_resultado
from src.shared.infrastructure.database.date_bounds import date_bound

pytestmark = pytest.mark.integration


def test_cache_no_mezcla_terminos_posicionales_ni_emite_claves_invalidas():
    cache.clear()
    llamadas = []

    @cache_resultado(prefijo="qa:terminos")
    def buscar(termino, limite=5):
        llamadas.append(termino)
        return f"{termino}:{limite}"

    assert buscar("arroz", limite=5) == "arroz:5"
    assert buscar("pan", limite=5) == "pan:5"
    assert buscar("arroz", limite=5) == "arroz:5"
    assert llamadas == ["arroz", "pan"]
    cache.clear()


def test_email_notifica_al_destinatario_y_no_al_remitente(mailoutbox):
    assert EmailNotifier().notificar_pedido_listo("Ana", "ana@example.test", "P001")
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["ana@example.test"]
    assert "P001" in mailoutbox[0].subject


def test_sms_sin_proveedor_no_declara_entrega_ni_expone_pii(caplog):
    assert not SmsNotifier().notificar_pedido_listo("Ana", "999888777", "P001")
    assert "999888777" not in caplog.text
    assert "P001" not in caplog.text


def test_alerta_email_fallida_se_registra_sin_ocultar_confirmacion(caplog):
    from src.modules.inventory.infrastructure.notifications.stock_email_notifier import StockEmailNotifier

    with patch("src.modules.inventory.infrastructure.notifications.stock_email_notifier.send_mail", side_effect=OSError("QA")):
        StockEmailNotifier().notificar_stock_minimo("producto", 1, 5)
    assert "No se pudo enviar la alerta" in caplog.text


def test_limites_de_dia_lima_y_datetime_conservado(settings):
    settings.TIME_ZONE = "America/Lima"
    inicio = date_bound(date(2026, 10, 16))
    fin = date_bound(date(2026, 10, 16), end=True)
    assert inicio.utcoffset() == timedelta(hours=-5)
    assert (inicio.hour, fin.hour, fin.minute) == (0, 23, 59)
    instante = datetime(2026, 10, 16, 12, tzinfo=timezone.utc)
    assert date_bound(instante) == instante
