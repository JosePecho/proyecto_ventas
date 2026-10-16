from src.modules.cash_register.domain.services.calculadora_arqueo import CalculadoraArqueo
from src.shared.domain.value_objects.monto import Monto


class CalcularDiferencia:
    """Validacion previa al cierre (el cajero ve la diferencia en vivo)."""

    def ejecutar(self, monto_fisico: float, monto_sistema: float, moneda: str = "PEN") -> dict:
        diferencia = CalculadoraArqueo.diferencia(Monto(monto_fisico, moneda), Monto(monto_sistema, moneda))
        return {
            "diferencia": diferencia.a_float(),
            "congruente": CalculadoraArqueo.es_congruente(diferencia),
            "direccion": "SOBRANTE" if diferencia.valor > 0 else ("FALTANTE" if diferencia.valor < 0 else "EXACTO"),
        }

