# Estrategia offline del POS

El POS debe vender aunque falle internet/BD central durante minutos.

## Componentes (static/js/offline/)

| Archivo | Responsabilidad |
|---|---|
| `service_worker.js` | Cache de assets criticos (CSS/JS del POS) |
| `indexed_db.js` | Almacena catalogo local y cola de envios |
| `offline_queue.js` | Encola acciones POST cuando no hay red |
| `sync_manager.js` | Al volver la red, sincroniza por orden de fecha |
| `conflict_resolver.js` | Resuelve duplicados por numero de ticket |

## Flujo de venta offline

1. El service worker entrega el shell del POS desde cache.
2. El catalogo se replica en IndexedDB (`productos`) durante la ultima conexion.
3. Cada cobro genera un registro con UUID local y se encola.
4. Al detectar `online`, `SyncManager` reenvia en orden cronologico.
5. Si el servidor ya tiene el ticket, se descarta la copia local (numero de ticket unico).

## Limites conocidos

- El stock puede quedar momentaneamente inconsistente; el inventario se reconcilia con
  los movimientos al sincronizar.
- Mas de 50 ventas offline simultaneas requieren el turno local (roadmap).

