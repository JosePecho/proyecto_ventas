# Requisitos funcionales

## RF-01 Identidad
- RF-01.1 Autenticar usuarios con usuario/contrasena; bloquear tras 5 intentos fallidos.
- RF-01.2 Administrar usuarios (crear, actualizar, desactivar) restringido a ADMINISTRADOR.
- RF-01.3 Cada rol tiene permisos explicitos (matriz en `PoliticaPermisos`).

## RF-02 Catalogo
- RF-02.1 CRUD de productos y categorias con margen minimo del 10%.
- RF-02.2 Busqueda por texto libre y por codigo de barras (EAN-13).
- RF-02.3 Descontinuar un producto impide venderlo.

## RF-03 Inventario
- RF-03.1 Recepcion de mercaderia por lote con proveedor, costo y vencimiento.
- RF-03.2 Salidas por PEPS (vencimiento mas proximo primero).
- RF-03.3 Reserva de stock para pedidos web con expiracion de 20 minutos.
- RF-03.4 Kardex inmutable de todos los movimientos.
- RF-03.5 Mermas con motivo; alertas de stock minimo y vencimientos.

## RF-04 Ventas (POS)
- RF-04.1 Carrito con escaner de codigo de barras; atajos de teclado (Alt+F2/F8, Esc).
- RF-04.2 Cobro parcial y total; vuelto automatico en efectivo.
- RF-04.3 El cobro descuenta stock atomicamente; sin cobro no hay descuento.
- RF-04.4 Emision de ticket PDF 80mm.
- RF-04.5 Anulacion con motivo por gerente; devuelve stock automaticamente.

## RF-05 Caja
- RF-05.1 Un cajero solo puede tener un turno abierto.
- RF-05.2 Movimientos de ingreso/egreso firmados por usuario.
- RF-05.3 Cierre con conteo fisico, calculo de diferencia y desglose por metodo de pago.

## RF-06 Pedidos web
- RF-06.1 Carrito publico con reserva de stock.
- RF-06.2 Flujo: BORRADOR -> CONFIRMADO -> EN_PREPARACION -> LISTO -> ENTREGADO / CANCELADO.
- RF-06.3 Seleccione de hora de recojo en franjas de 30 minutos.
- RF-06.4 Notificaciones por email/SMS al confirmar, estar listo y cancelar.
- RF-06.5 Seguimiento publico por numero de pedido.

## RF-07 Clientes y promociones
- RF-07.1 Registro de clientes con DNI validado y puntos de fidelidad.
- RF-07.2 Historial de compras y clasificacion de frecuencia.
- RF-07.3 Promociones PORCENTAJE, MONTO_FIJO, NX1 y PRECIO_ESPECIAL con vigencias.
- RF-07.4 Derecho al olvido: anonimizacion sin perder trazabilidad de ventas.

## RF-08 Reportes y auditoria
- RF-08.1 Ventas por dia/rango, top productos, utilidad y margen.
- RF-08.2 Productos de baja rotacion y stock minimo.
- RF-08.3 Exportacion CSV y PDF.
- RF-08.4 Auditoria inmutable de acciones sensibles con rastreo por entidad.

