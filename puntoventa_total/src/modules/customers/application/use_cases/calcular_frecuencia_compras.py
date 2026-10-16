from src.modules.customers.application.ports.historial_compras_port import HistorialComprasPort
from src.modules.customers.domain.repositories.cliente_repository import ClienteRepository
from src.modules.customers.domain.services.frecuencia_compra import FrecuenciaCompra


class CalcularFrecuenciaCompras:
    def __init__(self, repo: ClienteRepository, historial: HistorialComprasPort):
        self._repo = repo
        self._historial = historial

    def ejecutar(self, cliente_id: str) -> dict:
        compras = self._historial.compras_del_cliente(cliente_id)
        fechas = [c["fecha"] for c in compras]
        dias = FrecuenciaCompra.dias_entre_compras(fechas)
        return {
            "cliente_id": cliente_id,
            "compras_totales": len(fechas),
            "dias_promedio_entre_compras": dias,
            "dias_desde_ultima_compra": FrecuenciaCompra.ultimo_intervalo(fechas),
            "clasificacion": FrecuenciaCompra.clasificar(dias),
        }

