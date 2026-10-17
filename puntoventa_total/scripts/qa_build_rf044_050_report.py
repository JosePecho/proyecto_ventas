"""Genera el plan del módulo 3.6 con código versionado y evidencia local."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PARTES = []


def texto(contenido):
    PARTES.append(contenido.strip())


def codigo(ruta, lenguaje="python"):
    texto(f"**Archivo: `{ruta}`**\n\n```{lenguaje}\n{(ROOT / ruta).read_text(encoding='utf-8').rstrip()}\n```")


texto("""
# 1. DIAGNÓSTICO ARQUITECTÓNICO Y DE TESTABILIDAD DEL MÓDULO

## 1.1 Lenguaje, Runtime y Framework detectado

Módulo 3.6, RF-044 a RF-050. Revisión del 17/10/2026 sobre Python/Django,
monolito modular con dominio, aplicación, infraestructura y presentación HTML.
Perfil declarado: Python 3.11.16, Django 5.0.6, Celery 5.4.0; QA instalado:
Python 3.14.7, Django 6.1.2, pytest 9.1.1, pytest-django 4.14.0.
MySQL/InnoDB 8.4.3 es el motor de integración. SQLite se usa solo para iteración rápida.
Las rutas son formularios HTML autenticados por sesión y CSRF, no una API JSON.
No se presentan novedades futuras de 2027 como comprobadas.

