from datetime import date, timedelta

from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository


class ReporteBajaRotacion:
    def __init__(self, repo: ReporteRepository):
        self._repo = repo

    def ejecutar(self, dias_umbral: int = 90) -> list[dict]:
        hasta = date.today()
        desde = hasta - timedelta(days=dias_umbral)
        return [dict(f) for f in self._repo.rotacion_inventario(desde, hasta, dias_umbral)]

