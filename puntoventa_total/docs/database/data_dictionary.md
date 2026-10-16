# Diccionario de datos (campos críticos)

| Tabla | Campo | Tipo | Descripcion |
|---|---|---|---|
| identity_usuario | rol | enum | ADMINISTRADOR, GERENTE, CAJERO, ALMACENERO, CLIENTE |
| identity_usuario | intentos_fallidos | smallint | Bloquea al llegar a 5 |
| catalog_producto | costo | decimal(12,2) | Costo de compra (base para margen y utilidad) |
| catalog_producto | precio_venta | decimal(12,2) | Precio final al cliente (incluye IGV) |
| inventory_existencia | cantidad | int | Stock fisico consolidado |
| inventory_existencia | reservada | int | Comprometido en reservas vivas (no puede superar cantidad) |
| inventory_lote | cantidad_restante | int | Disponible del lote; sustenta el plan PEPS |
| inventory_movimiento | tipo | enum | ENTRADA, SALIDA_VENTA, SALIDA_PEDIDO, AJUSTE_*, MERMA, DEVOLUCION |
| sales_venta | estado | enum | BORRADOR, PAGADA, ANULADA |
| sales_venta | igv | decimal(12,2) | IGV implicito (18%) desglosado para boleta |
| sales_pago | metodo | enum | EFECTIVO, TARJETA, YAPE, PLIN, TRANSFERENCIA |
| cash_turno_caja | diferencia | decimal(12,2) | fisico - sistema al cierre |
| orders_pedido | hora_recojo | datetime | Franjas cada 30 minutos |
| promotions_promocion | vigencia_hasta | datetime | Beat la finaliza automaticamente |
| auditing_registro | detalle | JSON | Contexto libre de la accion |