Django 5.0 está sin soporte: aprobar pruebas no acredita seguridad productiva.
La actualización de dependencias queda pendiente, separada de estas correcciones.
[Tabla oficial de soporte de Django](https://www.djangoproject.com/download/).

## 1.2 Mapa de Dependencias del Módulo

| Componente | Unit: aislar | Integración/Sistema: infraestructura real |
|---|---|---|
| Reporting | Mock del puerto ReporteRepository; cálculos y rangos puros | ORM sobre ventas PAGADA, pagos, costos congelados, filtros de fecha |
| Identity | Entidad Usuario pura | Hasher, creación/edición/baja, sesiones, protección del último administrador |
| Catalog | Entidad Categoria pura | Creación y edición con permisos y auditoría |
| Auditing | Mock de AuditoriaRepository; entidad y DTO reales | Señales, transacción, actor, acción, fecha y filtros |
| UI | No navegador en Unit | Chromium, servidor Django, CSRF y sesión reales |
| Carga | No red en Unit | k6 contra servidor aislado, sesiones ADMIN y CLIENTE |

Este módulo no necesita APIs externas ni Redis para sus pruebas específicas.
Los fixtures reutilizan ventas y clientes del proyecto, sin tocar datos del negocio.

## 1.3 Deuda Técnica o Problemas de Testabilidad

| Hallazgo reproducido | Corrección / estado |
|---|---|
| RF-047 no incluía porcentaje por producto | Se agrega margen sobre ingresos, con ROUND_HALF_UP; también se homogeneiza el redondeo del total |
| Auditoría convertía página/fechas sin validación | Formulario valida enteros positivos, UUID, fechas y orden; errores devuelven 400 |
| Middleware escribe CREAR/ACTUALIZAR/ELIMINAR, pero el dominio las rechazaba al consultar | Se incorporan al catálogo de acciones válidas; acciones arbitrarias siguen rechazadas |
| El filtro HTTP de actor no llegaba al repositorio | Se propaga usuario_id validado y se expone en pantalla |
| Reportes materializan líneas en memoria y serializan montos como float | Deuda existente: probar volúmenes representativos y conservar Decimal hasta serializar en una mejora posterior |
| Consulta de auditoría tiene límite de 100 eventos | Límite existente; no se afirma paginación exhaustiva de historiales mayores |

El contrato detallado está en `docs/requirements/reportes_admin_rf044_rf050.md`.
Margen = utilidad/ingresos*100; el margen global pondera ingresos, no promedia porcentajes.
Costo desconocido o ingreso cero deja el margen del producto no disponible; no se inventan costos.
La utilidad global con históricos incompletos conserva su advertencia de resultado parcial.

# 2. MATRIZ DE APLICATIVOS Y HERRAMIENTAS REQUERIDAS (STACK 2026-2027)

| Nivel de Prueba | Librería / Framework Principal | Aplicativo / Motor Necesario | Propósito en el Módulo | Comando de Instalación |
|---|---|---|---|---|
| Unit | pytest 8.2.0, pytest-cov 5.0.0, unittest.mock; Hypothesis 6.169.4 | Python 3.11 | Rangos, márgenes, usuarios, categorías, acciones y propiedades monetarias | `rtk proxy python -m pip install -r requirements/testing.txt` |
| Integration | pytest-django 4.8.0, testcontainers[mysql] 4.15.0, mysqlclient 2.2.4 | Docker Desktop con motor Linux y MySQL 8.4.3 | ORM, transacciones, filtros y permisos | Mismo requirements; [instalar Docker](https://docs.docker.com/desktop/setup/install/windows-install/) e iniciar motor |
| System/E2E | Playwright 1.64.0 | Chromium | Utilidad visible, CRUD de usuarios, categorías y auditoría | `rtk proxy python -m playwright install chromium` |
| Performance | k6 2.3.0 | CLI k6 | Dos roles, p95 HTTP <500 ms, checks 100% | `rtk proxy python scripts/qa_download_tools.py k6 --asset k6-v2.3.0-windows-amd64.zip` |
| UAT | pytest-bdd 9.0.0 | CLI pytest | Seis escenarios de negocio del módulo | Incluido en requirements/testing.txt |

Versiones anteriores corresponden al perfil declarado; el perfil QA tiene sus pins en
`requirements/qa-inventory-mysql.txt` y `requirements/qa-inventory.txt`. No mezclar entornos.

# 3. ESTRUCTURA DE DIRECTORIOS DE TESTING (SCAFFOLDING)

```text
proyecto_ventas/
|-- .cursor/rules/reporting-admin-testing.mdc
|-- .github/workflows/full-quality.yml
`-- puntoventa_total/
    |-- tests/unit/application/test_reportes_administracion.py
    |-- tests/integration/test_reportes_administracion.py
    |-- tests/integration/test_rf030_050_contratos.py
    |-- tests/integration/test_rf038_050.py
    |-- tests/system/test_reportes_administracion_playwright.py
    |-- tests/system/test_rf038_050_k6.py
    |-- tests/performance/k6_reportes.js
    |-- tests/uat/features/reportes_administracion.feature
    |-- tests/uat/features/reportes_administracion_contratos.feature
    |-- tests/uat/test_reportes_administracion_bdd.py
    |-- tests/uat/test_reportes_administracion_contratos_bdd.py
    |-- scripts/qa_reportes_unit_gate.py
    |-- scripts/qa_build_rf044_050_report.py
    |-- docs/requirements/reportes_admin_rf044_rf050.md
    |-- docs/testing/plan_maestro_rf044_050.md
    `-- reports/ (JUnit, cobertura, k6 y traces; ignorado por Git)
```

# 4. NIVEL 1: PRUEBAS UNITARIAS (UNIT TESTING)

## 4.1 Qué se evalúa en este módulo

Margen positivo, pérdida, ingresos cero, costos desconocidos, empate decimal 3.125 → 3.13,
total ponderado, fecha inválida, tickets e IGV, acciones de auditoría, trazas inexistentes,
revocación en todos los roles y rechazo de un nombre vacío sin modificar la categoría.
La suite existente añade propiedades Hypothesis de conservación de centavos.

## 4.2 Aplicativos y Librerías a usar

Pytest, unittest.mock, pytest-cov e Hypothesis. El plugin Django impide acceso a BD en Unit.

## 4.3 Guía Paso a Paso de Configuración y Ejecución

Desde `puntoventa_total`, con Python 3.11 instalado:

```powershell
rtk proxy py -3.11 -m venv .venv-rf044-050
rtk proxy .venv-rf044-050/Scripts/python.exe -m pip install -r requirements/testing.txt
rtk proxy .venv-rf044-050/Scripts/python.exe -m pytest tests/unit -q -p no:cacheprovider --cov=src --cov-fail-under=0 --cov-report=json:reports/audit_unit_coverage.json --junitxml=reports/rf044-050-unit.xml
rtk proxy .venv-rf044-050/Scripts/python.exe scripts/qa_unit_gate.py
rtk proxy .venv-rf044-050/Scripts/python.exe scripts/qa_reportes_unit_gate.py
```

Se ejecutan todas las unitarias como regresión. El segundo gate mide doce archivos
de núcleo explícitos e incluye los no importados; mínimo 80%. No acredita cobertura
unitaria de todas las vistas/adaptadores de Identity y Catalog.
[API pública analysis2 de coverage.py](https://coverage.readthedocs.io/en/latest/api_coverage.html#coverage.Coverage.analysis2).

## 4.4 Código Completo del Test Unitario
""")
codigo("tests/unit/application/test_reportes_administracion.py")
codigo("scripts/qa_reportes_unit_gate.py")
texto("""
# 5. NIVEL 2: PRUEBAS DE INTEGRACIÓN (INTEGRATION TESTING)

## 5.1 Qué se evalúa en este módulo

Ventas diarias y rango local, pagos, ranking cantidad/monto, costo histórico y márgenes,
usuarios, categorías, actor/acción/fecha, permisos y rollback al fallar auditoría.
Las pruebas existentes de RF-048 verifican revocación de sesiones y del último administrador.

## 5.2 Aplicativos y Librerías a usar

Django Client, ORM real, MySQL/InnoDB con Testcontainers.
Este equipo no tiene Docker: se valida con MySQL nativo efímero; no se etiqueta como
Testcontainers ejecutado. SQLite no demuestra bloqueos de InnoDB.

## 5.3 Guía Paso a Paso de Configuración y Ejecución

Con Docker instalado e iniciado, usar el wrapper existente que crea y elimina MySQL:

```powershell
rtk proxy docker info
rtk proxy .venv-rf044-050/Scripts/python.exe scripts/qa_inventory_mysql.py tests/integration/test_reportes_administracion.py tests/integration/test_rf038_050.py tests/integration/test_rf030_050_contratos.py --junitxml=reports/rf044-050-integration.xml
```

El wrapper usa [MySqlContainer](https://testcontainers-python.readthedocs.io/en/latest/modules/mysql/README.html).
No requiere credenciales de la base del negocio.

## 5.4 Código Completo del Test de Integración
""")
codigo("tests/integration/test_reportes_administracion.py")
codigo("tests/integration/test_rf030_050_contratos.py")
codigo("tests/integration/test_rf038_050.py")
texto("""
# 6. NIVEL 3: PRUEBAS DE SISTEMA (SYSTEM / E2E & PERFORMANCE)

## 6.1 Qué se evalúa en este módulo

Por navegador: margen por producto, creación/edición/baja de usuario y creación/edición
de categoría con auditoría consultable. Bajo carga: administrador ve reportes y CLIENTE
es redirigido sin recibir su contenido. Es un smoke test de carga, no capacidad máxima.

## 6.2 Aplicativos y Librerías a usar

Playwright/Chromium, k6 y servidor Django real sobre MySQL. El fixture existente bloquea
CDN, usa esperas de elementos y conserva traces; no sincroniza la UI con sleeps.

## 6.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
rtk proxy .venv-rf044-050/Scripts/python.exe -m playwright install chromium
rtk proxy .venv-rf044-050/Scripts/python.exe scripts/qa_download_tools.py k6 --asset k6-v2.3.0-windows-amd64.zip
$env:QA_REQUIRE_BROWSER = '1'
$env:QA_K6_BINARY = 'C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/k6/v2.3.0/k6-v2.3.0-windows-amd64/k6.exe'
rtk proxy .venv-rf044-050/Scripts/python.exe scripts/qa_inventory_mysql.py tests/system/test_reportes_administracion_playwright.py tests/system/test_rf038_050_k6.py --junitxml=reports/rf044-050-system.xml
```

En otro equipo usar la ruta de k6 devuelta por el descargador. El test crea sesiones
efímeras y lanza el script k6 con datos reales; no ejecutar el JS sin esas sesiones.
Los [thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/) hacen fallar CI
si hay checks fallidos, errores inesperados o p95 >=500 ms. Ejecutar cargas secuencialmente.
Traces en `reports/browser/*.zip`, con datos/cookies de QA: artifacts privados de retención corta.

## 6.4 Código Completo del Test de Sistema (E2E) + Script rápido de Carga/Performance
""")
codigo("tests/system/test_reportes_administracion_playwright.py")
codigo("tests/system/test_rf038_050_k6.py")
codigo("tests/performance/k6_reportes.js", "javascript")
texto("""
# 7. NIVEL 4: PRUEBAS DE ACEPTACIÓN (UAT / BDD)

## 7.1 Escenarios de Negocio en Formato Gherkin
""")
codigo("tests/uat/features/reportes_administracion.feature", "gherkin")
codigo("tests/uat/features/reportes_administracion_contratos.feature", "gherkin")
texto("## 7.2 Automatización del UAT (Step Definitions) o Checklist de Validación Manual para el Product Owner / Cliente")
codigo("tests/uat/test_reportes_administracion_bdd.py")
codigo("tests/uat/test_reportes_administracion_contratos_bdd.py")
texto("""
## 7.3 Guía Paso a Paso para ejecutar y aprobar el UAT

```powershell
rtk proxy .venv-rf044-050/Scripts/python.exe scripts/qa_inventory_mysql.py tests/uat/test_reportes_administracion_bdd.py tests/uat/test_reportes_administracion_contratos_bdd.py --junitxml=reports/rf044-050-uat.xml
```

El PO debe aprobar: (1) que margen significa porcentaje sobre ventas, (2) presentación
de históricos incompletos, (3) permisos de GERENTE, (4) totales por método, ranking y
fechas locales, (5) actor y fecha de cambios y (6) revocación de acceso. Registrar
commit, fecha, aprobador, resultado e incidencias. BDD verde no sustituye esa aprobación.

# 8. GUÍA DE AI SKILLS, MCP Y AUTOMATIZACIÓN AGÉNTICA (CONTEXTO 2026-2027)

## 8.1 Configuración de Skill / Rule para el Agente de Código

La regla versionada aporta contexto al editar archivos coincidentes; no es un hook
que ejecute tests automáticamente. CI ejecuta la validación ante cada PR.
""")
codigo("../.cursor/rules/reporting-admin-testing.mdc", "markdown")
texto("""
## 8.2 Servidores MCP (Model Context Protocol) recomendados

| Herramienta | Uso en este módulo | Límite |
|---|---|---|
| [Playwright MCP oficial](https://github.com/microsoft/playwright-mcp) | Inspeccionar UI y reproducir localizadores | Opcional, Node >=18; no sustituye assertions de pytest |
| [GitHub MCP oficial](https://github.com/github/github-mcp-server) | Leer checks y artifacts | Permisos de lectura; no publicar ni modificar protección sin tarea autorizada |
| ORM/MySQL CLI | Comprobar estado de datos efímeros | No necesita instalar un MCP PostgreSQL/SQLite ajeno al motor |
| Skills Postman api-engineer / api-testing / ci-integration | Guiar contratos, pruebas y gates HTTP | Instrucciones usadas; no se afirma colección ejecutada ni workspace publicado |
| Testcontainers Cloud | Alternativa a motor Docker local | Opcional; sin cuenta/licencia presumida |

Configuración MCP opcional según el arranque documentado por Microsoft:

```json
{"mcpServers":{"playwright":{"command":"npx","args":["@playwright/mcp@latest","--headless","--isolated"]}}}
```

Fijar la versión comprobada antes de usarla en CI. Limitar herramientas y credenciales
a QA; los permisos efectivos del servidor son el control de acceso.
[Guía de seguridad MCP](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices).

## 8.3 Flujo de Auto-Healing (Autoreparación de Tests)

1. Leer RF, contrato, JUnit, trace y resumen k6 del fallo.
2. Reproducir el nodo exacto antes de editar.
3. Corregir causa o localizador verificable; no relajar porcentaje, permisos ni presupuesto.
4. Ejecutar Unit → MySQL → Chromium/k6 → UAT y conservar evidencia antes/después.
5. Si cambió el criterio de negocio, solicitar revisión de ese criterio; nunca actualizar el oráculo para ocultar un fallo.

Con Claude Code instalado/autenticado, desde la raíz Git:

```powershell
rtk proxy claude -p "Lee .cursor/rules/reporting-admin-testing.mdc y puntoventa_total/docs/testing/plan_maestro_rf044_050.md. Reproduce el fallo adjunto, corrige su causa y valida los cuatro niveles. No reduzcas umbrales, no omitas casos ni publiques cambios. Reporta evidencias y pendientes."
```

Comando de revisión opcional; no se ejecutó ni se presupone licencia.
[Referencia oficial del CLI](https://code.claude.com/docs/en/cli-reference).

# 9. PIPELINE CI/CD (QUALITY GATES)

El workflow existente de la raíz descubre estos archivos y ejecuta los cuatro niveles
secuencialmente en ambos perfiles. Se añade un gate unitario de doce archivos del núcleo
RF-044..050, mínimo 80%, contando archivos no importados mediante analysis2.
CI rechaza skips/xfails y guarda artifacts siete días. La protección remota debe exigir
`quality (production-declared)` y `quality (qa)`; no fue verificada ni modificada aquí.
[Required status checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
La suite global tenía un fallo POS de latencia en la revisión anterior; aprobar este
módulo no acredita que ese fallo haya sido corregido. No se ejecutó CI remoto.
""")
codigo("../.github/workflows/full-quality.yml", "yaml")
texto("""
# 10. MATRIZ DE TRAZABILIDAD DE PRUEBAS DEL MÓDULO

Desde puntoventa_total con el entorno configurado:

| ID Caso | Funcionalidad / Método del Módulo | Nivel | Tipo | Resultado Esperado | Comando de Ejecución |
|---|---|---|---|---|---|
| RF044-01 | Dashboard diario | Int | Positivo/Borde | 40 soles, 2 tickets, efectivo 10/tarjeta 30; excluye ayer/anuladas | `rtk proxy python scripts/qa_inventory_mysql.py tests/integration/test_reportes_administracion.py::test_dashboard_del_dia_excluye_ayer_y_anuladas_y_desglosa_pagos` |
| RF045-01 | Rango local y filtros | Unit/Int/UAT | Negativo/Borde | Día completo Lima; inválidos 400 sin consulta engañosa | `rtk proxy python scripts/qa_inventory_mysql.py tests/integration/test_rf030_050_contratos.py` |
| RF046-01 | Ranking cantidad/monto | Int/UAT | Positivo | Orden cambia; anuladas no cuentan | `rtk proxy python scripts/qa_inventory_mysql.py tests/uat/test_reportes_administracion_contratos_bdd.py` |
| RF047-01 | Margen por producto/total | Unit/Int/Sys/UAT | Positivo/Negativo/Borde | 40%, pérdida -50%, empate 3.13%; costo desconocido sin porcentaje | `rtk proxy python -m pytest tests/unit/application/test_reportes_administracion.py -q` |
| RF048-01 | Crear/editar/desactivar usuarios | Int/Sys/UAT | Positivo/Negativo | Rol y datos guardados; baja revoca sesión; último admin protegido | `rtk proxy python scripts/qa_inventory_mysql.py tests/system/test_reportes_administracion_playwright.py::test_admin_crea_edita_y_desactiva_usuario_por_ui` |
| RF049-01 | Categoría creada/editada | Sys/UAT | Positivo | Nombres persistidos y ambas acciones auditadas | `rtk proxy python scripts/qa_inventory_mysql.py tests/system/test_reportes_administracion_playwright.py::test_categoria_creada_editada_y_auditada_con_actor` |
| RF050-01 | Actor, acciones, fechas y validación | Unit/Int/Sys/UAT | Positivo/Negativo | Acciones consultables; filtro de actor efectivo; errores 400; sin secretos | `rtk proxy python scripts/qa_inventory_mysql.py tests/integration/test_reportes_administracion.py` |
| RF050-02 | Acceso bajo carga | Sys | Negativo/Performance | ADMIN ve reportes; CLIENTE es denegado; p95 <500 ms | `rtk proxy python scripts/qa_inventory_mysql.py tests/system/test_rf038_050_k6.py` |

# EVALUACIÓN FINAL DEL MÓDULO AUDITADO

Valoración cualitativa, no certificación ISO ni garantía de ausencia de flakiness:

- Testabilidad del Código Actual: **8/10**. Puertos aislables; algunas vistas construyen factories concretas.
- Cobertura Unitaria Alcanzable: **9/10**. Reglas puras; el porcentaje medido y su alcance aparecen debajo.
- Aislamiento de Dependencias: **8/10**. Dominio sin ORM; infraestructura verificada en MySQL y navegador.
- Preparación para CI/CD: **8/10**. Gates locales y YAML; CI remoto y soporte del perfil productivo pendientes.
- Resiliencia ante Fallos: **8/10**. Errores de entrada, permisos, pérdidas, costos ausentes y sesiones revocadas comprobados; memoria/paginación siguen siendo límites.

# ESTADO DE CALIDAD (QUALITY READINESS)
""")
unit_path = ROOT / "reports/rf044-050-unit-gate.json"
unit = json.loads(unit_path.read_text(encoding="utf-8")) if unit_path.exists() else {}
if unit:
    texto(f"Unit: {unit['unit_tests']} pruebas; cobertura del núcleo explícito: **{unit['percent']}%**, {unit['covered']}/{unit['statements']} líneas; mínimo 80%.")
texto("| Perfil | Unit | Cobertura del núcleo | Integración | Sistema/carga | UAT | Fallos / errores / omitidas | Reportes HTTP p95 |\n|---|---|---|---|---|---|---|---|")
listos = bool(unit.get("passed"))
for nombre in ("qa", "production"):
    path = ROOT / f"reports/rf044-050-{nombre}.xml"
    k6_path = ROOT / f"reports/rf044-050-{nombre}-k6.json"
    unit_perfil = ROOT / f"reports/rf044-050-{nombre}-unit-gate.json"
    if not path.exists() or not k6_path.exists() or not unit_perfil.exists():
        texto(f"| {nombre} | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente |")
        listos = False
        continue
    tree = ET.parse(path).getroot()
    suites = list(tree.iter("testsuite"))
    fallos = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("failures", "errors", "skipped")}
    casos = list(tree.iter("testcase"))
    niveles = {nivel: sum(c.get("classname", "").startswith(f"tests.{nivel}.") for c in casos)
               for nivel in ("integration", "system", "uat")}
    metrics = json.loads(k6_path.read_text(encoding="utf-8"))["metrics"]
    unit_datos = json.loads(unit_perfil.read_text(encoding="utf-8"))
    p95 = metrics["http_req_duration"]["p(95)"]
    bien = unit_datos["passed"] and not any(fallos.values()) and metrics["checks"]["value"] == 1 and metrics["http_req_failed"]["value"] == 0 and p95 < 500
    listos = listos and bien
    texto(f"| {nombre} | {unit_datos['unit_tests']} | {unit_datos['percent']}% | {niveles['integration']} | {niveles['system']} | {niveles['uat']} | {fallos['failures']} / {fallos['errors']} / {fallos['skipped']} | {p95:.2f} ms |")
if listos:
    texto("Unit Test Ready → ✅ Listo. Integration Ready → ✅ Listo con MySQL nativo efímero. System/E2E Ready → ✅ Listo para los flujos y smoke de carga probados. UAT/Business Ready → ⚠ Aprobación formal del PO pendiente; automatización aprobada.")
else:
    texto("⚠ Validación incompleta o gate no aprobado: consultar los artefactos antes de declarar readiness.")
texto("""
No se ejecutó Testcontainers en esta máquina porque falta Docker, ni se publicó un
workflow o modificó la protección de ramas. La aceptación productiva sigue pendiente.
El alcance nativo reutiliza tres archivos de integración (incluyen regresiones de clientes/promociones),
dos de sistema y dos de UAT: sus conteos no representan una nueva ejecución de toda la aplicación.

Reproducción local usando herramientas efímeras ya instaladas en este equipo, desde puntoventa_total:

```powershell
$env:QA_K6_BINARY = 'C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/k6/v2.3.0/k6-v2.3.0-windows-amd64/k6.exe'
rtk proxy .venv/Scripts/python.exe scripts/qa_inventory_mysql_native.py --basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --target tests/integration/test_reportes_administracion.py --target tests/integration/test_rf038_050.py --target tests/integration/test_rf030_050_contratos.py --target tests/system/test_reportes_administracion_playwright.py --target tests/system/test_rf038_050_k6.py --target tests/uat/test_reportes_administracion_bdd.py --target tests/uat/test_reportes_administracion_contratos_bdd.py --report-prefix rf044-050-qa
rtk proxy powershell -NoProfile -Command 'Copy-Item -LiteralPath reports/k6-reportes-summary.json -Destination reports/rf044-050-qa-k6.json'
```

Repetir secuencialmente con `.venv-production/Scripts/python.exe`, prefijo `rf044-050-production`
y destino `reports/rf044-050-production-k6.json`. Capturar k6 antes de otra carga.
Generar este documento: `rtk proxy .venv/Scripts/python.exe scripts/qa_build_rf044_050_report.py`.
Los JUnit before/after conservan la reproducción inicial; los XML por perfil y JSON k6
contienen la evidencia final. No se aplicaron migraciones ni se modificó la BD del negocio.
""")
destino = ROOT / "docs/testing/plan_maestro_rf044_050.md"
destino.write_text("\n\n".join(PARTES) + "\n", encoding="utf-8")
print(f"Plan generado: {destino.relative_to(ROOT)}")
