# Inventario: RF-016 a RF-024

Acceso de administrador, gerente y almacenero. Las rutas usan sesiones de Django;
los formularios POST requieren CSRF y muestran los errores sin guardar cambios.

| ID | Comportamiento | Pantalla |
|---|---|---|
| RF-016 | Alta y edicion de codigo, nombre, categoria, precio, costo, minimo y vencimiento. Categoria persistida; minimo no negativo. | `/catalogo/productos/nuevo/`, `/catalogo/productos/<uuid>/editar/` |
| RF-017 | El pago completo descuenta existencia y lotes por vencimiento proximo, registra salidas y rechaza un segundo cobro. Los pagos parciales no descuentan. Una linea sin stock revierte toda la operacion. | Punto de venta e inventario |
| RF-018 | Disponible = cantidad fisica menos reservas. Al caer estrictamente por debajo del minimo individual se notifica despues del commit. La igualdad no alerta. Incluye productos sin recepcion en la lista de faltantes. | `/inventario/alertas/` |
| RF-019 | Lotes con saldo y vencimiento entre hoy y hoy + 30 dias, ambos incluidos. Los vencidos aparecen aparte. Se muestra nombre del producto. El vencimiento del catalogo se usa si el producto aun no tiene lotes. | `/inventario/alertas/` |
| RF-020 | Recepcion de producto existente con lote, cantidad positiva, costo, proveedor y vencimiento; guarda lote, existencia y entrada de kardex en una transaccion. Vencimiento opcional para productos no perecibles. | `/inventario/recepcion/` |
| RF-021 | Merma por vencimiento, daño o robo; admite otros motivos del sistema. Valida cantidades, disponible y pertenencia del lote. Sin lote explicito distribuye la salida entre lotes, incluidos los vencidos. | `/inventario/mermas/` |
| RF-022 | Historial de entradas, ventas, mermas, devoluciones y ajustes, filtrable por producto y fechas. Paginas de 50 movimientos con total correcto y filtros conservados. | `/inventario/kardex/` |
| RF-023 | Productos activos sin ventas pagadas desde hoy - 60 dias hasta hoy. Ventas anuladas y borradores no cuentan. Incluye productos que nunca se vendieron. | `/reportes/inventario/` |
| RF-024 | Productos activos ordenados por margen descendente, con costo, precio y ganancia unitaria, aunque no tengan ventas. | `/reportes/inventario/` |

El margen conserva la regla existente de `Precio`: `(precio - costo) / costo * 100`;
para costo cero usa 100 %. El dashboard de ventas conserva su ranking separado
por utilidad total en un rango de fechas.

La anulacion de ventas repone los lotes originales con su vencimiento. Las ventas
historicas sin referencias de lote generan un lote de devolucion sin vencimiento.
La confirmacion de reservas tambien descuenta lotes. Las escrituras usan bloqueos
de filas dentro de transacciones; la concurrencia real debe comprobarse en MySQL,
porque SQLite no implementa `SELECT FOR UPDATE`.

## Migraciones y operacion

Se incorpora `catalog/migrations/0001_initial.py` con el esquema previo y
`0002_productomodel_fecha_vencimiento_and_more.py` con los campos nuevos. En una
base existente creada por sincronizacion, `--fake-initial` reconoce las tablas
previas y luego aplica los campos nuevos sin borrar datos:

```powershell
.venv\Scripts\python.exe manage.py migrate catalog --fake-initial
```

En instalaciones nuevas, ejecutar tambien `migrate --run-syncdb` para los modulos
que aun no disponen de migraciones. Usar los ajustes del entorno correspondiente.

`STOCK_ALERTA_DESTINATARIOS` configura destinatarios separados por comas. El envio
usa el backend de correo de Django: consola en desarrollo, memoria durante las
pruebas y SMTP configurado por el despliegue. Las pruebas no envian correos reales.
La lista de alertas siempre se calcula desde la base de datos.

Celery carga las tareas de inventario mediante `CELERY_IMPORTS`. Con worker y beat
en ejecucion se revisa stock cada hora y vencimientos cada seis horas. El cruce de
stock minimo se notifica tambien desde la operacion confirmada, sin esperar a beat.

## Verificacion reproducible

```powershell
.venv\Scripts\python.exe -m pytest tests/integration/test_inventario_requisitos.py -q -p no:cacheprovider
.venv\Scripts\python.exe -m pytest tests/unit tests/integration tests/functional tests/system/test_flujo_pos_sistema.py -q -p no:cacheprovider
.venv\Scripts\python.exe manage.py check --settings=config.settings.testing
```

Los escenarios usan ORM y transacciones reales sobre SQLite y peticiones HTTP del
cliente Django. Cubren los nueve requisitos, permisos, entradas invalidas, limites
de fechas, rollback, PEPS, reintentos, devoluciones y confirmacion de reservas.
No equivalen a validar SMTP, Redis/Celery desplegados ni concurrencia sobre MySQL.

Verificacion del 16/10/2026: suite completa con **174 pruebas aprobadas y 1 xfail**
preexistente de descuentos de ventas (RN-07), sin fallos nuevos. Incluye 47 casos
de inventario en integracion y un flujo nuevo de almacen en Chromium. La prueba
de navegador del POS tambien paso, comprobando la respuesta PDF del ticket.
`manage.py check` y la comprobacion de migraciones de catalogo pasaron.
Se verifico tanto la creacion desde cero como la actualizacion de tablas sin
historial de migraciones, preservando un producto previo. La base SQLite generada
para verificar el esquema no se incluye en los cambios.

El arranque con `config.settings.development` no pudo comprobarse: el entorno
actual no tiene instalado `django-debug-toolbar`, ya declarado en las dependencias
de desarrollo. Las pruebas usan `config.settings.testing` y correo en memoria.


Actualizacion final de pruebas del 16/10/2026: **300 aprobadas, sin omisiones
ni xfail**, ejecutando los cuatro niveles con MySQL 8.4.3/InnoDB nativo efimero
y Chromium obligatorio. Incluye cinco casos de concurrencia y la correccion de
RN-07. Cobertura unitaria de inventario: 95,95 %. Evidencia y limites en
[estado de validacion](../testing/inventory_validation_status.md).
