from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository
from src.modules.reporting.domain.value_objects.rango_fechas import RangoFechas


class ReporteProductosMasVendidos:
    def __init__(self, repo: ReporteRepository):
        self._repo = repo

    def ejecutar(self, desde, hasta, limite: int = 10) -> list[dict]:
        rango = RangoFechas(desde=desde, hasta=hasta)
        return [dict(f) for f in self._repo.productos_mas_vendidos(rango.desde, rango.hasta, limite)]

