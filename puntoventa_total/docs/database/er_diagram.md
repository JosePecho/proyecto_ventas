# Diagrama entidad-relacion (resumen)

```
identity_usuario (id UUID PK, username UQ, password_hash, rol, estado, ...)
catalog_categoria (id UUID PK, nombre UQ, slug UQ, orden, ...)
catalog_producto (id UUID PK, codigo_barras UQ, nombre, costo, precio_venta,
                  categoria_id FK->catalog_categoria, estado, ...)

inventory_existencia (id UUID PK, producto_id UQ, cantidad, reservada)
inventory_lote (id UUID PK, producto_id, numero_lote, cantidad_inicial,
                cantidad_restante, costo_unitario, fecha_vencimiento, ...)
inventory_reserva (id UUID PK, producto_id, cantidad, referencia, expira_en,
                   confirmada, liberada)
inventory_movimiento (id UUID PK, producto_id, tipo, cantidad, stock_resultante,
                      referencia, lote_id, fecha)

sales_venta (id UUID PK, numero_ticket UQ, cajero_id, turno_caja_id, cliente_id,
             estado, subtotal, descuento, igv, total, ...)
sales_detalle_venta (id UUID PK, venta_id FK->sales_venta, producto_id,
                     producto_nombre, cantidad, precio_unitario, descuento, total)
sales_pago (id UUID PK, venta_id FK->sales_venta, metodo, monto, vuelto, referencia)

cash_turno_caja (id UUID PK, cajero_id, estado, monto_apertura, monto_cierre,
                 diferencia, fecha_apertura, fecha_cierre)
cash_movimiento_caja (id UUID PK, turno_id FK->cash_turno_caja, tipo, monto, usuario_id)

orders_pedido (id UUID PK, numero UQ, cliente_id, cliente_nombre, cliente_dni,
               estado, total, hora_recojo, ...)
orders_detalle_pedido (id UUID PK, pedido_id FK->orders_pedido, producto_id,
                       cantidad, precio_unitario, subtotal)

customers_cliente (id UUID PK, nombre, dni UQ, email, telefono, usuario_id,
                   puntos_fidelidad)
promotions_promocion (id UUID PK, nombre, tipo, estado, producto_id, descuento_valor,
                      vigencia_desde, vigencia_hasta, aplica_clientes_frecuentes)
auditing_registro (id UUID PK, accion, entidad, entidad_id, usuario_id, detalle JSON,
                   ip, fecha)
```

Notas:
- Todos los IDs son UUID v4 (sin secuencias expuestas).
- `sales_detalle_venta` congela `producto_nombre` y `precio_unitario` para conservar el
  historial aunque el producto cambie.
- No hay FK hacia catalogo desde inventario/ventas: se usa UUID logico para desacoplar
  modulos (integridad aplicada en los casos de uso).

