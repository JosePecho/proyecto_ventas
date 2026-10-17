from src.modules.reporting.application.dto.utilidad_reporte_dto import UtilidadReporteDTO
from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository
from src.modules.reporting.domain.value_objects.rango_fechas import RangoFechas
from decimal import Decimal, ROUND_HALF_UP


class ReporteUtilidad:
    def __init__(self, repo: ReporteRepository):
        self._repo = repo

    def ejecutar(self, desde, hasta) -> UtilidadReporteDTO:
        rango = RangoFechas(desde=desde, hasta=hasta)
        filas = self._repo.utilidad_por_producto(rango.desde, rango.hasta)
        ingresos = sum((Decimal(str(f["ingresos"])) for f in filas), Decimal(0))
        costos = sum((Decimal(str(f["costo"])) for f in filas), Decimal(0))
        utilidad = ingresos - costos
        return UtilidadReporteDTO(
            estimado=any(f.get("estimado", False) for f in filas),
            desde=rango.desde.isoformat(),
            hasta=rango.hasta.isoformat(),
            por_producto=list(filas),
            ingresos_totales=float(ingresos),
            costos_totales=float(costos),
            utilidad_total=float(utilidad),
            margen_pct=float((utilidad / ingresos * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) if ingresos else 0.0,
        )

