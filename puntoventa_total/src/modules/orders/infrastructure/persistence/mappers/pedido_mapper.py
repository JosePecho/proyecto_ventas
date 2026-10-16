import uuid
from decimal import Decimal

from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate
from src.modules.orders.domain.entities.detalle_pedido import DetallePedido
from src.modules.orders.domain.entities.pedido import Pedido
from src.modules.orders.domain.enums.estado_pedido import EstadoPedido
from src.modules.orders.infrastructure.persistence.django_models.detalle_pedido_model import DetallePedidoModel
from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
from src.shared.domain.value_objects.dni import DNI
from src.shared.domain.value_objects.monto import Monto


class PedidoMapper:
    @staticmethod
    def agregado_a_dominio(m: PedidoModel) -> PedidoAggregate:
        pedido = Pedido(
            id=m.id,
            numero=m.numero,
            cliente_id=str(m.cliente_id) if m.cliente_id else None,
            cliente_nombre=m.cliente_nombre,
            cliente_dni=DNI(m.cliente_dni) if m.cliente_dni else None,
            cliente_telefono=m.cliente_telefono,
            estado=EstadoPedido(m.estado),
            total=float(m.total),
            moneda=m.moneda,
            hora_recojo=m.hora_recojo,
            observaciones=m.observaciones,
            activo=m.activo,
            fecha_creacion=m.fecha_creacion,
            fecha_actualizacion=m.fecha_actualizacion,
        )
        lineas = [
            DetallePedido(
                id=d.id,
                pedido_id=str(m.id),
                producto_id=str(d.producto_id),
                producto_nombre=d.producto_nombre,
                cantidad=d.cantidad,
                precio_unitario=Monto(Decimal(d.precio_unitario), m.moneda),
                subtotal=Monto(Decimal(d.subtotal), m.moneda),
                fecha_creacion=d.fecha_creacion,
            )
            for d in m.detalles.all()
        ]
        return PedidoAggregate(pedido=pedido, lineas=lineas)

    @staticmethod
    def guardar_agregado(agregado: PedidoAggregate) -> PedidoModel:
        p = agregado.pedido
        modelo = PedidoModel.objects.filter(pk=p.id).first() or PedidoModel(id=p.id)
        modelo.id = p.id if isinstance(p.id, uuid.UUID) else uuid.UUID(str(p.id))
        modelo.numero = p.numero
        modelo.cliente_id = uuid.UUID(str(p.cliente_id)) if p.cliente_id else None
        modelo.cliente_nombre = p.cliente_nombre
        modelo.cliente_dni = str(p.cliente_dni) if p.cliente_dni else ""
        modelo.cliente_telefono = p.cliente_telefono
        modelo.estado = p.estado.value
        modelo.total = p.total
        modelo.moneda = p.moneda
        modelo.hora_recojo = p.hora_recojo
        modelo.observaciones = p.observaciones
        modelo.activo = p.activo
        modelo.save()

        for linea in agregado.lineas:
            d = DetallePedidoModel.objects.filter(pk=linea.id).first() or DetallePedidoModel(id=linea.id)
            d.id = linea.id if isinstance(linea.id, uuid.UUID) else uuid.UUID(str(linea.id))
            d.pedido = modelo
            d.producto_id = uuid.UUID(str(linea.producto_id))
            d.producto_nombre = linea.producto_nombre
            d.cantidad = linea.cantidad
            d.precio_unitario = linea.precio_unitario.valor
            d.subtotal = linea.subtotal.valor
            d.save()
        return modelo

