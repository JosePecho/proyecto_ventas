from dataclasses import dataclass


@dataclass(frozen=True)
class CategoriaDTO:
    id: str
    nombre: str
    slug: str
    descripcion: str
    orden: int
    activo: bool

    @classmethod
    def desde_entidad(cls, categoria) -> "CategoriaDTO":
        return cls(
            id=str(categoria.id),
            nombre=categoria.nombre,
            slug=categoria.slug,
            descripcion=categoria.descripcion,
            orden=categoria.orden,
            activo=categoria.activo,
        )

