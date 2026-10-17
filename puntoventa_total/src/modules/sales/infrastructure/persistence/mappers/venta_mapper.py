"""Mapper completo del agregado Venta (venta + lineas + pagos)."""
import uuid
from decimal import Decimal

from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.detalle_venta import DetalleVenta
from src.modules.sales.domain.entities.pago import Pago
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.modules.sales.domain.value_objects.metodo_pago import MetodoPago
from src.modules.sales.infrastructure.persistence.django_models.detalle_venta_model import DetalleVentaModel
from src.modules.sales.infrastructure.persistence.django_models.pago_model import PagoModel
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.shared.domain.value_objects.monto import Monto


class VentaMapper:
    @staticmethod
    def venta_a_dominio(m: VentaModel) -> Venta:
        return Venta(
            id=m.id,
            numero_ticket=m.numero_ticket,
            cajero_id=str(m.cajero_id),
            turno_caja_id=str(m.turno_caja_id) if m.turno_caja_id else None,
            cliente_id=str(m.cliente_id) if m.cliente_id else None,
            estado=EstadoVenta(m.estado),
            subtotal=float(m.subtotal),
            descuento=float(m.descuento),
            total=float(m.total),
            igv=float(m.igv),
            moneda=m.moneda,
            observacion=m.observacion,
            activo=m.activo,
            fecha_creacion=m.fecha_creacion,
            fecha_actualizacion=m.fecha_actualizacion,
        )

    @staticmethod
    def agregado_a_dominio(m: VentaModel) -> VentaAggregate:
        venta = VentaMapper.venta_a_dominio(m)
        lineas = [
            DetalleVenta(
                id=d.id,
                venta_id=str(m.id),
                producto_id=str(d.producto_id),
                producto_nombre=d.producto_nombre,
                cantidad=d.cantidad,
                costo_unitario=Monto(d.costo_unitario, m.moneda) if d.costo_unitario is not None else None,
                precio_unitario=Monto(Decimal(d.precio_unitario), m.moneda),
                descuento=Monto(Decimal(d.descuento), m.moneda),
                pct_descuento=Decimal(d.pct_descuento),
                fecha_creacion=d.fecha_creacion,
            )
            for d in m.detalles.all()
        ]
        pagos = [
            Pago(
                id=p.id,
                venta_id=str(m.id),
                metodo=MetodoPago(
                    tipo=p.metodo,
                    monto=Monto(Decimal(p.monto), m.moneda),
                    referencia=p.referencia,
                ),
                vuelto=Monto(Decimal(p.vuelto), m.moneda) if p.vuelto is not None else None,
                fecha_creacion=p.fecha_creacion,
            )
            for p in m.pagos.all()
        ]
        return VentaAggregate(venta=venta, lineas=lineas, pagos=pagos, descuento_venta_pct=Decimal(m.descuento_venta_pct))

    @staticmethod
    def guardar_agregado(agregado: VentaAggregate) -> VentaModel:
        v = agregado.venta
        modelo = VentaModel.objects.filter(pk=v.id).first() or VentaModel(id=v.id)
        modelo.id = v.id if isinstance(v.id, uuid.UUID) else uuid.UUID(str(v.id))
        modelo.numero_ticket = v.numero_ticket
        modelo.cajero_id = uuid.UUID(str(v.cajero_id))
        modelo.turno_caja_id = uuid.UUID(str(v.turno_caja_id)) if v.turno_caja_id else None
        modelo.cliente_id = uuid.UUID(str(v.cliente_id)) if v.cliente_id else None
        modelo.estado = v.estado.value
        modelo.descuento_venta_pct = agregado.descuento_venta_pct
        modelo.subtotal, modelo.descuento, modelo.igv, modelo.total = v.subtotal, v.descuento, v.igv, v.total
        modelo.moneda, modelo.observacion, modelo.activo = v.moneda, v.observacion, v.activo
        modelo.save(force_insert=modelo._state.adding)

        detalles_existentes = {str(d.id): d for d in modelo.detalles.all()} if agregado.lineas else {}
        for linea in agregado.lineas:
            d = detalles_existentes.get(str(linea.id))
            costo = linea.costo_unitario.valor if linea.costo_unitario is not None else None
            if d is not None and (
                str(d.producto_id), d.producto_nombre, d.cantidad, d.precio_unitario, d.costo_unitario,
                d.pct_descuento, d.descuento, d.subtotal, d.total
            ) == (str(linea.producto_id), linea.producto_nombre, linea.cantidad, linea.precio_unitario.valor,
                  costo, linea.pct_descuento, linea.descuento.valor, linea.subtotal.valor, linea.total.valor):
                continue
            d = d or DetalleVentaModel(id=linea.id)
            d.id = linea.id if isinstance(linea.id, uuid.UUID) else uuid.UUID(str(linea.id))
            d.venta = modelo
            d.producto_id = uuid.UUID(str(linea.producto_id))
            d.producto_nombre = linea.producto_nombre
            d.cantidad = linea.cantidad
            d.costo_unitario = linea.costo_unitario.valor if linea.costo_unitario is not None else None
            d.precio_unitario = linea.precio_unitario.valor
            d.pct_descuento = linea.pct_descuento
            d.descuento = linea.descuento.valor
            d.subtotal = linea.subtotal.valor
            d.total = linea.total.valor
            d.save(force_insert=d._state.adding)

        pagos_existentes = {str(p.id): p for p in modelo.pagos.all()} if agregado.pagos else {}
        for pago in agregado.pagos:
            p = pagos_existentes.get(str(pago.id))
            vuelto = pago.vuelto.valor if pago.vuelto else None
            if p is not None and (p.metodo, p.monto, p.vuelto, p.referencia) == (
                pago.metodo.tipo, pago.metodo.monto.valor, vuelto, pago.metodo.referencia
            ):
                continue
            p = p or PagoModel(id=pago.id)
            p.id = pago.id if isinstance(pago.id, uuid.UUID) else uuid.UUID(str(pago.id))
            p.venta = modelo
            p.metodo = pago.metodo.tipo
            p.monto = pago.metodo.monto.valor
            p.vuelto = pago.vuelto.valor if pago.vuelto else None
            p.referencia = pago.metodo.referencia
            p.save(force_insert=p._state.adding)

        agregado.lineas_vinculadas = True  # marca interna para no reinsertar
        return modelo

