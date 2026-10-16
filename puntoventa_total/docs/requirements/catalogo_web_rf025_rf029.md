# Módulo 3.3 — Catálogo Web

| ID | Comportamiento implementado | Ruta y validación |
|---|---|---|
| RF-025 | Catálogo público sin inicio de sesión; precio vigente y stock físico menos reservas consultados en cada petición | GET /catalogo/; integración, navegador y BDD |
| RF-026 | Filtros por Abarrotes, Bebidas, Snacks, Limpieza y Cuidado personal; compatibles con búsqueda y paginación | ?categoria=<uuid>; migración 0003 crea las categorías sin reemplazar configuraciones existentes |
| RF-027 | Búsqueda parcial por nombre, sin distinguir mayúsculas en los casos probados; también conserva la búsqueda por descripción existente | ?q=<texto>; espacios extremos eliminados y HTML escapado |
| RF-028 | Detalle público con descripción, precio, imagen y disponibilidad; imagen alternativa cuando no hay imagen cargada | /catalogo/productos/<uuid>/; imagen real comprobada en Chromium |
| RF-029 | Agotados permanecen visibles, con etiqueta Agotado cuando no queda stock disponible | Listado y detalle; probado sin existencia, stock cero y stock totalmente reservado |

El stock se actualiza al consultar o recargar la página. No se implementó una
suscripción push. Productos inactivos y descontinuados no se publican y su detalle
devuelve 404. Las reservas no se ofrecen como unidades disponibles para otro cliente.

La página contiene como máximo 20 productos por defecto. Los filtros permanecen
al avanzar y retroceder. Una página no numérica se interpreta como la primera y
una página fuera de rango se ajusta al rango disponible. Una categoría con UUID
malformado devuelve 404; una inexistente devuelve un listado vacío.

Se respeta el almacenamiento configurado para resolver las imágenes. En producción,
el nginx existente sirve /media/ desde /app/media/. Las pruebas usan una ruta de
medios exclusiva del servidor de pruebas y un archivo PNG temporal.

Migración: aplicar `catalog.0003_categorias_catalogo_web` con el comando `manage.py
migrate` y los ajustes habituales del despliegue. No se modifica una base de
producción desde las pruebas.

La guía de cuatro niveles, herramientas, código y CI está en
[plan maestro de pruebas](../testing/catalog_master_plan.md).
