# Requisitos funcionales no

## RNF-01 Rendimiento
- Busqueda por codigo de barras: < 200 ms (p95).
- Cobro completo (descuento de stock + persistencia): < 500 ms (p95).
- Catalogo publico: < 800 ms con 50.000 productos (cache Redis de 120s).

## RNF-02 Disponibilidad
- Objetivo 99.5% en horario de tienda.
- El POS debe seguir operando offline (cola de sincronizacion con IndexedDB).

## RNF-03 Seguridad
- Contrasenas con PBKDF2 (Django defaults).
- Cookies secure/HSTS en produccion; cabeceras X-Frame-Options y nosniff.
- Auditoria de toda accion sensible con usuario, IP y detalle.

## RNF-04 Integridad
- Ninguna venta puede quedar PAGADA sin descuento de stock (transaccion unica).
- El arqueo nunca asume: compara conteo fisico vs sistema y registra la diferencia.
- Movimientos de kardex inmutbles.

## RNF-05 Usabilidad
- POS operable 100% con teclado (sin mouse).
- Interfaz responsive para tablet y celular (cliente web).

## RNF-06 Mantenibilidad
- Separacion por modulos con reglas de dependencia verificables.
- Cobertura objetivo >= 80% en `domain` y `application`.

## RNF-07 Operacion
- Despliegue via Docker Compose (web, worker, beat, db, cache, nginx).
- Metricas Prometheus y alertas de latencia/errores/cola.

