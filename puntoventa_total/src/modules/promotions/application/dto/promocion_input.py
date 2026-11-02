from dataclasses import dataclass, field


@dataclass(frozen=True)
class PromocionInputDTO:
    nombre: str
    tipo: str
    descuento_valor: float
    producto_id: str | None = None
    categoria_id: str | None = None
    cantidad_requerida: int = 0
    cantidad_gratuita: int = 0
    vigencia_desde: str | None = None
    vigencia_hasta: str | None = None
    aplica_clientes_frecuentes: bool = False
    componentes: list[dict] = field(default_factory=list)

