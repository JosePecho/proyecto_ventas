from dataclasses import dataclass, field


@dataclass(frozen=True)
class ArqueoDTO:
    turno_id: str
    monto_apertura: float
    ingresos: float
    egresos: float
    saldo_sistema: float
    monto_fisico: float
    diferencia: float
    congruente: bool
    ventas_total: float
    ventas_cantidad: int
    desglose_metodos: dict = field(default_factory=dict)

