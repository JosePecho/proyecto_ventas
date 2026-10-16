from src.modules.reporting.application.ports.exportador_reporte_port import ExportadorReportePort
from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository
from src.modules.reporting.infrastructure.exporters.csv_exporter import CsvExporter
from src.modules.reporting.infrastructure.exporters.pdf_exporter import PdfExporter
from src.modules.reporting.infrastructure.persistence.repositories.django_reporte_repository import (
    DjangoReporteRepository,
)


def construir_reporte_repository() -> ReporteRepository:
    return DjangoReporteRepository()


def construir_exportador(formato: str = "csv") -> ExportadorReportePort:
    return PdfExporter() if formato == "pdf" else CsvExporter()

