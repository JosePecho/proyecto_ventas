from datetime import datetime, timedelta, timezone

import pytest

from src.modules.cash_register.domain.entities.turno_caja import TurnoCaja
from src.modules.identity.domain.entities.usuario import Usuario
from src.modules.orders.domain.entities.pedido import Pedido
from src.modules.promotions.domain.entities.promocion import Promocion
from src.shared.domain.events.domain_event import DomainEvent
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def test_apertura_cierre_y_acceso_usan_fechas_aware():
    turno = TurnoCaja(cajero_id="cajero", monto_apertura=Monto(10))
    turno.registrar_cierre(Monto(10), Monto(10))
    usuario = Usuario(username="qa_hora", nombre_completo="QA")
    usuario.registrar_acceso_exitoso()
    for valor in (turno.fecha_apertura, turno.fecha_cierre, usuario.ultimo_acceso,
                  turno.fecha_creacion, turno.fecha_actualizacion, DomainEvent().fecha):
        assert valor.utcoffset() == timedelta(0)


@pytest.mark.parametrize("tz", [timezone.utc, timezone(timedelta(hours=-5)), None])
def test_recojo_y_promocion_aceptan_fechas_consistentes(tz):
    inicio = (datetime.now(tz) + timedelta(days=2)).replace(minute=30, second=0, microsecond=0)
    pedido = Pedido(cliente_nombre="Ana")
    pedido.asignar_hora_recojo(inicio)
    assert pedido.hora_recojo == inicio
    promocion = Promocion(nombre="Oferta QA")
    promocion.programar(inicio, inicio + timedelta(days=1))
    promocion.activar()
    assert not promocion.esta_vigente()
    assert promocion.esta_vigente(inicio + timedelta(hours=1))
