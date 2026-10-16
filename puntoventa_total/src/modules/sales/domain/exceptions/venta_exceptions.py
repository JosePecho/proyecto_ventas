from src.shared.domain.exceptions.domain_exception import DomainException


class VentaException(DomainException):
    codigo = "VENTA_INVALIDA"


class VentaNoEncontrada(VentaException):
    codigo = "VENTA_NO_ENCONTRADA"

    def __init__(self, venta_id):
        super().__init__(f"Venta no encontrada: {venta_id}")


class VentaNoModificable(VentaException):
    codigo = "VENTA_NO_MODIFICABLE"

    def __init__(self, estado: str):
        super().__init__(f"La venta en estado {estado} no admite modificaciones")


class ProductoYaAgregado(VentaException):
    codigo = "PRODUCTO_YA_AGREGADO"

    def __init__(self, nombre: str):
        super().__init__(f"'{nombre}' ya esta en la venta; modifique la cantidad")


class PagoInsuficiente(VentaException):
    codigo = "PAGO_INSUFICIENTE"

    def __init__(self, faltante: float):
        self.faltante = faltante
        super().__init__(f"El pago no cubre el total (faltan {faltante})")


class CajaNoAbierta(VentaException):
    codigo = "CAJA_NO_ABIERTA"

    def __init__(self):
        super().__init__("Debe abrir caja antes de registrar ventas")

