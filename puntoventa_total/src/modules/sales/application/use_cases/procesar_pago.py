"""Cobro: valida importe, registra pago y descuenta stock en una sola transaccion."""
from __future__ import annotations

from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.ports.auditoria_port import AuditoriaPort
from src.modules.sales.application.ports.inventario_port import InventarioPort
from src.modules.sales.domain.entities.pago import Pago
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.modules.sales.domain.value_objects.metodo_pago import MetodoPago
from src.shared.application.interfaces.unit_of_work import NullUnitOfWork, UnitOfWork
from src.shared.domain.value_objects.monto import Monto


class ProcesarPago:
    def __init__(
        self,
        repo: VentaRepository,
        inventario: InventarioPort,
        auditoria: AuditoriaPort,
        uow: UnitOfWork | None = None,
        promociones=None,
    ):
        self._repo = repo
        self._inventario = inventario
        self._auditoria = auditoria
        self._uow = uow or NullUnitOfWork()
        self._promociones = promociones

    def ejecutar(self, datos: ProcesarPagoDTO) -> dict:
        with self._uow:
            agregado = self._repo.buscar_por_id(datos.venta_id)
            if agregado is None:
                from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada

                raise VentaNoEncontrada(datos.venta_id)

            agregado.venta.verificar_modificable()
            if self._promociones is not None:
                from src.modules.sales.application.use_cases.preparar_beneficios import PrepararBeneficiosVenta
                PrepararBeneficiosVenta(self._repo, self._promociones).aplicar(agregado)
            total_anterior = agregado.venta.total
            pago = Pago(
                venta_id=datos.venta_id,
                metodo=MetodoPago(
                    tipo=datos.metodo,
                    monto=Monto(datos.monto, agregado.venta.moneda),
                    referencia=datos.referencia,
                ),
                vuelto=Monto(datos.monto_entregado - datos.monto, agregado.venta.moneda)
                if datos.monto_entregado is not None and datos.metodo == "EFECTIVO"
                else None,
            )
            agregado.registrar_pago(pago)

            if agregado.saldo_pendiente() > 0:
                # pago parcial: solo guarda, no cierra
                self._repo.guardar(agregado)
                return {"estado": "PENDIENTE", "saldo": float(agregado.saldo_pendiente())}

            # descuento definitivo de stock (PEPS) por cada linea
            referencia = f"VENTA:{agregado.venta.numero_ticket}"
            for linea in agregado.lineas:
                if linea.cantidad > 0:
                    self._inventario.descontar(
                        linea.producto_id, linea.cantidad, referencia, agregado.venta.cajero_id
                    )

            agregado.cerrar()
            self._repo.guardar(agregado)

            self._auditoria.registrar(
                accion="VENTA_PAGADA",
                entidad="Venta",
                entidad_id=str(agregado.venta.id),
                usuario_id=agregado.venta.cajero_id,
                detalle={"total": total_anterior, "metodo": datos.metodo, "numero_ticket": agregado.venta.numero_ticket},
            )
            return {
                "estado": agregado.venta.estado.value,
                "total": agregado.venta.total,
                "vuelto": pago.vuelto.a_float() if pago.vuelto else 0.0,
                "numero_ticket": agregado.venta.numero_ticket,
            }

