# Monolito modular

El sistema es un **unico despliegue** (un Django project) con **10 modulos** fuertemente
delimitados. Cada modulo publica su comportamiento mediante:

1. **Puertos (`ports/`)**: interfaces que otros modulos pueden consumir.
2. **Adaptadores (`adapters/`)**: traducciones hacia el modulo concreto.
3. **Tasks Celery**: comportamiento asincrono (alertas, notificaciones).

## Modulos

| Modulo | Responsabilidad | Depende de |
|---|---|---|
| identity | Usuarios, roles, autenticacion | - |
| catalog | Productos, categorias, imagenes | inventory (puerto) |
| inventory | Lotes, stock, reservas, kardex | catalog (solo IDs) |
| sales | POS, cobros, tickets, anulaciones | catalog, inventory, promotions, auditing |
| cash_register | Turnos, movimientos, arqueo | sales (solo lectura agregada) |
| orders | Pedidos web, recojo, notificaciones | catalog, inventory |
| customers | Clientes, fidelizacion, historial | sales (solo lectura) |
| promotions | Descuentos y vigencias | customers (puerto frecuencia) |
| reporting | Reportes y exportadores | todos (solo lectura via repos) |
| auditing | Traza inmutable | - |

## Comunicacion entre modulos

- **Permitida**: a traves de puertos y adaptadores (ej. `sales.ports.InventarioPort`).
- **Prohibida**: importar modelos ORM de otro modulo desde el dominio/aplicacion.
  (Las lecturas de reportes usan los repositorios publicos del modulo dueño de los datos.)
- **Datos compartidos**: solo identificadores UUID; ningun modulo expone sus tablas.

## Escalado futuro

La modularidad permite extraer un modulo a un servicio independiente reemplazando su
adaptador por un cliente HTTP/mensajeria sin tocar el resto del codigo.

