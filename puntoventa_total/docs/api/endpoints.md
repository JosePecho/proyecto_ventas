# Endpoints

Todas las rutas son HTML salvo las marcadas como AJAX (JSON). Autenticacion por sesion.

## Identidad (`/`)
| Metodo | Ruta | Accion |
|---|---|---|
| GET/POST | `/login/` | Iniciar sesion |
| GET | `/logout/` | Cerrar sesion |
| GET | `/usuarios/` | Listar (ADMIN) |
| POST | `/usuarios/nuevo/` | Crear (ADMIN) |
| GET/POST | `/usuarios/<id>/editar/` | Editar nombre, email, rol y contraseña opcional (ADMIN) |
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
| POST | `/pedidos/pedido/<id>/cancelar/` | Cancelar pedido propio Pendiente |
| POST | `/pedidos/pedido/<id>/estado/` | Avanzar estado (CAJERO/GERENTE/ADMIN) |
| GET | `/pedidos/cocina/` | Panel de cocina |
| GET | `/pedidos/seguimiento/?numero=` | Seguimiento autenticado del pedido propio; ajeno devuelve 404 |

## Otros
- Clientes: `/clientes/registro/`, `/clientes/perfil/<id>/`, `/clientes/historial/<id>/`
- Promociones: `/promociones/`, `/promociones/gestion/`, `/promociones/<id>/editar/`
- Reportes: `/reportes/`, `/reportes/ventas/?formato=csv|pdf`, `/reportes/inventario/`, `/reportes/utilidad/`
- Auditoria: `/auditoria/?accion=&entidad=&entidad_id=`

## Contratos comprobados RF-030 a RF-050

Son formularios HTML con sesión y CSRF; no son endpoints REST que acepten JSON.
Las mutaciones válidas suelen redirigir con 302 y los errores de formulario se
renderizan con 200. Los filtros inválidos de reportes devuelven 400. Los cambios
de estado y cancelación de pedidos requieren POST; la falta de CSRF devuelve 403.

| Flujo | Entradas y comportamiento |
|---|---|
| Registro web: POST `/clientes/registro/` sin sesión | `nombre`, `dni` (8 dígitos), `email`, `telefono`, `password`, `password_confirmacion`; crea cuenta CLIENTE y perfil; redirige al login |
| Login: POST `/login/` | El campo se llama `username` y acepta email; `password`; email se compara sin distinguir mayúsculas |
| Checkout: POST `/pedidos/checkout/` | `cliente_nombre`, `cliente_dni`, `cliente_telefono`, `modalidad=RECOJO`, `hora_recojo` futura en minutos 00/30 sin segundos; confirmación/reserva atómicas |
| Estado: POST `/pedidos/pedido/<id>/estado/` | `estado=EN_PREPARACION`, luego `LISTO`, luego `ENTREGADO`; transición inválida no cambia pedido/stock |
| Registro en caja: POST `/clientes/registro/` | Cajero/gerente/admin: `nombre`, `dni`, `telefono`; no asocia el perfil a la cuenta del operador |
| Historial: GET `/clientes/historial/<id>/` | UUID de Customers.Cliente; cliente propietario o CAJERO/GERENTE/ADMIN; solo ventas PAGADA; ajeno devuelve 403 |
| Crear promoción: POST `/promociones/crear/` | ADMIN/GERENTE; `nombre`, `tipo=PORCENTAJE|NX1|COMBO`, `descuento_valor`; NX1 requiere producto; combo requiere componentes distintos; fechas de inicio/fin juntas |
| Reportes: GET `/reportes/ventas/`, `/reportes/productos/`, `/reportes/utilidad/` | ADMIN/GERENTE; `desde`, `hasta` YYYY-MM-DD inclusivos en fecha local; ranking acepta `orden=cantidad|monto`; excluye ventas anuladas |

RF-037 se verifica con correo local/SMTP de QA. No hay proveedor SMS productivo
validado. El éxito de SMTP local no acredita recepción en un buzón real.

### Precisiones RF-047 y RF-050

`/reportes/utilidad/` presenta margen porcentual por producto y total, calculado
sobre ingresos netos y redondeado HALF_UP a dos decimales. Una fila con ingresos
cero o costos históricos incompletos muestra el margen como «No disponible».
Los históricos incompletos conservan el aviso de utilidad parcial.

`GET /auditoria/` admite `accion`, `entidad`, `entidad_id`, `usuario_id` (UUID),
`desde`, `hasta` y `pagina` (entero positivo, por defecto 1). UUID, páginas o
fechas malformados y rangos invertidos devuelven 400 con errores de formulario.
La consulta exige ADMINISTRADOR; las acciones CREAR, ACTUALIZAR y ELIMINAR del
middleware son consultables junto a las acciones específicas de negocio.

