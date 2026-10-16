from src.modules.reporting.application.dto.ventas_reporte_dto import VentasReporteDTO
from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository
from src.modules.reporting.domain.value_objects.rango_fechas import RangoFechas


class ReporteVentasPorFecha:
    def __init__(self, repo: ReporteRepository):
        self._repo = repo

    def ejecutar(self, desde, hasta) -> VentasReporteDTO:
        rango = RangoFechas(desde=desde, hasta=hasta)
        filas = self._repo.ventas_por_dia(rango.desde, rango.hasta)
        return VentasReporteDTO(
            desde=rango.desde.isoformat(),
            hasta=rango.hasta.isoformat(),
            por_dia=list(filas),
            total_ventas=float(sum((f["total"] for f in filas), 0)),
            total_igv=float(sum((f.get("igv", 0) for f in filas), 0)),
            cantidad_tickets=int(sum((f["cantidad"] for f in filas), 0)),
        )

