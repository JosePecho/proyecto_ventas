from src.modules.catalog.application.dto.categoria_dto import CategoriaDTO
from src.modules.catalog.domain.entities.categoria import Categoria
from src.modules.catalog.domain.repositories.categoria_repository import CategoriaRepository


class CrearCategoria:
    def __init__(self, repo: CategoriaRepository):
        self._repo = repo

    def ejecutar(self, nombre: str, descripcion: str = "", orden: int = 0) -> CategoriaDTO:
        categoria = Categoria(nombre=nombre, descripcion=descripcion, orden=orden)
        self._repo.guardar(categoria)
        return CategoriaDTO.desde_entidad(categoria)

