"""Carga datos iniciales: categorias, productos, usuarios y una venta de prueba.

Uso: python scripts/seed_data.py
"""
import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django  # noqa: E402

django.setup()

from src.modules.catalog.application.dto.producto_input import ProductoInputDTO  # noqa: E402
from src.modules.catalog.application.use_cases.crear_producto import CrearProducto  # noqa: E402
from src.modules.catalog.application.use_cases.crear_categoria import CrearCategoria  # noqa: E402
from src.modules.catalog.infrastructure.factories import (  # noqa: E402
    construir_categoria_repository,
    construir_producto_repository,
)
from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO  # noqa: E402
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario  # noqa: E402
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio  # noqa: E402

CATEGORIAS = ["Bebidas", "Abarrotes", "Lacteos", "Snacks", "Limpieza"]

PRODUCTOS = [
    ("Arroz Integral 1kg", "7751234000011", "Abarrotes", 4.50, 7.90),
    ("Azucar Rubia 1kg", "7751234000028", "Abarrotes", 3.80, 6.50),
    ("Gaseosa 500ml", "7751234000035", "Bebidas", 1.50, 3.00),
    ("Leche Entera 1L", "7751234000042", "Lacteos", 3.20, 5.50),
    ("Papa Frita 150g", "7751234000059", "Snacks", 4.00, 7.50),
    ("Detergente 1L", "7751234000066", "Limpieza", 6.00, 11.90),
]

USUARIOS = [
    ("admin", "Administrador General", "ADMINISTRADOR"),
    ("gerente", "Gerente de Tienda", "GERENTE"),
    ("cajero1", "Cajero Uno", "CAJERO"),
    ("almacen1", "Almacenero Uno", "ALMACENERO"),
]


def main() -> None:
    repo_cat = construir_categoria_repository()
    categorias = {}
    for nombre in CATEGORIAS:
        if not repo_cat.listar() or nombre not in [c.nombre for c in repo_cat.listar()]:
            dto = CrearCategoria(repo_cat).ejecutar(nombre, f"Categoria {nombre}")
            categorias[nombre] = dto.id
        else:
            categorias[nombre] = next(c.id for c in repo_cat.listar() if c.nombre == nombre)
    print(f"[ok] {len(categorias)} categorias")

    repo_prod = construir_producto_repository()
    creados = 0
    for nombre, codigo, categoria, costo, venta in PRODUCTOS:
        if repo_prod.buscar_por_codigo_barras(codigo):
            continue
        CrearProducto(repo_prod).ejecutar(
            ProductoInputDTO(
                nombre=nombre,
                descripcion=f"{nombre} - producto de demostracion",
                codigo_barras=codigo,
                costo=costo,
                precio_venta=venta,
                categoria_id=categorias.get(categoria),
            )
        )
        creados += 1
    print(f"[ok] {creados} productos")

    repo_user = construir_repositorio()
    hasher = construir_hasher()
    for username, nombre, rol in USUARIOS:
        if repo_user.buscar_por_username(username):
            continue
        CrearUsuario(repo_user, hasher).ejecutar(
            UsuarioInputDTO(username=username, password="Cambio1234!", nombre_completo=nombre, rol=rol)
        )
    print(f"[ok] {len(USUARIOS)} usuarios (password por defecto: Cambio1234!)")


if __name__ == "__main__":
    main()

