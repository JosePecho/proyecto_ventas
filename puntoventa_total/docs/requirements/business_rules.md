# Reglas de negocio

| Codigo | Regla | Ubicacion |
|---|---|---|
| RN-01 | Todo precio de venta debe superar al costo en al menos 10% | `catalog/domain/value_objects/precio.py` |
| RN-02 | No se puede vender un producto descontinuado | `catalog/domain/entities/producto.py` |
| RN-03 | Las salidas de stock usan PEPS (vencimiento mas proximo primero) | `inventory/domain/services/politica_stock.py` |
| RN-04 | reservada <= cantidad; disponible = cantidad - reservada | `inventory/domain/entities/existencia.py` |
| RN-05 | Las reservas expiran a los 20 minutos y liberan stock | `inventory/domain/entities/reserva_stock.py` |
| RN-06 | Una venta BORRADOR no puede anularse dos veces ni cerrarse sin pago total | `sales/domain/aggregates/venta_aggregate.py` |
| RN-07 | El descuento total de una venta no puede superar 50% | `sales/domain/aggregates/venta_aggregate.py` |
| RN-08 | El vuelto nunca puede ser negativo | `sales/domain/services/calculadora_venta.py` |
| RN-09 | Un cajero solo puede tener un turno de caja abierto | `cash_register/application/use_cases/abrir_turno.py` |
| RN-10 | La diferencia de arqueo se registra como movimiento firmado | `cash_register/application/use_cases/cerrar_turno.py` |
| RN-11 | Los pedidos solo avanzan segun el flujo de estados definido | `orders/domain/enums/estado_pedido.py` |
| RN-12 | La hora de recojo debe ser futura y en franjas de 30 minutos | `orders/domain/entities/pedido.py` |
| RN-13 | No se puede desactivar al ultimo administrador | `identity/application/use_cases/desactivar_usuario.py` |
| RN-14 | El DNI debe tener 8 digitos | `shared/domain/value_objects/dni.py` |
| RN-15 | Una promocion solo aplica dentro de su vigencia y estado ACTIVA | `promotions/domain/entities/promocion.py` |
| RN-16 | El kardex es inmutable: las correcciones son movimientos compensatorios | `inventory/domain/entities/movimiento_stock.py` |
| RN-17 | Los montos se redondean a 2 decimales con ROUND_HALF_UP | `shared/domain/value_objects/monto.py` |

