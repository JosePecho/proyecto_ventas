from typing import Optional, Sequence
from django.db import connection, transaction
from django.utils import timezone
from src.modules.sales.infrastructure.persistence.django_models.ticket_sequence_model import TicketSequenceModel
from src.shared.infrastructure.database.date_bounds import date_bound

from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.modules.sales.infrastructure.persistence.mappers.venta_mapper import VentaMapper


class DjangoVentaRepository(VentaRepository):
    def __init__(self):
        # Identidad ORM local a esta instancia de repositorio/unidad de trabajo.
        self._cargadas = {}

    def buscar_por_id(self, venta_id) -> Optional[VentaAggregate]:
        qs = VentaModel.objects.filter(pk=venta_id)
        if connection.in_atomic_block:
            qs = qs.select_for_update()
        m = qs.prefetch_related("detalles", "pagos").first()
        if m is not None:
            self._cargadas[str(m.pk)] = m
        return VentaMapper.agregado_a_dominio(m) if m else None

    def buscar_por_numero_ticket(self, numero_ticket: str) -> Optional[VentaAggregate]:
        m = (
            VentaModel.objects.filter(numero_ticket=numero_ticket)
            .prefetch_related("detalles", "pagos")
            .first()
        )
        return VentaMapper.agregado_a_dominio(m) if m else None

    def guardar(self, agregado: VentaAggregate) -> VentaAggregate:
        VentaMapper.guardar_agregado(agregado, self._cargadas.pop(str(agregado.venta.id), None))
        return agregado

    def listar_por_turno(self, turno_caja_id: str) -> Sequence[VentaAggregate]:
        qs = (
            VentaModel.objects.filter(turno_caja_id=turno_caja_id)
            .prefetch_related("detalles", "pagos")
            .order_by("fecha_creacion")
        )
        return [VentaMapper.agregado_a_dominio(m) for m in qs]

    def listar_por_fecha(self, desde, hasta) -> Sequence[VentaAggregate]:
        inicio = date_bound(desde)
        fin = date_bound(hasta, end=True)
        qs = (
            VentaModel.objects.filter(fecha_creacion__range=(inicio, fin))
            .prefetch_related("detalles", "pagos")
            .order_by("-fecha_creacion")
        )
        return [VentaMapper.agregado_a_dominio(m) for m in qs]

    def siguiente_numero_ticket(self) -> str:
        dia = timezone.localdate()
        prefijo = f"T{dia:%Y%m%d}"
        with transaction.atomic():
            if connection.vendor == "mysql":
                # El upsert toma bloqueo exclusivo sin la conversion shared->exclusive
                # de get_or_create, que puede causar deadlock en la primera reserva.
                tabla = connection.ops.quote_name(TicketSequenceModel._meta.db_table)
                with connection.cursor() as cursor:
                    cursor.execute(f"INSERT INTO {tabla} (dia, ultimo) VALUES (%s, 0) "
                                   "ON DUPLICATE KEY UPDATE ultimo=ultimo", [dia])
            else:
                TicketSequenceModel.objects.get_or_create(dia=dia)
            secuencia = TicketSequenceModel.objects.select_for_update().get(pk=dia)
            if secuencia.ultimo == 0:
                # Una instalacion existente puede tener tickets previos a la secuencia.
                anteriores = VentaModel.objects.filter(numero_ticket__startswith=prefijo).values_list("numero_ticket", flat=True)
                secuencia.ultimo = max((int(n[len(prefijo):]) for n in anteriores if n[len(prefijo):].isdigit()), default=0)
            secuencia.ultimo += 1
            secuencia.save(update_fields=["ultimo"])
            return f"{prefijo}{secuencia.ultimo:05d}"

