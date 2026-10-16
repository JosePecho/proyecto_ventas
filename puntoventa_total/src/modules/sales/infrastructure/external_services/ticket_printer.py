"""Emision de tickets en PDF (reportlab) 80mm."""
from __future__ import annotations

import io
from typing import Sequence

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from src.modules.sales.application.ports.ticket_port import TicketPort

# Papel termico estandar de 80mm (ancho) x 297mm (alto continuo)
TICKET_80MM = (80 * mm, 297 * mm)


class TicketPrinter(TicketPort):
    ANCHO, ALTO = TICKET_80MM

    def emitir(self, venta: dict, lineas: Sequence[dict], pagos: Sequence[dict]) -> bytes:
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=TICKET_80MM)
        pdf.setTitle(f"Ticket {venta['numero_ticket']}")

        y = self.ALTO - 12 * mm
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(5 * mm, y, "PUNTOVENTA TOTAL")
        y -= 5 * mm
        pdf.setFont("Helvetica", 8)
        pdf.drawString(5 * mm, y, f"Ticket N: {venta['numero_ticket']}")
        y -= 4 * mm
        pdf.drawString(5 * mm, y, f"Fecha: {venta['fecha'][:19].replace('T', ' ')}")
        y -= 6 * mm

        for linea in lineas:
            pdf.drawString(5 * mm, y, f"{linea['nombre'][:24]}")
            pdf.drawRightString(self.ANCHO - 5 * mm, y, f"x{linea['cantidad']}")
            y -= 3.5 * mm
            pdf.drawString(8 * mm, y, f"@ {linea['precio_unitario']:.2f}")
            pdf.drawRightString(self.ANCHO - 5 * mm, y, f"{linea['total']:.2f}")
            y -= 4 * mm

        y -= 2 * mm
        pdf.line(5 * mm, y, self.ANCHO - 5 * mm, y)
        y -= 5 * mm
        for etiqueta, valor in (
            ("Subtotal", venta["subtotal"]),
            ("Descuento", venta["descuento"]),
            ("IGV 18%", venta["igv"]),
        ):
            pdf.drawString(5 * mm, y, etiqueta)
            pdf.drawRightString(self.ANCHO - 5 * mm, y, f"{valor:.2f}")
            y -= 4 * mm
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(5 * mm, y, "TOTAL")
        pdf.drawRightString(self.ANCHO - 5 * mm, y, f"{venta['total']:.2f} {venta['moneda']}")
        y -= 6 * mm

        pdf.setFont("Helvetica", 8)
        for pago in pagos:
            pdf.drawString(5 * mm, y, f"Pago {pago['metodo']}: {pago['monto']:.2f}")
            if pago.get("vuelto"):
                y -= 3.5 * mm
                pdf.drawString(5 * mm, y, f"Vuelto: {pago['vuelto']:.2f}")
            y -= 3.5 * mm

        pdf.showPage()
        pdf.save()
        return buffer.getvalue()

    def nombre_archivo(self, numero_ticket: str) -> str:
        return f"ticket-{numero_ticket}.pdf"

