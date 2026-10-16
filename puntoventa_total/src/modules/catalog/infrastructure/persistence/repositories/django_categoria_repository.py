from typing import Optional, Sequence

from src.modules.catalog.domain.entities.categoria import Categoria
from src.modules.catalog.domain.repositories.categoria_repository import CategoriaRepository
from src.modules.catalog.infrastructure.persistence.django_models.categoria_model import CategoriaModel
from src.modules.catalog.infrastructure.persistence.mappers.categoria_mapper import CategoriaMapper


class DjangoCategoriaRepository(CategoriaRepository):
    def __init__(self):
        self._mapper = CategoriaMapper()

    def buscar_por_id(self, categoria_id) -> Optional[Categoria]:
        m = CategoriaModel.objects.filter(pk=categoria_id).first()
        return self._mapper.a_dominio(m) if m else None

    def buscar_por_slug(self, slug: str) -> Optional[Categoria]:
        m = CategoriaModel.objects.filter(slug=slug).first()
        return self._mapper.a_dominio(m) if m else None

    def listar(self, solo_activas: bool = True) -> Sequence[Categoria]:
        qs = CategoriaModel.objects.all()
        if solo_activas:
            qs = qs.filter(activo=True)
        return [self._mapper.a_dominio(m) for m in qs]

    def guardar(self, categoria: Categoria) -> Categoria:
        m = CategoriaModel.objects.filter(pk=categoria.id).first()
        self._mapper.a_modelo(categoria, m).save()
        return categoria

