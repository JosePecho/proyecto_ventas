from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository
from src.modules.reporting.domain.value_objects.rango_fechas import RangoFechas


class ReporteMayorGanancia:
    def __init__(self, repo: ReporteRepository):
        self._repo = repo

    def por_margen(self) -> list[dict]:
        return list(self._repo.productos_mayor_ganancia())

    def ejecutar(self, desde, hasta, limite: int = 10) -> list[dict]:
        """Conserva el ranking de utilidad total del dashboard de ventas."""
        rango = RangoFechas(desde=desde, hasta=hasta)
        filas = [dict(f) for f in self._repo.utilidad_por_producto(rango.desde, rango.hasta)]
        filas.sort(key=lambda f: f["utilidad"], reverse=True)
        return filas[:limite]
