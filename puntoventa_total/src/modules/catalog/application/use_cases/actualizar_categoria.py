from src.modules.catalog.application.dto.categoria_dto import CategoriaDTO
from src.modules.catalog.domain.exceptions.producto_exceptions import CategoriaNoEncontrada
from src.modules.catalog.domain.repositories.categoria_repository import CategoriaRepository


class ActualizarCategoria:
    def __init__(self, repo: CategoriaRepository):
        self._repo = repo

    def ejecutar(self, categoria_id: str, nombre: str | None = None, orden: int | None = None) -> CategoriaDTO:
        categoria = self._repo.buscar_por_id(categoria_id)
        if categoria is None:
            raise CategoriaNoEncontrada(categoria_id)
        if nombre:
            categoria.renombrar(nombre)
        if orden is not None:
            categoria.mover_a_posicion(orden)
        self._repo.guardar(categoria)
        return CategoriaDTO.desde_entidad(categoria)

