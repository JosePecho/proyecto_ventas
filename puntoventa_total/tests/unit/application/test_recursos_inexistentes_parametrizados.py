"""Un recurso ausente debe producir el error del modulo sin escribir ni emitir efectos."""
from importlib import import_module
from unittest.mock import Mock, call

import pytest

from src.modules.cash_register.domain.exceptions.caja_exceptions import TurnoNoEncontrado
from src.modules.catalog.application.dto.producto_input import ActualizarProductoDTO
from src.modules.catalog.domain.exceptions.producto_exceptions import (
    CategoriaNoEncontrada,
    ProductoNoEncontrado,
)
from src.modules.customers.application.dto.cliente_input import ActualizarClienteDTO
from src.modules.customers.domain.exceptions.cliente_exceptions import ClienteNoEncontrado
from src.modules.identity.application.dto.usuario_input import ActualizarUsuarioDTO
from src.modules.identity.domain.exceptions.usuario_exceptions import UsuarioNoEncontrado
from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoNoEncontrado
from src.modules.promotions.domain.exceptions.promocion_exceptions import PromocionNoEncontrada
from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada
from src.shared.application.exceptions.application_exception import NotFoundException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit

# modulo, archivo/clase, dependencias adicionales, metodo, argumentos posteriores al id,
# envoltorio DTO (si corresponde), error. Los repositorios usan su interfaz real como spec.
CASOS = [
    ("catalog", "actualizar_categoria.ActualizarCategoria", [], "ejecutar", (), None, CategoriaNoEncontrada),
    ("catalog", "actualizar_producto.ActualizarProducto", [], "ejecutar", (), ActualizarProductoDTO, ProductoNoEncontrado),
    ("catalog", "descontinuar_producto.DescontinuarProducto", [], "ejecutar", (), None, ProductoNoEncontrado),
    ("catalog", "consultar_disponibilidad.ConsultarDisponibilidad", ["puerto"], "ejecutar", (), None, ProductoNoEncontrado),
    ("identity", "actualizar_usuario.ActualizarUsuario", ["hasher"], "ejecutar", (), ActualizarUsuarioDTO, UsuarioNoEncontrado),
    ("identity", "asignar_rol.AsignarRol", [], "ejecutar", ("CAJERO", True), None, UsuarioNoEncontrado),
    ("identity", "desactivar_usuario.DesactivarUsuario", [], "ejecutar", (), None, UsuarioNoEncontrado),
    ("identity", "verificar_permisos.VerificarPermisos", [], "ejecutar", (), None, UsuarioNoEncontrado),
    ("customers", "actualizar_cliente.ActualizarCliente", [], "ejecutar", (), ActualizarClienteDTO, ClienteNoEncontrado),
    ("customers", "consultar_cliente.ConsultarCliente", [], "por_id", (), None, ClienteNoEncontrado),
    ("customers", "consultar_historial_compras.ConsultarHistorialCompras", ["historial"], "ejecutar", (), None, ClienteNoEncontrado),
    ("customers", "eliminar_datos_cliente.EliminarDatosCliente", [], "ejecutar", (), None, ClienteNoEncontrado),
    ("sales", "anular_venta.AnularVenta", ["inventario", "auditoria"], "ejecutar", ("Motivo", "u1"), None, VentaNoEncontrada),
    ("sales", "aplicar_promocion.AplicarPromocion", ["promociones"], "ejecutar", (), None, VentaNoEncontrada),
    ("sales", "calcular_total.CalcularTotal", [], "ejecutar", (), None, VentaNoEncontrada),
    ("sales", "cerrar_venta.CerrarVenta", [], "ejecutar", (), None, VentaNoEncontrada),
    ("sales", "eliminar_producto.EliminarProducto", [], "ejecutar", ("p1",), None, VentaNoEncontrada),
    ("sales", "emitir_ticket.EmitirTicket", ["impresora"], "ejecutar", (), None, NotFoundException),
    ("sales", "modificar_cantidad.ModificarCantidad", [], "ejecutar", ("p1", 1), None, VentaNoEncontrada),
    ("sales", "preparar_beneficios.PrepararBeneficiosVenta", ["promociones"], "ejecutar", (), None, VentaNoEncontrada),
    ("sales", "procesar_pago.ProcesarPago", ["inventario", "auditoria"], "ejecutar", (), lambda id: ProcesarPagoDTO(id, "EFECTIVO", 10), VentaNoEncontrada),
    ("orders", "cancelar_pedido.CancelarPedido", ["inventario"], "ejecutar", (), None, PedidoNoEncontrado),
    ("orders", "confirmar_pedido.ConfirmarPedido", ["inventario"], "ejecutar", (), None, PedidoNoEncontrado),
    ("orders", "entregar_pedido.EntregarPedido", ["inventario"], "ejecutar", (), None, PedidoNoEncontrado),
    ("orders", "marcar_pedido_listo.MarcarPedidoListo", [], "ejecutar", (), None, PedidoNoEncontrado),
    ("orders", "preparar_pedido.PrepararPedido", [], "ejecutar", (), None, PedidoNoEncontrado),
    ("orders", "seleccionar_hora_recojo.SeleccionarHoraRecojo", [], "ejecutar", ("2030-01-01T12:00:00+00:00",), None, PedidoNoEncontrado),
    ("promotions", "activar_promocion.ActivarPromocion", [], "ejecutar", (), None, PromocionNoEncontrada),
    ("promotions", "actualizar_promocion.ActualizarPromocion", [], "ejecutar", (), None, PromocionNoEncontrada),
    ("promotions", "calcular_descuento.CalcularDescuento", [], "ejecutar", (Monto(10),), None, PromocionNoEncontrada),
    ("promotions", "cancelar_promocion.CancelarPromocion", [], "ejecutar", (), None, PromocionNoEncontrada),
    ("promotions", "programar_vigencia.ProgramarVigencia", [], "ejecutar", ("2030-01-01T12:00:00", "2030-01-02T12:00:00"), None, PromocionNoEncontrada),
    ("cash_register", "cerrar_turno.CerrarTurno", ["ventas"], "ejecutar", (100, "u1"), None, TurnoNoEncontrado),
    ("cash_register", "consultar_arqueo.ConsultarArqueo", ["ventas"], "ejecutar", (), None, TurnoNoEncontrado),
    ("cash_register", "registrar_movimiento.RegistrarMovimiento", [], "ejecutar", ("DEPOSITO", 10, "u1"), None, TurnoNoEncontrado),
]

