"""Entrega SMTP por socket real hacia un servidor local de pruebas."""
import django
from email.parser import BytesParser
from socketserver import StreamRequestHandler, ThreadingTCPServer
from threading import Thread

import pytest

from src.modules.orders.infrastructure.notifications.email_notifier import EmailNotifier

pytestmark = pytest.mark.integration


class SMTPHandler(StreamRequestHandler):
    def handle(self):
        self.wfile.write(b"220 localhost QA SMTP\r\n")
        recipients = []
        while line := self.rfile.readline():
            command = line.split(b" ", 1)[0].strip().upper()
            if command == b"QUIT":
                self.wfile.write(b"221 Bye\r\n")
                return
            if command == b"RCPT":
                recipients.append(line.decode().strip())
            if command == b"DATA":
                self.wfile.write(b"354 End with dot\r\n")
                data = []
                while (part := self.rfile.readline()) not in (b".\r\n", b""):
                    data.append(part[1:] if part.startswith(b"..") else part)
                self.server.messages.append((recipients[:], b"".join(data)))
            self.wfile.write(b"250 OK\r\n")


@pytest.mark.django_db
@pytest.mark.parametrize("via", ["notificador", "tarea"])
def test_email_pedido_se_entrega_por_smtp_al_cliente(settings, via):
    with ThreadingTCPServer(("127.0.0.1", 0), SMTPHandler) as server:
        server.messages = []
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            if django.VERSION >= (6, 1):
                settings.MAILERS = {"default": {"BACKEND": "django.core.mail.backends.smtp.EmailBackend",
                    "OPTIONS": {"host": host, "port": port, "timeout": 5, "username": "", "password": ""}}}
            else:
                settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
                settings.EMAIL_HOST = host
                settings.EMAIL_PORT = port
                settings.EMAIL_HOST_USER = ""
                settings.EMAIL_HOST_PASSWORD = ""
                settings.EMAIL_USE_TLS = False
                settings.EMAIL_USE_SSL = False
                settings.EMAIL_TIMEOUT = 5
            if via == "notificador":
                assert EmailNotifier().notificar_pedido_listo("Ana", "ana@example.test", "P-SMTP-QA")
            else:
                from uuid import uuid4
                from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
                from src.modules.orders.infrastructure.tasks.enviar_notificacion_pedido import run
                pedido = PedidoModel.objects.create(id=uuid4(), numero="P-SMTP-QA", cliente_nombre="Ana",
                                                     cliente_email="ana@example.test", estado="LISTO")
                assert run(str(pedido.id)) is True
                pedido.refresh_from_db()
                assert pedido.notificado_listo
                assert run(str(pedido.id)) is True
            assert len(server.messages) == 1
            recipients, raw = server.messages[0]
            assert [r.lower() for r in recipients] == ["rcpt to:<ana@example.test>"]
            message = BytesParser().parsebytes(raw)
            assert message["To"] == "ana@example.test"
            assert "P-SMTP-QA" in message["Subject"]
        finally:
            server.shutdown()
            thread.join(timeout=5)
