from src.modules.cash_register.application.dto.arqueo_dto import ArqueoDTO
from src.modules.cash_register.application.ports.ventas_turno_port import VentasTurnoPort
from src.modules.cash_register.domain.exceptions.caja_exceptions import TurnoNoEncontrado
from src.modules.cash_register.domain.repositories.turno_repository import TurnoRepository
from src.modules.cash_register.domain.services.calculadora_arqueo import CalculadoraArqueo


class ConsultarArqueo:
    def __init__(self, repo: TurnoRepository, ventas: VentasTurnoPort):
        self._repo = repo
        self._ventas = ventas

    def ejecutar(self, turno_id: str) -> ArqueoDTO:
        turno = self._repo.buscar_por_id(turno_id)
        if turno is None:
            raise TurnoNoEncontrado(turno_id)

        movimientos = self._repo.movimientos_del_turno(turno_id)
        ingresos = CalculadoraArqueo.ingresos(movimientos)
        egresos = CalculadoraArqueo.egresos(movimientos)
        saldo = CalculadoraArqueo.saldo_sistema(turno.monto_apertura, movimientos)
        fisico = turno.monto_cierre or saldo
        diferencia = CalculadoraArqueo.diferencia(fisico, saldo)

        return ArqueoDTO(
            turno_id=str(turno.id),
            monto_apertura=turno.monto_apertura.a_float(),
            ingresos=ingresos.a_float(),
            egresos=egresos.a_float(),
            saldo_sistema=saldo.a_float(),
            monto_fisico=fisico.a_float(),
            diferencia=diferencia.a_float(),
            congruente=CalculadoraArqueo.es_congruente(diferencia),
            ventas_total=self._ventas.total_ventas(turno_id),
            ventas_cantidad=self._ventas.contar_ventas(turno_id),
            desglose_metodos=CalculadoraArqueo.desglose_por_metodo(list(self._ventas.pagos_del_turno(turno_id))),
        )

