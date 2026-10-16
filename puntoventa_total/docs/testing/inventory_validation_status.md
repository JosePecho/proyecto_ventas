# Estado verificado del inventario

Fecha: 16 de octubre de 2026. Ejecucion: `2026-10-16T20:45:42.326611+00:00`.

| Comprobacion | Resultado observado |
|---|---|
| Suite completa, cuatro niveles | **300 aprobadas; 0 fallos; 0 omisiones; 0 xfail** |
| Motor de BD | MySQL 8.4.3, InnoDB real, instancia nativa efimera |
| Unitarias de inventario | 106 aprobadas; cobertura dominio/aplicacion 95,95 %; gate >=80 % |
| Integracion de inventario | 48 casos RF/reservas y 5 casos de concurrencia aprobados |
| Navegador | Chromium obligatorio, inventario y POS con ticket PDF aprobados |
| Seguridad | CSRF, escape HTML y cabeceras aprobados |
| Carga HTTP | 20 peticiones, 4 usuarios; 0 errores; p95 131.26 ms <= 2000.0 ms |
| Aceptacion automatizada | 6 escenarios BDD aprobados con ORM MySQL |
| Auditoria QA-INV-01..03 | Exit 0; los tres defectos ya no se reproducen |
| RN-07 de ventas | Corregido; antigua prueba xfail y cinco regresiones adicionales aprobadas |
| Docker/Testcontainers | No ejecutado; la validacion real de BD se completo con MySQL nativo desechable |
| GitHub Actions remoto | Workflow preparado localmente; publicacion y ejecucion remota pendientes |
| Aprobacion humana de negocio | Pendiente en inventory_uat_approval.md |

Los casos de concurrencia comprueban dos salidas, dos reservas, liberacion
repetida, confirmacion repetida y primeras recepciones simultaneas. Cada trabajador
usa su propia conexion y la cierra al terminar. No se agregaron retries ni skips
para conseguir verde. Se corrigio una expectativa del nuevo test: confirmar una
reserva genera SALIDA_PEDIDO, segun el contrato real del modulo.

La suite emite 24 advertencias existentes de deprecaciones, fechas naive en otros
componentes y formato de claves de cache. No tuvo errores de limpieza de la BD
temporal en esta ejecucion de MySQL. Una ejecucion aprobada no garantiza ausencia
absoluta de flakiness ni rendimiento productivo.

## Reproduccion desde puntoventa_total

```powershell
$qaMysql = Join-Path $env:TEMP 'qa-mysql-binaries/mysql-8.4.3-winx64'
.venv/Scripts/python.exe -m pip install -r requirements/qa-inventory-mysql.txt
.venv/Scripts/python.exe -m playwright install chromium
.venv/Scripts/python.exe scripts/qa_inventory_mysql_native.py --basedir $qaMysql --full
```

El ZIP oficial ya esta extraido en esa ruta de este equipo. El runner requiere
ese directorio de binarios, crea sus propios datos y credenciales, y apaga y elimina
su instancia. Solo carga las zonas UTC y America/Lima para fechas actuales;
no valida el historial completo de cambios de zona horaria.

Artefactos locales en reports/: inventory-mysql-native.xml/json,
inventory-unit-coverage.xml/json, inventory-load.json, inventory-findings.json y
browser/*.zip. El informe completo y el codigo reproducible estan en
inventory_master_plan.md. El workflow de la raiz conserva la ruta Testcontainers
para CI Linux y agrega las regresiones de descuentos del POS.

La ejecucion local de los cuatro niveles esta completa. Publicar los cambios,
observar CI remoto y firmar UAT son pasos separados y no se presentan como realizados.
