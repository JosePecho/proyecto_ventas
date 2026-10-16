import uuid

from src.modules.catalog.domain.entities.categoria import Categoria
from src.modules.catalog.infrastructure.persistence.django_models.categoria_model import CategoriaModel


class CategoriaMapper:
    @staticmethod
    def a_dominio(m: CategoriaModel) -> Categoria:
        return Categoria(
            id=m.id, nombre=m.nombre, slug=m.slug, descripcion=m.descripcion,
            orden=m.orden, activo=m.activo,
            fecha_creacion=m.fecha_creacion, fecha_actualizacion=m.fecha_actualizacion,
        )

    @staticmethod
    def a_modelo(e: Categoria, m: CategoriaModel | None = None) -> CategoriaModel:
        m = m or CategoriaModel(id=e.id)
        m.id = e.id if isinstance(e.id, uuid.UUID) else uuid.UUID(str(e.id))
        m.nombre, m.slug, m.descripcion, m.orden, m.activo = (
            e.nombre, e.slug, e.descripcion, e.orden, e.activo,
        )
        return m

