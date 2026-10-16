from abc import ABC, abstractmethod
from typing import Optional, Sequence

from src.modules.promotions.domain.entities.promocion import Promocion


class PromocionRepository(ABC):
    @abstractmethod
    def buscar_por_id(self, promocion_id) -> Optional[Promocion]:
        ...

    @abstractmethod
    def listar(self, incluir_finalizadas: bool = False) -> Sequence[Promocion]:
        ...

    @abstractmethod
    def listar_activas(self) -> Sequence[Promocion]:
        ...

    @abstractmethod
    def activa_para_producto(self, producto_id: str) -> Optional[Promocion]:
        ...

    @abstractmethod
    def guardar(self, promocion: Promocion) -> Promocion:
        ...

