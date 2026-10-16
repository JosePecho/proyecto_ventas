from datetime import date

from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository


class ReporteVentasDiarias:
    def __init__(self, repo: ReporteRepository):
        self._repo = repo

    def ejecutar(self, dia: date | None = None) -> dict:
        dia = dia or date.today()
        filas = self._repo.ventas_por_dia(dia, dia)
        total = sum((f["total"] for f in filas), 0)
        return {
            "fecha": dia.isoformat(),
            "ventas": list(filas),
            "total": float(total),
            "tickets": sum((f["cantidad"] for f in filas), 0),
        }

