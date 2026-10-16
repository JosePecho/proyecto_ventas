"""Ruta critica del POS: unico lookup indexado por codigo."""
from __future__ import annotations

from src.modules.catalog.application.dto.producto_output import ProductoOutputDTO
from src.modules.catalog.domain.entities.producto import Producto
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoNoEncontrado
from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository


class BuscarPorCodigoBarras:
    def __init__(self, repo: ProductoRepository):
        self._repo = repo

    def ejecutar(self, codigo: str) -> ProductoOutputDTO:
        producto = self.encontrar(codigo)
        return ProductoOutputDTO.desde_entidad(producto)

    def encontrar(self, codigo: str) -> Producto:
        producto = self._repo.buscar_por_codigo_barras(codigo.strip())
        if producto is None:
            raise ProductoNoEncontrado(codigo)
        producto.verificar_disponibilidad_venta()
        return producto

