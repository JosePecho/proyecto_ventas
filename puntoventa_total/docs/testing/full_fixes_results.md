# Correcciones de la auditoría transversal

> Actualización posterior: las validaciones completas con Redis, Celery, SMTP y k6
> se registran en [complete_validation.md](complete_validation.md). Los pendientes
> y cifras de esta primera corrección se conservan como historial.

Estado posterior a las correcciones del 16/10/2026. Este documento sustituye los
estados abiertos de la auditoría inicial `full_master_audit.md`.

| Hallazgo | Corrección | Evidencia / límite |
|---|---|---|
| AUD-01: redirección externa | Login valida host/esquema y exige HTTPS si la petición es segura; fallback a catálogo | Regresiones de destino externo y destinos locales aprobadas |
| AUD-02: perfil ajeno | GET y POST requieren CLIENTE propietario o ADMINISTRADOR/GERENTE/CAJERO; ALMACENERO y sesiones sin rol se rechazan | Matriz de roles/propiedad con comprobación de persistencia aprobada; historial ya restringido al personal |
| AUD-03: página inválida | Letras, decimales, cero y negativos responden HTTP 400 | Cuatro casos negativos aprobados |
| AUD-04: MySQL no validado | Se ejecutó la suite completa en MySQL 8.4.3/InnoDB efímero con el wrapper nativo existente | 380 aprobadas, un caso Redis omitido; instancia temporal, sin datos de negocio; ejecución Docker sigue pendiente |
| AUD-05: CI incompleto y perfiles divergentes | Workflow raíz con cuatro niveles, gates unitario/global >=80%, Chromium obligatorio y Redis real; matriz Python 3.11/base declarada y Python 3.14.7/QA | Gates locales aprobados; pipeline remoto y perfil Python 3.11 no ejecutados en esta sesión; no se cambió silenciosamente producción |
| AUD-06: k6 sin sesión/CSRF válido | Un cajero y cookie jar por VU, sesión persistente, token tras rotación de login, sin seguir redirección al comprobar 302, check PDF y thresholds de checks | Sintaxis JavaScript verificada con Node; k6 no está instalado, carga con este script pendiente |
| AUD-07: fechas naive | Reloj UTC del dominio; fechas de acceso/caja/auditoría/eventos/movimientos/reservas con zona; límites de consultas en zona de negocio; comparación de recojo/promoción compatible con fechas aware | Regresiones con UTC/Lima/naive y suite completa sin warnings |
| AUD-08: SMS simulado declara éxito | El adaptador no configurado devuelve False y no registra nombre/teléfono/mensaje | Regresión aprobada; envío SMS real requiere elegir/configurar proveedor y credenciales |
| Caché mezclaba búsquedas | La clave incluye argumentos posicionales y kwargs mediante hash, sin espacios/caracteres problemáticos | Buscar arroz/pan y repetir arroz conserva resultados separados y reutiliza su resultado |
| Correo al remitente | EmailNotifier usa el destino recibido y no el remitente como destinatario | Outbox real de Django dirigido a ana@example.test |
| Deprecated email y alerta silenciosa | Configuración MAILERS en Django >=6.1; compatibilidad EMAIL_BACKEND en versiones anteriores; alertas capturan errores SMTP/I/O y los registran explícitamente | Suite sin warnings; fallo de transporte de alerta probado; SMTP externo no ejercitado |
| SQLite ocupado al terminar navegador | Se cierran conexiones ORM del contexto async antes de detener Playwright | Suite SQLite completa sin warning de teardown |

Los tres defectos originales ya no tienen `xfail`. Los controles de autorización
no aceptan un usuario únicamente por estar autenticado. No se alteraron los cambios
previos de catálogo para conseguir estos resultados.

## Resultados ejecutados

| Validación | Resultado |
|---|---|
| Suite SQLite completa, cuatro niveles, navegador real | **375 aprobadas, 6 omitidas, 0 fallos, 0 xfail, sin warnings** |
| Cobertura global de esa ejecución | **81,58 %** de líneas, umbral 80 % aprobado |
| Suite MySQL efímero nativo, cuatro niveles y navegador real | **380 aprobadas, 1 omitida, 0 fallos, 0 xfail, sin warnings** |
| Unitarias aisladas | **223 aprobadas** |
| Cobertura unitaria dominio/aplicación | **2016/2251 = 89,56 %**, umbral 80 % aprobado |
| Django system checks | Sin incidencias |
| Script k6 de cobro | Sintaxis verificada con `node --check`; no medición de carga k6 |

Las seis omisiones SQLite son los cinco casos InnoDB y la prueba Redis/Celery.
En MySQL solo se omite Redis/Celery por faltar `QA_REDIS_URL` local.
La prueba de Redis/worker está configurada en CI sobre un servicio aislado;
su ejecución remota todavía no está comprobada. Es una comprobación de infraestructura
con worker real; no demuestra por sí sola todas las tareas de negocio.

## Reproducción

Desde `puntoventa_total`, usando el perfil QA instalado:

```powershell
rtk proxy .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --runxfail --cov=src --cov-report=json:reports/fixes_coverage.json --cov-report=xml:reports/fixes_coverage.xml --cov-fail-under=80 --junitxml=reports/fixes_junit.xml
rtk proxy .venv/Scripts/python.exe -m pytest tests/unit -q --cov=src --cov-fail-under=0 --cov-report=json:reports/audit_unit_coverage.json
rtk proxy .venv/Scripts/python.exe scripts/qa_unit_gate.py
rtk proxy .venv/Scripts/python.exe manage.py check --settings=config.settings.testing
rtk proxy node --check tests/performance/k6_cobro.js
```

Con Docker Desktop activo:

```powershell
rtk proxy .venv/Scripts/python.exe scripts/qa_inventory_mysql.py tests/integration --runxfail
```

Alternativa utilizada, solo si existen estos binarios en la máquina:

```powershell
rtk proxy .venv/Scripts/python.exe scripts/qa_inventory_mysql_native.py --basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --full
```

Para Redis/Celery, definir `QA_REDIS_URL` hacia un Redis exclusivo de QA y ejecutar
`tests/integration/test_redis_celery_real.py`. No apuntar al broker de negocio.

La carga k6 necesita un entorno QA preparado: cajeros distintos por VU, sin turno
abierto previo, producto activo y stock para todas las iteraciones. Variables y
ejecución se describen al inicio de `tests/performance/k6_cobro.js`.

## Artefactos y pendientes externos

- `reports/fixes_junit.xml`, `reports/fixes_coverage.json`, `reports/fixes_coverage.xml`.
- `reports/inventory-mysql-native.xml` y `.json`: versión, engine, ejecución efímera y salida 0.
- `reports/audit_unit_coverage.json`: evidencia del gate exclusivamente unitario.
- `.github/workflows/full-quality.yml` en la raíz: checks `quality (production-declared)` y `quality (qa)`.
- Los checks solo bloquean merges cuando un administrador los configura como requeridos en el ruleset de la rama.
- Pendientes de ejecución/configuración externa: CI remoto, Redis/worker real, k6 contra despliegue,
  proveedor SMS, correo SMTP real y aprobación del Product Owner.

Los fallos de aplicación reproducidos están corregidos. No se declara entrega SMS,
compatibilidad productiva completa ni aprobación UAT por tener la suite local verde.
