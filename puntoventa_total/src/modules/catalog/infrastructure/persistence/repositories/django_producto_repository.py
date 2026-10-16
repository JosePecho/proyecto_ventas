from __future__ import annotations

from typing import Optional, Sequence

from django.db import IntegrityError
from django.db.models import Q

from src.modules.catalog.domain.entities.producto import Producto
from src.modules.catalog.domain.exceptions.producto_exceptions import CodigoBarrasDuplicado
from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository
from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
from src.modules.catalog.infrastructure.persistence.mappers.producto_mapper import ProductoMapper


class DjangoProductoRepository(ProductoRepository):
    def __init__(self):
        self._mapper = ProductoMapper()

    def _queryset(self, incluir_inactivos: bool, termino: str | None, categoria_id: str | None):
        qs = ProductoModel.objects.select_related("categoria").all()
        if not incluir_inactivos:
            qs = qs.filter(activo=True, estado="ACTIVO")
        if termino:
            qs = qs.filter(Q(nombre__icontains=termino) | Q(descripcion__icontains=termino))
        if categoria_id:
            qs = qs.filter(categoria_id=categoria_id)
        return qs

    def buscar_por_id(self, producto_id) -> Optional[Producto]:
        m = ProductoModel.objects.filter(pk=producto_id).select_related("categoria").first()
        return self._mapper.a_dominio(m) if m else None

    def buscar_por_codigo_barras(self, codigo: str) -> Optional[Producto]:
        m = ProductoModel.objects.filter(codigo_barras=codigo).first()
        return self._mapper.a_dominio(m) if m else None

    def listar(self, incluir_inactivos=False, termino=None, categoria_id=None, limit=None) -> Sequence[Producto]:
        qs = self._queryset(incluir_inactivos, termino, categoria_id)
        if limit:
            qs = qs[:limit]
        return [self._mapper.a_dominio(m) for m in qs]

    def contar(self, incluir_inactivos=False, termino=None, categoria_id=None) -> int:
        return self._queryset(incluir_inactivos, termino, categoria_id).count()

    def guardar(self, producto: Producto) -> Producto:
        modelo = ProductoModel.objects.filter(pk=producto.id).first()
        modelo = self._mapper.a_modelo(producto, modelo)
        try:
            modelo.save()
        except IntegrityError as exc:
            raise CodigoBarrasDuplicado(str(producto.codigo_barras)) from exc
        return producto

    def existe_codigo_barras(self, codigo: str, excluir_id=None) -> bool:
        qs = ProductoModel.objects.filter(codigo_barras=codigo)
        if excluir_id:
            qs = qs.exclude(pk=excluir_id)
        return qs.exists()

