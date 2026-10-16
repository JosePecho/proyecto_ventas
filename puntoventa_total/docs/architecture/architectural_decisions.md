# Decisiones arquitectonicas (ADR)

## ADR-001: Monolito modular sobre microservicios
**Estado**: aceptado. Una tienda de barrio no necesita la complejidad operativa de
microservicios; el monolito modular conserva la separacion sin el costo de red.

## ADR-002: Clean Architecture por modulo
**Estado**: aceptado. Reglas de negocio (margen minimo, PEPS, arqueo) deben sobrevivir a
cambios de framework y poder probarse sin base de datos.

## ADR-003: Agregados con entidades de dominio + mappers a Django ORM
**Estado**: aceptado. Se evita anemic modeling: los calculos viven en el agregado
(`VentaAggregate`, `PedidoAggregate`), el ORM solo persiste.

## ADR-004: Reserva de stock para pedidos web, descuento directo para POS
**Estado**: aceptado. El mostrador descuenta en el momento del cobro (velocidad); el
pedido web reserva con expiracion de 20 minutos para no perder ventas por exceso de stock.

## ADR-005: Kardex inmutable
**Estado**: aceptado. Los movimientos nunca se editan ni se borran; una anulacion genera
un movimiento compensatorio de tipo DEVOLUCION.

## ADR-006: Celery + Redis para tareas diferidas
**Estado**: aceptado. Alertas de stock, vencimientos, notificaciones de pedidos y
sincronizacion de promociones corren fuera del request.

## ADR-007: Soporte offline via IndexedDB + cola de sincronizacion
**Estado**: aceptado. El POS debe seguir vendiendo sin internet; la cola se sincroniza
por orden de fecha y resuelve conflictos por numero de ticket.

