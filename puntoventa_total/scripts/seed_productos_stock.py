"""Carga productos de demostracion con lotes, existencias y kardex reales.

Uso: python scripts/seed_productos_stock.py [--apply]
Sin --apply muestra el plan. Repetirlo no duplica lotes ni repone stock vendido.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.db import transaction  # noqa: E402

from src.modules.catalog.application.dto.producto_input import ProductoInputDTO  # noqa: E402
from src.modules.catalog.application.use_cases.crear_categoria import CrearCategoria  # noqa: E402
from src.modules.catalog.application.use_cases.crear_producto import CrearProducto  # noqa: E402
from src.modules.catalog.infrastructure.factories import construir_categoria_repository, construir_producto_repository  # noqa: E402
from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel  # noqa: E402
from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel  # noqa: E402
from src.modules.inventory.application.dto.lote_dto import RecepcionLoteDTO  # noqa: E402
from src.modules.inventory.application.use_cases.recibir_mercaderia import RecibirMercaderia  # noqa: E402
from src.modules.inventory.infrastructure.factories import (  # noqa: E402
    construir_lote_repository,
    construir_movimiento_repository,
    construir_stock_repository,
)
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import LoteModel  # noqa: E402
from src.modules.inventory.infrastructure.persistence.django_models.movimiento_model import MovimientoModel  # noqa: E402


# Nombre, categoria, costo PEN, venta PEN, cantidad inicial.
PRODUCTOS_NUEVOS = [
    ("Aceite Vegetal 1L", "Abarrotes", "6.50", "9.50", 36),
    ("Fideos Tallarin 500g", "Abarrotes", "2.20", "3.50", 60),
    ("Lentejas 500g", "Abarrotes", "3.00", "4.80", 45),
    ("Frejol Canario 500g", "Abarrotes", "3.80", "5.90", 40),
    ("Sal de Mesa 1kg", "Abarrotes", "1.00", "1.80", 80),
    ("Harina de Trigo 1kg", "Abarrotes", "3.00", "4.50", 50),
    ("Avena 500g", "Abarrotes", "2.80", "4.20", 40),
    ("Atun en Conserva 170g", "Abarrotes", "4.50", "6.80", 48),
    ("Agua Mineral 625ml", "Bebidas", "0.90", "1.80", 96),
    ("Agua Mineral 2.5L", "Bebidas", "2.00", "3.80", 40),
    ("Jugo de Naranja 1L", "Bebidas", "3.20", "5.00", 36),
    ("Bebida Rehidratante 500ml", "Bebidas", "2.30", "3.80", 30),
    ("Yogur de Fresa 1L", "Lacteos", "4.50", "6.80", 30),
    ("Leche Evaporada 400g", "Lacteos", "3.00", "4.50", 48),
    ("Queso Fresco 250g", "Lacteos", "5.00", "7.50", 24),
    ("Galletas de Vainilla Pack 6", "Snacks", "3.00", "4.80", 40),
    ("Galletas de Chocolate Pack 6", "Snacks", "3.50", "5.50", 40),
    ("Mani Tostado 100g", "Snacks", "1.80", "3.00", 36),
    ("Chocolate 50g", "Snacks", "2.00", "3.50", 30),
    ("Lavavajilla 500g", "Limpieza", "3.00", "4.80", 36),
    ("Lejia 1L", "Limpieza", "1.60", "2.80", 40),
    ("Papel Higienico Pack 4", "Higiene Personal", "4.50", "6.90", 32),
    ("Jabon de Tocador 90g", "Higiene Personal", "1.50", "2.50", 48),
    ("Pasta Dental 90g", "Higiene Personal", "3.20", "5.00", 36),
]


def codigo_interno(indice: int) -> str:
    base = str(200000100000 + indice)
    suma = sum(int(digit) * (3 if index % 2 else 1) for index, digit in enumerate(base))
    return base + str((10 - suma % 10) % 10)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    database = settings.DATABASES["default"]
    if database["ENGINE"] != "django.db.backends.mysql" or database["NAME"] != "punto_venta":
        raise RuntimeError("Esta carga requiere la base MySQL/MariaDB punto_venta configurada en .env")
    categoria_repo = construir_categoria_repository()
    producto_repo = construir_producto_repository()
    stock_repo = construir_stock_repository()
    recibir = RecibirMercaderia(stock_repo, construir_lote_repository(), construir_movimiento_repository())
    admin = UsuarioModel.objects.filter(username="admin").first()
    usuario_id = str(admin.pk) if admin else ""
    rows = []
    creados = entradas = unidades = 0
    with transaction.atomic():
        categorias = {categoria.nombre: categoria.id for categoria in categoria_repo.listar()}
        for index, (nombre, categoria, costo, venta, cantidad) in enumerate(PRODUCTOS_NUEVOS, 1):
            codigo = codigo_interno(index)
            existing = ProductoModel.objects.select_for_update().filter(codigo_barras=codigo).first()
            if existing and existing.nombre != nombre:
                raise RuntimeError(f"Codigo interno ocupado por otro producto: {codigo}")
            if not existing:
                creados += 1
                if args.apply:
                    if categoria not in categorias:
                        categorias[categoria] = CrearCategoria(categoria_repo).ejecutar(categoria).id
                    CrearProducto(producto_repo).ejecutar(ProductoInputDTO(
                        nombre=nombre, descripcion="Producto de demostracion para ventas e inventario.",
                        codigo_barras=codigo, costo=costo, precio_venta=venta,
                        categoria_id=categorias[categoria], stock_minimo=10,
                    ))
            producto = producto_repo.buscar_por_codigo_barras(codigo)
            lote_numero = f"INICIAL-DEMO-{codigo}"
            existe_lote = bool(producto and LoteModel.objects.filter(
                producto_id=producto.id, numero_lote=lote_numero).exists())
            tiene_historial = bool(producto and MovimientoModel.objects.filter(producto_id=producto.id).exists())
            existencia = stock_repo.obtener(producto.id) if producto else None
            tiene_lotes = bool(producto and LoteModel.objects.filter(producto_id=producto.id).exists())
            ingresar = (not existe_lote and not tiene_historial and not tiene_lotes
                        and (existencia is None or existencia.cantidad == 0))
            if ingresar:
                entradas += 1
                unidades += cantidad
                if args.apply:
                    recibir.ejecutar(RecepcionLoteDTO(
                        producto_id=producto.id, numero_lote=lote_numero,
                        cantidad=cantidad, costo_unitario=float(producto.precio.costo.valor),
                        proveedor="Carga inicial de demostracion",
                    ), usuario_id=usuario_id)
            disponible = stock_repo.disponible(producto.id) if producto else 0
            rows.append({"nombre": nombre, "codigo": codigo, "categoria": categoria,
                         "precio_venta": venta, "stock_disponible": disponible,
                         "ingreso": cantidad if ingresar else 0})
        # Los seis productos de la primera demostracion reciben stock solo si
        # no tienen movimientos previos; nunca se reponen automaticamente ventas.
        originales = [
            ("7751234000011", 80), ("7751234000028", 70), ("7751234000035", 96),
            ("7751234000042", 60), ("7751234000059", 45), ("7751234000066", 35),
        ]
        for codigo, cantidad in originales:
            original = ProductoModel.objects.select_for_update().filter(codigo_barras=codigo).first()
            if not original:
                continue
            producto = producto_repo.buscar_por_codigo_barras(codigo)
            lote_numero = f"INICIAL-DEMO-{codigo}"
            existencia = stock_repo.obtener(producto.id)
            ingresar = (not MovimientoModel.objects.filter(producto_id=producto.id).exists()
                        and not LoteModel.objects.filter(producto_id=producto.id).exists()
                        and (existencia is None or existencia.cantidad == 0))
            if ingresar:
                entradas += 1
                unidades += cantidad
                if args.apply:
                    recibir.ejecutar(RecepcionLoteDTO(
                        producto_id=producto.id, numero_lote=lote_numero,
                        cantidad=cantidad, costo_unitario=float(original.costo),
                        proveedor="Carga inicial de demostracion",
                    ), usuario_id=usuario_id)
            rows.append({"nombre": original.nombre, "codigo": codigo,
                         "categoria": original.categoria.nombre if original.categoria else "",
                         "precio_venta": str(original.precio_venta),
                         "stock_disponible": stock_repo.disponible(producto.id),
                         "ingreso": cantidad if ingresar else 0})
    summary = {"aplicado": args.apply, "database": database["NAME"], "port": database["PORT"],
               "productos_nuevos": creados, "entradas_stock": entradas,
               "unidades_ingresadas": unidades, "productos": rows}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.apply:
        reports = ROOT / "reports"
        reports.mkdir(exist_ok=True)
        (reports / "productos-stock-creados.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        with (reports / "productos-stock-creados.csv").open("w", newline="", encoding="utf-8-sig") as output:
            writer = csv.DictWriter(output, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