REPOS = {
    "catalog": ("producto_repository.ProductoRepository", "categoria_repository.CategoriaRepository"),
    "identity": ("usuario_repository.UsuarioRepository",),
    "customers": ("cliente_repository.ClienteRepository",),
    "sales": ("venta_repository.VentaRepository",),
    "orders": ("pedido_repository.PedidoRepository",),
    "promotions": ("promocion_repository.PromocionRepository",),
    "cash_register": ("turno_repository.TurnoRepository",),
}


def cargar(ruta):
    modulo, nombre = ruta.rsplit(".", 1)
    return getattr(import_module(modulo), nombre)


@pytest.mark.parametrize("caso", CASOS, ids=[f"{c[0]}.{c[1].split('.')[-1]}" for c in CASOS])
@pytest.mark.parametrize("identificador", ["inexistente", "00000000-0000-0000-0000-000000000000", "otro-id"])
def test_recurso_ausente_no_produce_efectos(caso, identificador):
    modulo, ruta, dependencias, metodo, extras, dto, error = caso
    interfaz = REPOS[modulo][1 if "Categoria" in ruta else 0]
    repo = Mock(spec=cargar(f"src.modules.{modulo}.domain.repositories.{interfaz}"))
    repo.buscar_por_id.return_value = None
    puertos = {nombre: Mock(name=nombre) for nombre in dependencias}
    clase = cargar(f"src.modules.{modulo}.application.use_cases.{ruta}")
    servicio = clase(repo, **puertos)
    argumento = dto(identificador) if dto else identificador

    with pytest.raises(error):
        getattr(servicio, metodo)(argumento, *extras)

    repo.buscar_por_id.assert_called_once_with(identificador)
    assert repo.mock_calls == [call.buscar_por_id(identificador)]
    for puerto in puertos.values():
        assert puerto.mock_calls == [], f"Efecto externo inesperado: {puerto.mock_calls}"
