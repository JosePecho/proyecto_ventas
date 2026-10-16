from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository


class ReporteStockMinimo:
    def __init__(self, repo: ReporteRepository):
        self._repo = repo

    def ejecutar(self, umbral: int | None = None) -> dict:
        filas = [dict(f) for f in self._repo.resumen_stock()]
        bajos = [f for f in filas if f["disponible"] < (f.get("stock_minimo", 5) if umbral is None else umbral)]
        return {
            "umbral": umbral,
            "productos_bajo_minimo": bajos,
            "cantidad": len(bajos),
            "valorizado_total": float(sum(f.get("valorizado", 0) for f in filas)),
        }

