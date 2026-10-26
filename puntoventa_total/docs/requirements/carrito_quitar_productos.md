# Quitar productos del carrito web

`POST /pedidos/carrito/quitar/<producto_id>/` (nombre Django `orders:quitar`)
quita todas las unidades del producto del pedido de la sesion `pedido_web`.
Requiere autenticacion, CSRF valido y propiedad del pedido. Solo modifica pedidos
BORRADOR; recalcula y persiste el total y redirige al carrito. Si no hay carrito
o la linea ya fue retirada, redirige sin cambios. GET devuelve 405; un pedido
ajeno devuelve 404. Un pedido confirmado no admite cambios.

Al quitar la ultima linea se muestra el carrito vacio y se oculta el checkout.
Los borradores no reservan stock: las reservas se crean en la confirmacion.
