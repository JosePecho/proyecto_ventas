from src.modules.cash_register.application.dto.turno_dto import TurnoDTO
from src.modules.cash_register.domain.entities.turno_caja import TurnoCaja
from src.modules.cash_register.domain.exceptions.caja_exceptions import TurnoYaAbierto
from src.modules.cash_register.domain.repositories.turno_repository import TurnoRepository
from src.shared.domain.value_objects.monto import Monto


class AbrirTurno:
    def __init__(self, repo: TurnoRepository, moneda: str = "PEN"):
        self._repo = repo
        self._moneda = moneda

    def ejecutar(self, cajero_id: str, monto_apertura: float) -> TurnoDTO:
        if self._repo.buscar_abierto_por_cajero(cajero_id):
            raise TurnoYaAbierto(cajero_id)
        turno = TurnoCaja(cajero_id=cajero_id, monto_apertura=Monto(monto_apertura, self._moneda))
        self._repo.guardar(turno)
        return TurnoDTO.desde_entidad(turno)

