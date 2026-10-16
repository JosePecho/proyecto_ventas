from src.modules.promotions.application.ports.frecuencia_cliente_port import FrecuenciaClientePort


class FrecuenciaClienteAdapter(FrecuenciaClientePort):
    def clasificacion(self, cliente_id: str) -> str:
        from src.modules.customers.application.use_cases.calcular_frecuencia_compras import CalcularFrecuenciaCompras
        from src.modules.customers.infrastructure.factories import construir_cliente_repository, construir_historial_port

        resultado = CalcularFrecuenciaCompras(construir_cliente_repository(), construir_historial_port()).ejecutar(
            cliente_id
        )
        return resultado["clasificacion"]

    def compras_previas(self, cliente_id: str) -> int:
        from src.modules.customers.application.ports.historial_compras_port import HistorialComprasPort
        from src.modules.customers.infrastructure.factories import construir_historial_port

        port: HistorialComprasPort = construir_historial_port()
        return len(port.compras_del_cliente(cliente_id))

