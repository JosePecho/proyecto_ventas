from abc import ABC, abstractmethod
from collections.abc import Sequence

from src.modules.promotions.domain.entities.promocion import Promocion


class PromocionRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, promocion_id) -> Promocion | None:
        ...

    @abstractmethod
    def listar(self, incluir_finalizadas: bool = False) -> Sequence[Promocion]:
        ...

    @abstractmethod
    def listar_activas(self) -> Sequence[Promocion]:
        ...

    @abstractmethod
    def activa_para_producto(self, producto_id: str) -> Promocion | None:
        ...

    @abstractmethod
    def guardar(self, promocion: Promocion) -> Promocion:
        ...

