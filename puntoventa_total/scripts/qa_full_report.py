"""Genera un informe auditable desde JUnit, coverage JSON y fuentes reales."""
from collections import defaultdict
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def source(path, language="python"):
    return f"\nArchivo `{path}`:\n\n```{language}\n{(ROOT / path).read_text(encoding='utf-8').rstrip()}\n```\n"


def main():
    coverage = json.loads((ROOT / "reports/audit_final_coverage.json").read_text())
    junit = ET.parse(ROOT / "reports/audit_final_junit.xml")
    counts = defaultdict(lambda: defaultdict(int))
    for case in junit.iter("testcase"):
        parts = case.attrib["classname"].split(".")
        level = parts[1] if len(parts) > 1 else "otro"
        skipped = case.find("skipped")
        result = "passed"
        if skipped is not None:
            result = "xfail" if "xfail" in skipped.attrib.get("type", "") else "skipped"
        elif case.find("failure") is not None or case.find("error") is not None:
            result = "failed"
        counts[level][result] += 1
    modules = defaultdict(lambda: [0, 0])
    for filename, data in coverage["files"].items():
        parts = filename.replace("\\", "/").split("/")
        module = parts[2] if len(parts) > 2 and parts[1] == "modules" else "shared"
        modules[module][0] += data["summary"]["covered_lines"]
        modules[module][1] += data["summary"]["num_statements"]
    pieces = ["""# 1. DIAGNÓSTICO ARQUITECTÓNICO Y DE TESTABILIDAD DEL MÓDULO

## 1.1 Lenguaje, Runtime y Framework detectado

Alcance: los diez módulos de PuntoVenta Total y shared; revisión estática de configuración, capas,
seguridad y pruebas; ejecución de toda la suite disponible el 16/10/2026.
No equivale a verificar exhaustivamente cada combinación ni a una certificación ISO.

| Elemento | Declarado en producción | Observado en esta ejecución |
|---|---|---|
| Runtime | Python >=3.11 | CPython 3.14.7, Windows |
| Framework | Django 5.0.6, DRF 3.15.1 | Django 6.1.2, DRF 3.18.3 |
| Persistencia | MySQL 8 | SQLite temporal; MySQL no ejecutado |
| Tareas/caché | Celery 5.4.0, Redis 5.0.4 | eager/locmem en testing |
| QA | requirements/testing.txt incompleto para la suite actual | requirements/qa-inventory.txt |

La diferencia de versiones impide extrapolar los resultados al entorno de producción declarado.
Los números de versión anteriores proceden de archivos y paquetes locales; no son una recomendación
de compatibilidad futura. No se asume disponibilidad de productos de 2027.

## 1.2 Mapa de Dependencias del Módulo

| Módulo | Dependencias/negocio | Aislar en unitarias | Infraestructura real pendiente o requerida |
|---|---|---|---|
| identity | usuarios, roles, hash, sesión | repositorio y hasher | ORM, login, CSRF, expiración/revocación de roles |
| catalog | productos, categorías, disponibilidad | producto repo, disponibilidad port, caché | ORM, templates, navegador, Redis |
| inventory | existencias, lotes, reservas, kardex | repositorios, notificador, reloj | InnoDB, bloqueos, rollback y commit |
| sales | pagos, IGV, descuentos, ticket | inventario, auditoría, repositorios | venta-pago-stock atómicos, PDF real |
| cash_register | apertura, movimientos, arqueo/cierre | turno repo, ventas port, reloj | turnos simultáneos y permisos |
| orders | carrito, reserva, checkout, recojo | inventario, notificador, pedido repo | sesiones, ORM, worker y entrega |
| customers | contacto, fidelidad, historial | repositorio | propiedad de perfil/historial y PII |
| promotions | vigencia, descuentos, frecuencia | frecuencia port, repositorio, reloj | ORM y tarea de actualización |
| reporting | rangos, ventas, utilidad, exportadores | reporte repo y exportador | consultas reales y PDF/CSV |
| auditing | registro y rastreo | repositorio | persistencia, acceso por rol e integridad |
| shared | monto, DNI, UoW, eventos, cifrado | reloj/event publisher | Redis y Celery reales |

## 1.3 Deuda Técnica o Problemas de Testabilidad

| ID | Prioridad | Evidencia | Acción propuesta |
|---|---|---|---|
| AUD-02 | Alta | Un CLIENTE autenticado obtiene HTTP 200 del perfil de otro cliente | Vincular usuario de dominio a cliente y exigir propietario o rol autorizado, también en POST/historial |
| AUD-01 | Media | login con next=https://example.invalid/ redirige al host externo | Validar destino con url_has_allowed_host_and_scheme y fallback local |
| AUD-03 | Media | /pos/ventas/?pagina=abc devuelve 500 | Parseo defensivo y respuesta 400 o página normalizada |
| AUD-04 | Alta | settings.testing siempre SQLite; cinco casos InnoDB omitidos | Ejecutar wrapper MySQL en CI y no contar skips como evidencia |
| AUD-05 | Media | workflow anidado omite integración/system/UAT y usa ruff no instalado | Workflow raíz con cuatro etapas y dependencias reproducibles |
| AUD-06 | Media | k6_cobro comparte login de setup sin cookies por VU, sigue redirect pero espera 302 | Sesión/CSRF por VU, producto/usuario aislados y redirects:0 al comprobar redirección |
| AUD-07 | Media | datetime.now sin zona genera warnings con USE_TZ | Reloj inyectado/aware y escenarios en cambio de día |
| AUD-08 | Media | SmsNotifier solo escribe log y devuelve True | No declarar entrega SMS; implementar proveedor y pruebas de recuperación |

AUD-01/02/03 se reprodujeron con tests nuevos: 3 fallidos y 9 aprobados usando --runxfail.
Los defectos siguen abiertos. Sus xfail(strict=True) documentan deuda; CI usa --runxfail para bloquearlos.
El login del caso AUD-01 aísla AutenticarUsuario, y prueba la vista real de redirección; no valida credenciales.
AUD-02 usa usuario, sesión, vista y BD reales, sin mock del control de acceso.
También se observan factories construidas dentro de vistas; favorecen integración pero dificultan
aislamiento. Mantener puertos e introducir inyección en límites concretos, sin reescribir toda la arquitectura.

`manage.py check` pasó. Ruff no está instalado; pyflakes devolvió avisos de imports/redefiniciones.
Algunos son reexportaciones ORM o fixtures intencionales; no todos representan defectos funcionales.
Hubo un warning de limpieza SQLite por archivo ocupado: no se puede prometer zero-flakiness.

# 2. MATRIZ DE APLICATIVOS Y HERRAMIENTAS REQUERIDAS (STACK 2026-2027)

| Nivel de Prueba | Librería / Framework Principal | Aplicativo / Motor Necesario | Propósito en el Módulo | Comando de Instalación |
| :--- | :--- | :--- | :--- | :--- |
| Unit | pytest 9.1.1, Hypothesis 6.169.4, pytest-cov 7.1.0 | Python 3.14.7 | Dominio/casos de uso | python -m pip install -r requirements/qa-inventory.txt |
| Integration | pytest-django 4.14.0, testcontainers 4.15.0, mysqlclient 2.3.0 | Docker Desktop, MySQL 8.4.3 efímero | Transacciones y concurrencia | python -m pip install -r requirements/qa-inventory-mysql.txt |
| System | Playwright 1.64.0, pytest | Chromium | POS, inventario y catálogo UI | python -m playwright install chromium |
| Performance | k6 (CLI; versión no verificada localmente) | k6, despliegue QA | Lectura concurrente y p95 | winget install --id GrafanaLabs.k6 --exact |
| UAT | pytest-bdd 9.0.0 | Python y responsable de negocio | Gherkin de reglas reales | python -m pip install -r requirements/qa-inventory.txt |

Instalar Docker Desktop mediante `winget install --id Docker.DockerDesktop --exact`, abrirlo y
verificar `docker info`. Instalación no realizada durante esta auditoría.
No es necesario Postman Desktop para ejecutar la suite Django. Postman CLI puede complementar
contratos HTTP si se mantiene una colección; aquí no se creó una conexión de workspace ni se publicó nada.

Desde la raíz del repositorio, PowerShell (usar `rtk proxy` ante los comandos conforme a RTK.md):

```powershell
Set-Location puntoventa_total
rtk proxy python -m venv .venv
rtk proxy .venv/Scripts/python.exe -m pip install -r requirements/qa-inventory-mysql.txt
rtk proxy .venv/Scripts/python.exe -m playwright install chromium
```

Si el entorno .venv ya existe, conservarlo y omitir su creación. No instalar paquetes QA en producción.

# 3. ESTRUCTURA DE DIRECTORIOS DE TESTING (SCAFFOLDING)

```text
proyecto_ventas/
|-- .github/workflows/full-quality.yml       # nuevo gate transversal
|-- .cursor/rules/full-testing.mdc          # regla del agente
`-- puntoventa_total/
    |-- requirements/qa-inventory[-mysql].txt
    |-- config/settings/testing[_mysql].py
    |-- scripts/qa_inventory_mysql.py
    |-- scripts/qa_full_report.py
    |-- tests/
    |   |-- conftest.py
    |   |-- factories/
    |   |-- unit/domain/test_auditoria_transversal.py
    |   |-- unit/{application,inventory,catalog}/
    |   |-- integration/test_auditoria_seguridad.py
    |   |-- integration/test_inventario_mysql.py
    |   |-- functional/
    |   |-- system/                         # HTTP + Chromium
    |   |-- e2e/
    |   |-- performance/k6_catalog_audit.js
    |   `-- uat/features/                   # Gherkin + steps ../test_*_bdd.py
    |-- reports/audit_*                     # evidencia local
    `-- docs/testing/full_master_audit.md   # este informe
```

# 4. NIVEL 1: PRUEBAS UNITARIAS (UNIT TESTING)

## 4.1 Qué se evalúa en este módulo

Entidades de venta/producto/stock/pedido, pagos parciales, IGV, descuentos, anulación y promociones.
Nuevos casos: privacidad de anonimización, canje de fidelidad, validaciones de contacto y límites de rangos.
Los tests unitarios no solicitan django_db; pytest-django bloquea ORM accidental.

## 4.2 Aplicativos y Librerías a usar

Python, pytest, unittest.mock; Hypothesis ya se usa en inventario. No requiere Docker.

## 4.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
rtk proxy .venv/Scripts/python.exe -m pip install -r requirements/qa-inventory.txt
rtk proxy .venv/Scripts/python.exe -m pytest tests/unit -q -p no:cacheprovider
```

Ejecución aislada: **219 aprobados**. Cobertura exclusivamente unitaria de dominio/aplicación:
**1885/2095 líneas = 89.98%**. Gate mínimo 80% aprobado mediante scripts/qa_unit_gate.py.
El denominador incluye domain/application de todos los módulos y shared; no incluye infraestructura.
La cobertura de la tabla global incluye todos los niveles.

## 4.4 Código Completo del Test Unitario
"""]
    pieces.append(source("tests/unit/domain/test_auditoria_transversal.py"))
    pieces.append("""
# 5. NIVEL 2: PRUEBAS DE INTEGRACIÓN (INTEGRATION TESTING)

## 5.1 Qué se evalúa en este módulo

Repositorios, serialización, pago/stock, reservas, rollback, notificación tras commit,
consultas de catálogo y seguridad HTTP. Los cinco casos exclusivos de MySQL se omiten en SQLite.
Redis y workers Celery reales no quedaron verificados.

## 5.2 Aplicativos y Librerías a usar

Docker Desktop activo, testcontainers[mysql], PyMySQL y mysqlclient del perfil QA MySQL.
El wrapper existente crea y destruye su propio contenedor; no usar una BD de negocio.

## 5.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
rtk proxy docker info
rtk proxy .venv/Scripts/python.exe -m pip install -r requirements/qa-inventory-mysql.txt
rtk proxy .venv/Scripts/python.exe scripts/qa_inventory_mysql.py tests/integration --runxfail --junitxml=reports/mysql-integration.xml
```

Comando ejecutado localmente: wrapper terminó con código 2 por falta de Docker CLI/Desktop.
No se afirma aprobación MySQL. Para reproducir los defectos sin Docker:

```powershell
rtk proxy .venv/Scripts/python.exe -m pytest tests/integration/test_auditoria_seguridad.py --runxfail -q
```

## 5.4 Código Completo del Test de Integración
""")
    pieces.append(source("tests/integration/test_auditoria_seguridad.py"))
    pieces.append(source("scripts/qa_inventory_mysql.py"))
    pieces.append("""
# 6. NIVEL 3: PRUEBAS DE SISTEMA (SYSTEM / E2E & PERFORMANCE)

## 6.1 Qué se evalúa en este módulo

Login real, apertura de caja, búsqueda por código, cobro, PDF, descuento de stock,
inventario y catálogo en navegador. Las pruebas HTTP con Django Client no equivalen a un despliegue
Nginx/Gunicorn/MySQL/Redis; faltan estrés y fallos de infraestructura en ese entorno.

## 6.2 Aplicativos y Librerías a usar

Playwright/Chromium para UI. k6 para carga HTTP con thresholds; un check aislado no basta
para hacer fallar k6. [Documentación oficial de thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/).
Se reutilizan fixtures de datos, sesiones y trazas existentes.

## 6.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
rtk proxy .venv/Scripts/python.exe -m playwright install chromium
$env:QA_REQUIRE_BROWSER = '1'
rtk proxy .venv/Scripts/python.exe -m pytest tests/system tests/e2e tests/functional tests/performance -q
# Solo contra QA preparado; no se levanto un despliegue para k6 en esta auditoria:
rtk proxy k6 run -e BASE_URL=http://127.0.0.1:8000 tests/performance/k6_catalog_audit.js
```

El presupuesto inicial del nuevo script es p95<500ms, cinco VUs y 20 segundos;
requiere ratificación de negocio y una máquina de referencia. No es una medición obtenida.
El catálogo QA debe tener productos, ser público y no redirigir a login.
El script de cobro anterior requiere corregir sesión/CSRF por VU y redirecciones antes de usarlo como gate.

## 6.4 Código Completo del Test de Sistema (E2E) + Script rápido de Carga/Performance
""")
    pieces.append(source("tests/system/test_e2e_pos_playwright.py"))
    pieces.append(source("tests/performance/k6_catalog_audit.js", "javascript"))
    pieces.append("""
# 7. NIVEL 4: PRUEBAS DE ACEPTACIÓN (UAT / BDD)

## 7.1 Escenarios de Negocio en Formato Gherkin

Se conserva la feature real de ventas (cinco escenarios), junto con inventario y catálogo existentes.
""")
    pieces.append(source("tests/uat/features/ventas_pos.feature", "gherkin"))
    pieces.append("""
## 7.2 Automatización del UAT (Step Definitions) o Checklist de Validación Manual

Los steps de ventas validan reglas con puertos externos simulados; no prueban entrega de SMS,
stock persistido ni permisos UI. Esas garantías corresponden a integración/sistema.
""")
    pieces.append(source("tests/uat/test_ventas_bdd.py"))
    pieces.append("""
## 7.3 Guía Paso a Paso para ejecutar y aprobar el UAT

```powershell
rtk proxy .venv/Scripts/python.exe -m pytest tests/uat -q --junitxml=reports/uat-approval.xml
```

El responsable debe registrar versión/commit, entorno, fecha, datos, evidencias y firma:

| Validación manual | Criterio verificable | Estado |
|---|---|---|
| Cobro efectivo | Total correcto, vuelto y PDF; stock disminuye una sola vez | Pendiente PO |
| Pago parcial | No cierra venta ni descuenta stock antes de pago completo | Pendiente PO |
| Anulación gerente | Devuelve stock una vez y deja auditoría | Pendiente PO |
| Inventario | Recepción/merma/kardex coherentes y aviso tras commit | Pendiente PO |
| Catálogo | Búsqueda/categoría muestran disponibilidad correcta | Pendiente PO |
| Perfil de cliente | Otro cliente no puede leer ni modificar PII | Bloqueado AUD-02 |

Los BDD verdes no sustituyen aprobación humana del valor de negocio.

# 8. GUÍA DE AI SKILLS, MCP Y AUTOMATIZACIÓN AGÉNTICA (CONTEXTO 2026-2027)

## 8.1 Configuración de Skill / Rule para el Agente de Código

Regla instalada en la raíz del repositorio:
""")
    pieces.append(source("../.cursor/rules/full-testing.mdc", "markdown"))
    pieces.append("""
## 8.2 Servidores MCP recomendados

1. Reutilizar pytest como fuente de verdad y dar al agente JUnit/cobertura/trazas locales.
2. Opcional: [Playwright MCP oficial](https://github.com/microsoft/playwright-mcp) para inspeccionar
   accesibilidad y seleccionar controles por rol/nombre; convertir lo observado en tests versionados.
   Instalarlo en el cliente MCP elegido siguiendo su README y fijar versión antes de compartir configuración.
3. Para estado MySQL, preferir fixtures ORM y consultas de solo lectura sobre BD efímera.
   Un servidor PostgreSQL no valida este proyecto MySQL. No se instaló un MCP de BD ni se afirma su compatibilidad.
4. GitHub MCP puede aportar diff/PR/estado de checks; requiere conexión y permisos del usuario.
   No es necesario para ejecutar estos tests ni está configurado por este trabajo.
5. Skills aplicadas: [api-engineer](C:/Users/mallq/.codex/plugins/cache/postman/postman/1.1.0/skills/api-engineer/SKILL.md)
   y [api-testing](C:/Users/mallq/.codex/plugins/cache/postman/postman/1.1.0/skills/api-testing/SKILL.md).
   Se eligió la suite HTTP existente en vez de duplicar contratos en un workspace externo.

No se presupone que herramientas comerciales de 2027 existan o estén disponibles en esta cuenta.

## 8.3 Flujo de Auto-Healing (Autoreparación de Tests)

Ejecutar el comando real, entregar salida al agente y revisar el diff propuesto:

```powershell
rtk proxy .venv/Scripts/python.exe -m pytest tests/integration/test_auditoria_seguridad.py --runxfail -q --junitxml=reports/security-regression.xml
```

Instrucción reutilizable para el agente: «Lee full-testing.mdc y los requisitos. Reproduce el fallo
de JUnit con el menor caso. Distingue defecto de aplicación, fixture o selector. Propón la corrección
sin relajar permisos/assertions. Ejecuta regresión y suite afectada; presenta diff y evidencia».
No es una integración automática instalada ni una orden CLI inventada.
Para fallos UI, abrir la traza con `python -m playwright show-trace ruta.zip`;
el [Trace Viewer oficial](https://playwright.dev/python/docs/trace-viewer-intro) permite revisar acciones y snapshots.
Cambios de negocio requieren criterios revisados; no autoaprobarlos cambiando el resultado esperado.

# 9. PIPELINE CI/CD (QUALITY GATES)

Workflow nuevo en la raíz real del repositorio. Corre cuatro niveles secuenciales, cobertura
unitaria dominio/aplicación >=80% y cobertura global >=80%; falla ante AUD-01/02/03 mediante --runxfail.
No fue ejecutado en GitHub desde esta sesión.
Los archivos .github dentro de puntoventa_total no son workflows raíz detectados por GitHub en este layout.
No se borraron ni modificaron workflows anteriores ni los cambios locales de catálogo.
El gate unitario lee reports/audit_unit_coverage.json, generado ejecutando solo tests/unit;
el umbral global se calcula por separado al ejecutar toda la suite.
La repetición final permite medir cobertura conjunta sin mezclar artefactos entre BD diferentes.
El gate queda rojo ante defectos actuales: es comportamiento intencional de auditoría.

Para bloquear merge hay que marcar `Full quality audit / quality` como check requerido en el ruleset
de la rama. El YAML no configura por sí mismo esa protección.
[Documentación de ramas protegidas](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
""")
    pieces.append(source("../.github/workflows/full-quality.yml", "yaml"))
    pieces.append("""
# 10. MATRIZ DE TRAZABILIDAD DE PRUEBAS DEL MÓDULO

Todos los comandos parten de puntoventa_total y usan el Python del entorno QA.

| ID Caso | Funcionalidad / Método del Módulo | Nivel | Tipo | Resultado Esperado | Comando de Ejecución |
|---|---|---|---|---|---|
| CLI-01 | Cliente.canjear_puntos | Unit | Positivo/Negativo | Canje resta saldo; exceso no muta | python -m pytest tests/unit/domain/test_auditoria_transversal.py -q |
| CLI-02 | Cliente.anonimizar | Unit | Positivo | Contacto vacío y cuenta inactiva | python -m pytest tests/unit/domain/test_auditoria_transversal.py -q |
| REP-01 | RangoFechas | Unit | Borde/Negativo | Febrero bisiesto, rechazo rango invertido/excesivo | python -m pytest tests/unit/domain/test_auditoria_transversal.py -q |
| VEN-01 | ProcesarPago | Unit | Positivo/Negativo | Cierre y stock solo al completar | python -m pytest tests/unit/application/test_procesar_pago.py -q |
| INV-01 | existencia/lotes/reservas | Unit | Borde | No sobrerreserva ni cantidades inválidas | python -m pytest tests/unit/inventory -q |
| PRO-01 | promociones | Unit | Positivo/Negativo | Descuentos y condiciones válidas | python -m pytest tests/unit/domain/test_promocion.py -q |
| INT-01 | venta/stock | Int | Negativo | Pago parcial conserva stock | python -m pytest tests/integration/test_transaccion_venta_stock.py -q |
| INT-02 | InnoDB | Int | Concurrencia | Lock/rollback sin sobreventa | python scripts/qa_inventory_mysql.py tests/integration/test_inventario_mysql.py |
| CAT-01 | catálogo ORM | Int | Positivo/Borde | Filtros y disponibilidad | python -m pytest tests/integration/test_catalogo_web.py -q |
| AUD-01 | login next | Int | Negativo | Destino externo rechazado; hoy FALLA | python -m pytest tests/integration/test_auditoria_seguridad.py --runxfail -q |
| AUD-02 | perfil ajeno | Int | Negativo | 403/404; hoy FALLA con 200 | python -m pytest tests/integration/test_auditoria_seguridad.py --runxfail -q |
| AUD-03 | ventas página inválida | Int | Borde | 200 normalizado o 400; hoy FALLA con 500 | python -m pytest tests/integration/test_auditoria_seguridad.py --runxfail -q |
| SYS-01 | POS UI | Sys | Positivo | Login/caja/cobro/PDF/stock | python -m pytest tests/system/test_e2e_pos_playwright.py -q |
| SYS-02 | inventario UI | Sys | Positivo | Flujo almacenero | python -m pytest tests/system/test_inventario_playwright.py -q |
| SYS-03 | pedido web | Sys | Positivo | Confirmación y reserva | python -m pytest tests/e2e/test_pedido_web.py -q |
| SYS-04 | cierre caja | Sys | Positivo | Cierre/arqueo | python -m pytest tests/e2e/test_cierre_caja.py -q |
| PERF-01 | catálogo público | Sys | Carga | checks=100%, errores=0, p95<500ms; pendiente | k6 run -e BASE_URL=http://127.0.0.1:8000 tests/performance/k6_catalog_audit.js |
| UAT-01 | cobro/anulación/descuento | UAT | Positivo/Negativo/Borde | Reglas Gherkin y aprobación PO | python -m pytest tests/uat/test_ventas_bdd.py -q |
| UAT-02 | stock/kardex/alerta | UAT | Positivo/Negativo | Reglas de inventario | python -m pytest tests/uat/test_inventario_bdd.py -q |
| UAT-03 | catálogo | UAT | Positivo/Borde | Reglas de catálogo | python -m pytest tests/uat/test_catalogo_web_bdd.py -q |

La matriz cubre casos de referencia; el JUnit contiene el inventario completo de pruebas ejecutadas.
Clientes, identidad, caja, reportes y auditoría requieren ampliar pruebas directas y negativas;
su cobertura indirecta no demuestra todas sus reglas.

Evidencia por directorio (categorías de archivo; algunos tests tienen múltiples markers):

| Directorio | Aprobados | Fallidos | Omitidos | Xfail |
|---|---:|---:|---:|---:|
""")
    for level, data in sorted(counts.items()):
        pieces.append(f"| {level} | {data['passed']} | {data['failed']} | {data['skipped']} | {data['xfail']} |\n")
    pieces.append("\nCobertura de líneas por módulo, sumando todos los niveles (no branches):\n\n| Módulo | Líneas cubiertas/ejecutables | Cobertura |\n|---|---:|---:|\n")
    for module, (covered, total) in sorted(modules.items()):
        pieces.append(f"| {module} | {covered}/{total} | {100 * covered / total if total else 0:.2f}% |\n")
    pieces.append(f"""

Suite inicial: **341 passed, 5 skipped**, cobertura **79.76%**, salida 1 por gate.
Suite tras agregar 12 casos: **350 passed, 5 skipped, 3 xfailed**, cobertura
**{coverage['totals']['percent_covered']:.2f}%**, salida 0. Unitaria aislada: **219 passed**.
Regresiones con --runxfail: **3 failed, 9 passed**, salida 1.
No se ocultó un arreglo en producción: los tres defectos permanecen reproducibles.
La cobertura sube por casos nuevos de clientes/reportes y ejecución de vistas negativas;
eso no implica que los defectos estén corregidos.

Artefactos: reports/audit_all_junit.xml, audit_coverage.json (antes), audit_final_junit.xml,
audit_final_coverage.json/xml (después), audit_findings.xml y audit_unit_junit.xml.
La cobertura omite migraciones, apps.py, models.py de reexportación y tests según pyproject.toml.
La ejecución completa detectó 23 warnings: revisar fechas naive, deprecaciones y limpieza SQLite.

# EVALUACIÓN FINAL DEL MÓDULO AUDITADO

Puntuación técnica orientativa, basada en evidencia de esta revisión; no es una métrica certificada.

- **Testabilidad del Código Actual** ............ 7/10
- **Cobertura Unitaria Alcanzable** ............. 8/10 (potencial estimado, no cobertura medida)
- **Aislamiento de Dependencias** ............... 6/10
- **Preparación para CI/CD** .................... 5/10 (workflow creado, ejecución remota pendiente)
- **Resiliencia ante Fallos (Edge Cases)** ...... 5/10

# ESTADO DE CALIDAD (QUALITY READINESS)

- **Unit Test Ready** → ✅ Listo para ejecutar; faltan reglas de módulos menos cubiertos.
- **Integration Ready** → ⚠ Requiere validar MySQL/Redis/workers y corregir seguridad.
- **System / E2E Ready** → ⚠ Navegador local aprobado; despliegue/carga real pendientes.
- **UAT / Business Ready** → ❌ No aprobado: defectos abiertos y firma PO pendiente.

Prioridad: corregir AUD-02, AUD-01 y AUD-03 con sus regresiones; después ejecutar MySQL,
alinear runtime de QA/producción, validar Redis/Celery y medir carga en despliegue QA.
No se garantiza zero-flakiness ni se declara el sistema listo para producción.
""")
    destination = ROOT / "docs/testing/full_master_audit.md"
    body = "".join(pieces)
    notice = ("\n> Auditoria inicial: consultar [full_fixes_results.md](full_fixes_results.md) "
              "para el estado posterior a las correcciones. Los resultados historicos no son el estado actual.\n")
    if (ROOT / "docs/testing/full_fixes_results.md").exists():
        body = body.replace("## 1.1 Lenguaje", notice + "\n## 1.1 Lenguaje", 1)
    destination.write_text(body, encoding="utf-8")
    print(f"Informe: {destination}; cobertura {coverage['totals']['percent_covered']:.2f}%")


if __name__ == "__main__":
    main()
