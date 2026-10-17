"""Adaptador concreto del puerto DisponibilidadPort (anti-corruption layer)."""
from __future__ import annotations

from typing import Iterable

from src.modules.catalog.application.ports.disponibilidad_port import DisponibilidadPort


class DisponibilidadAdapter(DisponibilidadPort):
    """Traduce las consultas de stock a la API publica de inventory."""

    def stock_disponible(self, producto_id: str) -> int:
        from src.modules.inventory.application.use_cases.consultar_stock import ConsultarStock
        from src.modules.inventory.infrastructure.factories import construir_stock_repository

        return ConsultarStock(construir_stock_repository()).ejecutar(producto_id).disponible

    def stock_disponible_lote(self, producto_ids: Iterable[str]) -> dict[str, int]:
        from src.modules.inventory.infrastructure.factories import construir_stock_repository

        repo = construir_stock_repository()
        return repo.disponibles(producto_ids)

    def tiene_stock_minimo(self, producto_id: str) -> bool:
        from src.modules.inventory.domain.services.politica_stock import PoliticaStock
        from src.modules.inventory.infrastructure.factories import construir_stock_repository

        repo = construir_stock_repository()
        return repo.disponible(producto_id) <= PoliticaStock.umbral_minimo()

