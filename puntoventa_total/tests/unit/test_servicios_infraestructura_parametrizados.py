"""Notificaciones locales, exportaciones, autenticacion y logs sin servicios externos."""
import csv
import io
import json
import logging

import pytest

from src.modules.identity.infrastructure.security.django_auth_adapter import DjangoAuthAdapter
from src.modules.orders.infrastructure.notifications.email_notifier import EmailNotifier
from src.modules.orders.infrastructure.notifications.sms_notifier import SmsNotifier
from src.modules.reporting.infrastructure.exporters.csv_exporter import CsvExporter
from src.modules.reporting.infrastructure.exporters.pdf_exporter import PdfExporter
from src.modules.sales.infrastructure.external_services.ticket_printer import TicketPrinter
from src.shared.infrastructure.logging.json_logger import JsonFormatter

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("password", ["clave con espacios ñ", "Clave-larga-2026!"])
def test_adaptador_auth_verifica_hash_y_rechaza_otra_clave(password):
    adaptador = DjangoAuthAdapter()
    clave_hash = adaptador.hash(password)
    assert clave_hash != password
    assert adaptador.verificar(password, clave_hash)
    assert not adaptador.verificar(password + "x", clave_hash)


@pytest.mark.parametrize("metodo,extra", [
    ("notificar_pedido_confirmado", ()), ("notificar_pedido_listo", ()),
    ("notificar_pedido_cancelado", ("Sin stock",)),
])
@pytest.mark.parametrize("destino", ["", "ana@example.test"])
def test_email_local_no_finge_envio_sin_destino(metodo, extra, destino, mailoutbox):
    resultado = getattr(EmailNotifier(), metodo)("Ana", destino, "P1", *extra)
    assert resultado is bool(destino)
    assert len(mailoutbox) == (1 if destino else 0)
    if destino:
        assert mailoutbox[0].to == [destino]
        assert "P1" in mailoutbox[0].subject
        assert "Ana" in mailoutbox[0].body


@pytest.mark.parametrize("metodo,extra", [
    ("notificar_pedido_confirmado", ()), ("notificar_pedido_listo", ()),
    ("notificar_pedido_cancelado", ("Sin stock",)),
])
@pytest.mark.parametrize("telefono", ["", "987654321"])
def test_sms_sin_proveedor_no_finge_entrega(metodo, extra, telefono, caplog):
    assert getattr(SmsNotifier(), metodo)("Ana", telefono, "P1", *extra) is False
    assert telefono == "" or telefono not in caplog.text


@pytest.mark.parametrize("filas", [[], [["María", "uno,dos"], ['Texto "citado"', "línea\nnueva"]]])
def test_csv_se_puede_leer_sin_perder_unicode_o_separadores(filas):
    resultado = CsvExporter().exportar(["Nombre", "Detalle"], filas, "reporte")
    leido = list(csv.reader(io.StringIO(resultado["contenido"].decode("utf-8-sig"))))
    assert leido == [["Nombre", "Detalle"], *filas]
    assert resultado["nombre_archivo"] == "reporte.csv"
    assert resultado["contenido"].startswith(b"\xef\xbb\xbf")


@pytest.mark.parametrize("filas", [[], [["Agua", 2], ["Pan", 1]]])
def test_pdf_genera_documento_completo(filas):
    resultado = PdfExporter().exportar(["Producto", "Cantidad"], filas, "reporte")
    assert resultado["contenido"].startswith(b"%PDF-")
    assert resultado["contenido"].rstrip().endswith(b"%%EOF")
    assert resultado["content_type"] == "application/pdf"
    assert resultado["nombre_archivo"] == "reporte.pdf"


@pytest.mark.parametrize("cantidad", [1, 2])
@pytest.mark.parametrize("vuelto", [0, 5])
def test_ticket_genera_pdf_con_pago(cantidad, vuelto):
    venta = {"numero_ticket": "T1", "fecha": "2026-10-30T12:00:00", "subtotal": 10 * cantidad,
             "descuento": 0, "igv": 1.53, "total": 10 * cantidad, "moneda": "PEN"}
    contenido = TicketPrinter().emitir(venta, [{"nombre": "Agua", "cantidad": cantidad, "precio_unitario": 10,
                                               "total": 10 * cantidad}], [{"metodo": "EFECTIVO", "monto": 10 * cantidad, "vuelto": vuelto}])
    assert contenido.startswith(b"%PDF-")
    assert contenido.rstrip().endswith(b"%%EOF")
    assert TicketPrinter().nombre_archivo("T1") == "ticket-T1.pdf"


@pytest.mark.parametrize("nivel", [logging.INFO, logging.ERROR])
@pytest.mark.parametrize("usuario", [None, "usuario-ñ"])
def test_log_json_conserva_mensaje_y_omite_nulos(nivel, usuario):
    registro = logging.LogRecord("prueba", nivel, __file__, 1, "Operación %s", ("válida",), None)
    registro.usuario = usuario
    datos = json.loads(JsonFormatter().format(registro))
    assert datos["mensaje"] == "Operación válida"
    assert datos["nivel"] == logging.getLevelName(nivel)
    assert "transaccion" not in datos
    assert datos.get("usuario") == usuario


@pytest.mark.parametrize("accion", ["CREAR", "ACTUALIZAR"])
def test_audit_logger_escribe_en_directorio_temporal(accion, tmp_path, settings):
    from src.modules.auditing.infrastructure.logging.audit_logger import AuditLogger

    settings.BASE_DIR = tmp_path
    logger = logging.getLogger(AuditLogger.NOMBRE)
    anteriores = logger.handlers[:]
    nivel, propagar = logger.level, logger.propagate
    logger.handlers = []
    try:
        AuditLogger.registrar(accion, "Producto", "p1", "u1")
        assert f"{accion} | Producto:p1 | usuario=u1" in (tmp_path / "logs/auditoria.log").read_text(encoding="utf-8")
    finally:
        for handler in logger.handlers:
            handler.close()
        logger.handlers = anteriores
        logger.setLevel(nivel)
        logger.propagate = propagar


@pytest.mark.parametrize("metodo,args", [("notificar_stock_minimo", ("p1", 0, 5)), ("notificar_vencimiento", ("l1", "p1", 3))])
def test_alerta_stock_usa_correo_local(metodo, args, mailoutbox):
    from src.modules.inventory.infrastructure.notifications.stock_email_notifier import StockEmailNotifier

    getattr(StockEmailNotifier(), metodo)(*args)
    assert len(mailoutbox) == 1
    assert "p1" in mailoutbox[0].body
