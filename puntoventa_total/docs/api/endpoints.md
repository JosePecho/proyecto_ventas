# Endpoints

Todas las rutas son HTML salvo las marcadas como AJAX (JSON). Autenticacion por sesion.

## Identidad (`/`)
| Metodo | Ruta | Accion |
|---|---|---|
| GET/POST | `/login/` | Iniciar sesion |
| GET | `/logout/` | Cerrar sesion |
| GET | `/usuarios/` | Listar (ADMIN) |
| POST | `/usuarios/nuevo/` | Crear (ADMIN) |
| POST | `/usuarios/<id>/desactivar/` | Desactivar (ADMIN) |

## Catalogo (`/catalogo/`)
| Metodo | Ruta | Accion |
|---|---|---|
| GET | `/catalogo/?q=&categoria=&pagina=` | Vitrina publica |
| GET | `/catalogo/productos/<id>/` | Detalle |
| GET | `/catalogo/productos/admin/` | Admin (GERENTE/ADMIN) |
| POST | `/catalogo/productos/nuevo/` | Crear |
| POST | `/catalogo/productos/<id>/descontinuar/` | Descontinuar |
| GET/POST | `/catalogo/categorias/` | Gestionar categorias |

## Inventario (`/inventario/`)
| Metodo | Ruta | Accion |
|---|---|---|
| GET | `/inventario/` | Existencias |
| GET/POST | `/inventario/recepcion/` | Recepcion de mercaderia |
| GET/POST | `/inventario/mermas/` | Registrar merma |
| GET | `/inventario/kardex/?producto_id=&desde=&hasta=` | Kardex |
| GET | `/inventario/alertas/` | Alertas stock/vencimientos |

## Ventas POS (`/pos/`)
| Metodo | Ruta | Accion |
|---|---|---|
| GET | `/pos/` | Interfaz POS |
| GET | `/pos/buscar/?q=` (AJAX) | Busqueda por scanner/texto |
| GET | `/pos/ventas/` | Ventas del dia |
| POST | `/pos/venta/<id>/agregar/<producto_id>/` (AJAX) | Agregar producto |
| POST | `/pos/venta/<id>/cantidad/<producto_id>/` (AJAX) | Modificar cantidad |
| POST | `/pos/venta/<id>/eliminar/<producto_id>/` (AJAX) | Eliminar producto |
| GET/POST | `/pos/venta/<id>/pago/` | Cobro |
| GET | `/pos/venta/<id>/ticket/` | Ticket PDF |
| POST | `/pos/venta/<id>/anular/` | Anular (ADMIN/GERENTE) |

## Caja (`/caja/`)
| Metodo | Ruta | Accion |
|---|---|---|
| GET/POST | `/caja/apertura/` | Abrir turno |
| GET/POST | `/caja/cierre/` | Cerrar turno |
| GET | `/caja/arqueo/?turno_id=` | Arqueo |

## Pedidos (`/pedidos/`)
| Metodo | Ruta | Accion |
|---|---|---|
| GET | `/pedidos/carrito/` | Carrito web |
| POST | `/pedidos/carrito/agregar/<producto_id>/` | Agregar |
| GET/POST | `/pedidos/checkout/` | Confirmar pedido |
| GET | `/pedidos/mis-pedidos/` | Pedidos del cliente |
| GET | `/pedidos/pedido/<id>/` | Detalle |
| GET | `/pedidos/cocina/` | Panel de cocina |
| GET | `/pedidos/seguimiento/?numero=` | Seguimiento publico |

## Otros
- Clientes: `/clientes/registro/`, `/clientes/perfil/<id>/`, `/clientes/historial/<id>/`
- Promociones: `/promociones/`, `/promociones/gestion/`, `/promociones/<id>/editar/`
- Reportes: `/reportes/`, `/reportes/ventas/?formato=csv|pdf`, `/reportes/inventario/`, `/reportes/utilidad/`
- Auditoria: `/auditoria/?accion=&entidad=&entidad_id=`

