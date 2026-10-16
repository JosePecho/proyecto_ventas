from src.modules.sales.application.ports.ticket_port import TicketPort
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.shared.application.exceptions.application_exception import NotFoundException


class EmitirTicket:
    def __init__(self, repo: VentaRepository, impresora: TicketPort):
        self._repo = repo
        self._impresora = impresora

    def ejecutar(self, venta_id: str) -> dict:
        agregado = self._repo.buscar_por_id(venta_id)
        if agregado is None:
            raise NotFoundException(f"Venta {venta_id} no existe")

        venta = {
            "numero_ticket": agregado.venta.numero_ticket,
            "fecha": agregado.venta.fecha_creacion.isoformat(),
            "estado": agregado.venta.estado.value,
            "subtotal": agregado.venta.subtotal,
            "descuento": agregado.venta.descuento,
            "igv": agregado.venta.igv,
            "total": agregado.venta.total,
            "moneda": agregado.venta.moneda,
        }
        pagos = [
            {"metodo": p.metodo.tipo, "monto": p.monto.a_float(), "vuelto": p.vuelto.a_float() if p.vuelto else None}
            for p in agregado.pagos
        ]
        contenido = self._impresora.emitir(venta, agregado.resumen_lineas(), pagos)
        return {
            "contenido": contenido,
            "nombre_archivo": self._impresora.nombre_archivo(agregado.venta.numero_ticket),
        }

