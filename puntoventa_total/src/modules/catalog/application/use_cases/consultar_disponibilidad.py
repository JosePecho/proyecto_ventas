"""Expone stock al catalogo/POS sin importar el modulo inventory."""
from __future__ import annotations

from src.modules.catalog.application.ports.disponibilidad_port import DisponibilidadPort
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoNoEncontrado
from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository


class ConsultarDisponibilidad:
    def __init__(self, repo: ProductoRepository, puerto: DisponibilidadPort):
        self._repo = repo
        self._puerto = puerto

    def ejecutar(self, producto_id: str) -> dict:
        producto = self._repo.buscar_por_id(producto_id)
        if producto is None:
            raise ProductoNoEncontrado(producto_id)
        stock = self._puerto.stock_disponible(str(producto.id))
        return {
            "producto_id": str(producto.id),
            "nombre": producto.nombre,
            "stock_disponible": stock,
            "vendible": producto.disponible_para_vender and (stock > 0 or not producto.requiere_stock),
            "stock_minimo": self._puerto.tiene_stock_minimo(str(producto.id)),
        }

