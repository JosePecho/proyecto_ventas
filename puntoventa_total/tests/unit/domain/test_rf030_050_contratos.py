"""Oráculos explícitos de estados y fronteras temporales RF-035/036/042."""
from datetime import datetime, timedelta, timezone
from itertools import product

import pytest

from src.modules.orders.domain.entities.pedido import Pedido
from src.modules.orders.domain.enums.estado_pedido import EstadoPedido
from src.modules.orders.domain.exceptions.pedido_exceptions import TransicionInvalida
from src.modules.promotions.domain.entities.promocion import Promocion
from src.modules.promotions.domain.enums.estado_promocion import EstadoPromocion
from src.modules.promotions.domain.exceptions.promocion_exceptions import PromocionException

pytestmark = pytest.mark.unit

# Contrato de negocio: BORRADOR es el carrito; CONFIRMADO se presenta como Pendiente.
TRANSICIONES = {
    ("BORRADOR", "CONFIRMADO"), ("BORRADOR", "CANCELADO"),
    ("CONFIRMADO", "EN_PREPARACION"), ("CONFIRMADO", "CANCELADO"),
    ("EN_PREPARACION", "LISTO"), ("LISTO", "ENTREGADO"),
}


@pytest.mark.parametrize("origen,destino", list(product(EstadoPedido, repeat=2)))
def test_matriz_completa_de_transiciones_del_pedido(origen, destino):
    pedido = Pedido(cliente_nombre="Cliente contrato", estado=origen)
    if (origen.value, destino.value) in TRANSICIONES:
        pedido.transicionar_a(destino)
        assert pedido.estado == destino
    else:
        with pytest.raises(TransicionInvalida):
            pedido.transicionar_a(destino)
        assert pedido.estado == origen


@pytest.mark.parametrize("estado", list(EstadoPromocion))
@pytest.mark.parametrize("offset,vigente", [(-1, False), (0, True), (59, True), (60, False)])
def test_vigencia_inicio_inclusivo_fin_exclusivo(estado, offset, vigente):
    inicio = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)
    promocion = Promocion(nombre="Frontera contractual", estado=estado,
                         vigencia_desde=inicio, vigencia_hasta=inicio + timedelta(seconds=60))
    assert promocion.esta_vigente(inicio + timedelta(seconds=offset)) is (
        vigente and estado == EstadoPromocion.ACTIVA
    )


@pytest.mark.parametrize("estado", [EstadoPromocion.FINALIZADA, EstadoPromocion.CANCELADA])
def test_promocion_terminal_no_se_reactiva(estado):
    promocion = Promocion(nombre="Terminal", estado=estado)
    with pytest.raises(PromocionException):
        promocion.activar()
    assert promocion.estado == estado
