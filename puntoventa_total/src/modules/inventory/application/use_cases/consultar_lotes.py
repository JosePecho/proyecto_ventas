from src.modules.inventory.application.dto.lote_dto import LoteDTO
from src.modules.inventory.domain.repositories.lote_repository import LoteRepository


class ConsultarLotes:
    def __init__(self, repo: LoteRepository):
        self._repo = repo

    def ejecutar(self, producto_id: str, solo_pendientes: bool = True) -> list[LoteDTO]:
        return [LoteDTO.desde_entidad(l) for l in self._repo.listar_por_producto(producto_id, solo_pendientes)]

    def ejecutar_vencidos(self) -> list[LoteDTO]:
        return [LoteDTO.desde_entidad(l) for l in self._repo.lotes_vencidos()]

