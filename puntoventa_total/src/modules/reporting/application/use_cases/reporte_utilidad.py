from src.modules.reporting.application.dto.utilidad_reporte_dto import UtilidadReporteDTO
from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository
from src.modules.reporting.domain.value_objects.rango_fechas import RangoFechas


class ReporteUtilidad:
    def __init__(self, repo: ReporteRepository):
        self._repo = repo

    def ejecutar(self, desde, hasta) -> UtilidadReporteDTO:
        rango = RangoFechas(desde=desde, hasta=hasta)
        filas = self._repo.utilidad_por_producto(rango.desde, rango.hasta)
        ingresos = float(sum((f["ingresos"] for f in filas), 0))
        costos = float(sum((f["costo"] for f in filas), 0))
        utilidad = ingresos - costos
        return UtilidadReporteDTO(
            desde=rango.desde.isoformat(),
            hasta=rango.hasta.isoformat(),
            por_producto=list(filas),
            ingresos_totales=ingresos,
            costos_totales=costos,
            utilidad_total=utilidad,
            margen_pct=round((utilidad / ingresos * 100), 2) if ingresos else 0.0,
        )

