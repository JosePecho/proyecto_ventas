"""Consultas agregadas con ORM de Django (optimizadas con values/annotate)."""
from __future__ import annotations

from datetime import date
from typing import Sequence

from django.db.models import Count, Sum
from src.shared.infrastructure.database.date_bounds import date_bound

from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository


class DjangoReporteRepository(ReporteRepository):
    def _rango(self, desde: date, hasta: date):
        return date_bound(desde), date_bound(hasta, end=True)

    def ventas_por_dia(self, desde: date, hasta: date) -> Sequence[dict]:
        from django.db.models.functions import TruncDate

        from src.modules.sales.domain.enums.estado_venta import EstadoVenta
        from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel

        inicio, fin = self._rango(desde, hasta)
        filas = (
            VentaModel.objects.filter(estado=EstadoVenta.PAGADA.value, fecha_creacion__range=(inicio, fin))
            .annotate(dia=TruncDate("fecha_creacion"))
            .values("dia")
            .annotate(cantidad=Count("id"), total=Sum("total"), igv=Sum("igv"))
            .order_by("dia")
        )
        return [
            {"fecha": f["dia"].isoformat(), "cantidad": f["cantidad"], "total": float(f["total"] or 0), "igv": float(f["igv"] or 0)}
            for f in filas
        ]

    def productos_mas_vendidos(self, desde: date, hasta: date, limite: int = 10) -> Sequence[dict]:
        from src.modules.sales.domain.enums.estado_venta import EstadoVenta
        from src.modules.sales.infrastructure.persistence.django_models.detalle_venta_model import DetalleVentaModel

        inicio, fin = self._rango(desde, hasta)
        filas = (
            DetalleVentaModel.objects.filter(
                venta__estado=EstadoVenta.PAGADA.value, venta__fecha_creacion__range=(inicio, fin)
            )
            .values("producto_id", "producto_nombre")
            .annotate(unidades=Sum("cantidad"), ingresos=Sum("total"))
            .order_by("-ingresos")[:limite]
        )
        return [
            {
                "producto_id": str(f["producto_id"]),
                "producto_nombre": f["producto_nombre"],
                "unidades": f["unidades"],
                "ingresos": float(f["ingresos"] or 0),
            }
            for f in filas
        ]

    def utilidad_por_producto(self, desde: date, hasta: date) -> Sequence[dict]:
        from src.modules.sales.domain.enums.estado_venta import EstadoVenta
        from src.modules.sales.infrastructure.persistence.django_models.detalle_venta_model import DetalleVentaModel

        inicio, fin = self._rango(desde, hasta)
        filas = (
            DetalleVentaModel.objects.filter(
                venta__estado=EstadoVenta.PAGADA.value, venta__fecha_creacion__range=(inicio, fin)
            )
            .values("producto_id", "producto_nombre")
            .annotate(
                unidades=Sum("cantidad"),
                ingresos=Sum("total"),
            )
            .order_by("-ingresos")
        )
        from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel

        costos = {
            str(p.id): float(p.costo)
            for p in ProductoModel.objects.all().only("id", "costo")
        }
        resultado = []
        for f in filas:
            ingresos = float(f["ingresos"] or 0)
            costo = costos.get(str(f["producto_id"]), 0.0) * (f["unidades"] or 0)
            resultado.append(
                {
                    "producto_id": str(f["producto_id"]),
                    "producto_nombre": f["producto_nombre"],
                    "unidades": f["unidades"],
                    "ingresos": ingresos,
                    "costo": round(costo, 2),
                    "utilidad": round(ingresos - costo, 2),
                }
            )
        return resultado

    def rotacion_inventario(self, desde: date, hasta: date, dias_umbral: int = 60) -> Sequence[dict]:
        from src.modules.sales.infrastructure.persistence.django_models.detalle_venta_model import DetalleVentaModel

        inicio, fin = self._rango(desde, hasta)
        vendidos = {
            str(f["producto_id"])
            for f in DetalleVentaModel.objects.filter(venta__estado="PAGADA", venta__fecha_creacion__date__range=(desde, hasta))
            .values("producto_id")
            .distinct()
        }
        from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel

        return [
            {"producto_id": str(p.id), "producto_nombre": p.nombre, "ultimo_movimiento": "sin ventas recientes"}
            for p in ProductoModel.objects.filter(activo=True)
            if str(p.id) not in vendidos
        ]

    def resumen_stock(self) -> Sequence[dict]:
        from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
        from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel

        existencias = {str(e.producto_id): e.cantidad - e.reservada for e in ExistenciaModel.objects.all()}
        return [
            {
                "producto_id": str(p.id),
                "producto_nombre": p.nombre,
                "disponible": existencias.get(str(p.id), 0),
                "stock_minimo": p.stock_minimo,
                "valorizado": round(existencias.get(str(p.id), 0) * float(p.costo), 2),
            }
            for p in ProductoModel.objects.filter(activo=True)
        ]

    def productos_mayor_ganancia(self) -> Sequence[dict]:
        from decimal import Decimal
        from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
        resultado = []
        for p in ProductoModel.objects.filter(activo=True):
            ganancia = p.precio_venta - p.costo
            margen = ((ganancia / p.costo * 100) if p.costo else Decimal("100")).quantize(Decimal("0.01"))
            resultado.append({"producto_id": str(p.id), "producto_nombre": p.nombre,
                              "costo": p.costo, "precio_venta": p.precio_venta,
                              "ganancia_unitaria": ganancia, "margen_pct": margen})
        return sorted(resultado, key=lambda p: (-p["margen_pct"], -p["ganancia_unitaria"], p["producto_nombre"]))

    def totales_por_metodo_pago(self, desde: date, hasta: date) -> dict:
        from src.modules.sales.domain.enums.estado_venta import EstadoVenta
        from src.modules.sales.infrastructure.persistence.django_models.pago_model import PagoModel

        inicio, fin = self._rango(desde, hasta)
        filas = (
            PagoModel.objects.filter(venta__estado=EstadoVenta.PAGADA.value, venta__fecha_creacion__range=(inicio, fin))
            .values("metodo")
            .annotate(total=Sum("monto"))
        )
        return {f["metodo"]: float(f["total"] or 0) for f in filas}

