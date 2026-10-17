"""Genera el plan completo con código real versionado, sin duplicarlo a mano."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET

from qa_rf030_050_evidence import perfil as validar_perfil

ROOT = Path(__file__).resolve().parents[1]
PARTES = []


def texto(contenido):
    contenido = contenido.strip()
    if "\n" not in contenido and contenido.startswith("|") and PARTES and PARTES[-1].rstrip().endswith("|"):
        PARTES[-1] = PARTES[-1].rstrip() + "\n" + contenido + "\n"
    else:
        PARTES.append(contenido + "\n")


def codigo(ruta, lenguaje="python"):
    path = ROOT / ruta
    texto(f"**Archivo: `{ruta}`**\n\n```{lenguaje}\n{path.read_text(encoding='utf-8').rstrip()}\n```\n")


texto("""
# 1. DIAGNÓSTICO ARQUITECTÓNICO Y DE TESTABILIDAD DEL MÓDULO

## 1.1 Lenguaje, Runtime y Framework detectado

Alcance: RF-030..050, módulos 3.4 Pedidos en Línea, 3.5 Clientes Frecuentes/Promociones y 3.6 Reportes/Administración.
Los conteos finales corresponden a la suite completa del proyecto, incluyendo regresiones de POS,
inventario y catálogo. Los escenarios específicos y su relación con RF-030..050 se identifican en la matriz.
Python, Django, monolito modular con dominio/aplicación/infraestructura/presentación. Se revisó el código antes de seleccionar herramientas.
Revisión del 17 de octubre de 2026. Perfil declarado: Python 3.11.16, Django 5.0.6, Celery 5.4.0.
Perfil QA observado: Python 3.14.7, Django 6.1.2, Celery 5.6.3, pytest 9.1.1, pytest-django 4.14.0.
Los perfiles tienen dependencias independientes y fijadas; esta auditoría no actualiza silenciosamente producción.
No se presentan herramientas futuras de 2027 como verificadas hoy.
El perfil declarado es histórico: Django 5.0 terminó soporte el 2 de abril de 2025 y 5.0.6 precede correcciones de seguridad.
No se declara preparado para exposición productiva solo por aprobar tests. La actualización a una rama soportada requiere
una migración de dependencias y su validación; esta auditoría mantiene la comparación reproducible con el perfil recibido.
[Soporte oficial](https://www.djangoproject.com/download/) y [correcciones posteriores a 5.0.6](https://docs.djangoproject.com/en/dev/releases/5.0.7/).

## 1.2 Mapa de Dependencias del Módulo

| Dependencia | Unit: aislar | Integración/Sistema/UAT: comprobar |
|---|---|---|
| Orders y Customers | Agregados, DTO y reglas reales; repositorios/puertos con mocks cuando corresponde | Persistencia, sesión y propietario reales |
| Identity y Catalog | Hasher/repositorios como puertos | Hash, login, roles, usuarios y categorías reales |
| Promotions | Motor y cálculos puros | Vigencia, 2x1, combo, fidelización y persistencia |
| Sales/Inventory | Puertos de inventario y promociones | Pagos, lotes, reservas y transacciones MySQL/InnoDB |
| Reporting | Rangos y distribución monetaria puros | Ventas PAGADA, exclusión de anuladas y costo congelado |
| Auditing | Sin red | Actor, acción, agregado y fecha en la transacción; libro de movimientos del inventario |
| Redis/Celery/SMTP | Sin servicios externos | Worker real y SMTP por socket local; no se finge entrega al proveedor productivo |
| UI/carga | No corresponde | Chromium y k6 contra servidor real |

Identificadores: Pedido.cliente_id = Identity.Usuario.id; Venta.cliente_id = Customers.Cliente.id.
El perfil y el historial validan al dueño por Cliente.usuario_id. No intercambiar esos UUID.
El hasher de pruebas utiliza la configuración de testing (MD5PasswordHasher para velocidad);
la comprobación de credenciales no acredita el algoritmo/costo configurado en producción.

## 1.3 Deuda Técnica o Problemas de Testabilidad

La suite existente protege propiedad del carrito y seguimiento, checkout, cancelación durante preparación,
reservas hasta el recojo, historial propio, descuento de frecuencia, fechas, combos, edición web,
costo histórico, persistencia de descuentos, auditoría y revocación de sesiones.
La consolidación incorpora contratos de estados/fronteras, rankings, último administrador,
entrega por navegador, las pruebas completas del módulo 3.6 y el ciclo de promoción
Borrador → Activa → Vencida → Cancelada solicitado por el usuario.
Las correcciones de 3.6 incluyen margen porcentual por producto, redondeo HALF_UP del total,
acciones CREAR/ACTUALIZAR/ELIMINAR consultables y validación/filtro por actor en auditoría.

| Hallazgo de análisis estático | Riesgo / testabilidad | Tratamiento |
|---|---|---|
| Adaptadores construyen repositorios concretos mediante factories e imports locales | Acoplamiento medio; difícil inducir fallos sin monkeypatch | Mantener puertos en Unit; extraer factories a parámetros si se refactoriza |
| `descuento_producto` captura `Exception` y devuelve cero | Puede ocultar indisponibilidad del cálculo de descuentos | Falta política de negocio de fallo; registrar observabilidad y acordar si debe bloquear el cobro |
| Reportes e historial convierten Decimal a float en su salida | Riesgo de precisión en agregaciones futuras | Cálculos monetarios usan Decimal; conservarlo hasta serializar en una refactorización separada |
| Historial carga todas las compras y utilidad todas las líneas del rango | Memoria/tiempo crecen con los datos | Añadir paginación y probar volúmenes representativos antes de declarar capacidad productiva |
| RF-037 usa SMTP dentro de una transacción y marca luego el envío | Bloqueo prolongado o duplicado tras una caída | Probar recuperación; valorar outbox e idempotencia del proveedor |
| DNI/teléfono son datos personales; sesión controla propiedad y roles | Exposición por IDOR o logs | Pruebas de propietario, CSRF, roles y exclusión de secretos de auditoría |
| Dependencias productivas fijan Django 5.0.6 sin soporte | Riesgo alto de seguridad de dependencias | Migrar a rama soportada en trabajo de actualización; esta suite no certifica seguridad productiva |
| El ciclo suministrado exige Vencida → Cancelada | Brecha reproducida en Unit/HTTP y corregida | Se permite cancelar FINALIZADA; cancelada es terminal y vencida/cancelada no se reactivan; UI y BDD lo verifican |
| RF-047 mostraba utilidad por producto pero no porcentaje; auditoría rechazaba acciones escritas por el middleware y filtros inválidos producían 500 | Corregido y comprobado en los cuatro niveles | Se consolidan las pruebas de `test_reportes_administracion*` y el gate de doce archivos del núcleo |

Políticas conservadas o explicitadas:

- Fidelización existente: recurrente hasta 7 días = 10%; OCASIONAL = 5%; requiere una promoción de fidelización vigente.
  El código clasifica como OCASIONAL también intervalos superiores a 30 días: no se introduce un corte no confirmado.
  No hubo confirmación de otra política. Dos compras del mismo día cuentan como recurrentes; una sola no proporciona frecuencia.
- Combo: productos/cantidades definidos por el administrador y precio final del paquete. Solo paquetes completos.
  Beneficio global = mejor opción entre combo/fidelización, descontando lo aplicado a líneas para evitar acumulación accidental.
- Promoción: Borrador → Activa → Vencida → Cancelada. PROGRAMADA se conserva internamente como borrador con calendario;
  FINALIZADA se muestra Vencida. El fin es exclusivo: en ese instante ya no aplica.
  La cancelación desde FINALIZADA se permite conforme al contrato suministrado; la reactivación queda prohibida.
- Pedidos: CONFIRMADO se muestra Pendiente; BORRADOR solo representa el carrito interno. El cliente solo cancela Pendiente.
- Horarios: franjas futuras de 30 minutos. No se inventaron horario comercial, capacidad por franja ni política de no-show.
- Utilidad comercial: ingresos netos distribuidos por línea y costo de catálogo congelado al agregar el producto.
  No es un cálculo contable PEPS del costo de cada lote. Los costos históricos ausentes se identifican; no se reconstruyen con valores actuales.
- RF-037 se implementa mediante email. SMS no tiene proveedor real configurado. SMTP no puede garantizar exactly-once tras una caída entre envío y commit.

# 2. MATRIZ DE APLICATIVOS Y HERRAMIENTAS REQUERIDAS (STACK 2026-2027)

| Nivel de Prueba | Librería / Framework Principal | Aplicativo / Motor Necesario | Propósito en el Módulo | Comando de Instalación |
|---|---|---|---|---|
| Unit | pytest 8.2.0, pytest-cov 5.0.0, Hypothesis 6.169.4, unittest.mock | Python 3.11 | Reglas y propiedades monetarias | `rtk proxy python -m pip install -r requirements/testing.txt` |
| Integration | pytest-django 4.8.0, testcontainers[mysql] 4.15.0, mysqlclient 2.2.4 | Docker con motor Linux; MySQL 8.4.3 | ORM, rollback, permisos y carreras | requirements/testing.txt; Docker: instalador oficial indicado debajo |
| System/E2E | Playwright 1.64.0 | CLI Playwright + Chromium | Formularios, navegación, sesiones y CSRF reales | `rtk proxy python -m playwright install chromium` |
| Performance | k6 2.3.0 | CLI k6 | Cobro <100 ms p95; reportes/pedidos <500 ms p95 | Windows: `rtk proxy python scripts/qa_download_tools.py k6 --asset k6-v2.3.0-windows-amd64.zip` |
| UAT | pytest-bdd 9.0.0 | CLI pytest | Diecinueve escenarios de negocio entre los tres módulos | requirements/testing.txt |
| Servicios | Celery 5.4.0, redis 5.0.4 | Redis y SMTP | Worker, recuperación de avisos y entrega SMTP | requirements/testing.txt; Redis portable: `rtk proxy python scripts/qa_download_tools.py redis --asset Redis-8.10.2-Windows-x64-cygwin.zip` |

[Instalación oficial de Docker Desktop en Windows](https://docs.docker.com/desktop/setup/install/windows-install/).
Con el instalador descargado, PowerShell: `Start-Process '.\\Docker Desktop Installer.exe' -Wait -ArgumentList 'install'`.
Después iniciar el motor Linux y comprobar `rtk proxy docker version`. Requiere virtualización/WSL según el instalador.
No se requieren dos instalaciones de Docker Desktop ni Postman para ejecutar pytest.
Testcontainers usa TCP 127.0.0.1 y el puerto publicado; localhost en mysqlclient puede forzar un socket equivocado.

Preparación desde puntoventa_total, con Python 3.11 instalado:

```powershell
rtk proxy py -3.11 -m venv .venv-rf030-050
rtk proxy .venv-rf030-050/Scripts/python.exe -m pip install -r requirements/testing.txt
rtk proxy .venv-rf030-050/Scripts/python.exe -m playwright install chromium
rtk proxy .venv-rf030-050/Scripts/python.exe manage.py check --settings=config.settings.testing
rtk proxy .venv-rf030-050/Scripts/python.exe manage.py makemigrations --check --dry-run --settings=config.settings.testing
```

Los comandos abreviados con `python` requieren ese entorno activado. Para evitar depender de la activación,
puede sustituirse `python` por `.venv-rf030-050/Scripts/python.exe` en cada comando.
Los comandos nativos de este equipo ya indican sus intérpretes completos (.venv y .venv-production).
El perfil QA alternativo se instala con requirements/qa-inventory-mysql.txt y Python 3.14.7 en otro entorno.

# 3. ESTRUCTURA DE DIRECTORIOS DE TESTING (SCAFFOLDING)

```text
proyecto_ventas/
|-- .cursor/rules/rf030-050-testing.mdc
|-- .github/workflows/full-quality.yml
`-- puntoventa_total/
    |-- config/settings/{testing,testing_mysql}.py
    |-- requirements/{testing,qa-inventory-mysql}.txt
    |-- src/modules/{orders,customers,promotions,reporting,identity,catalog,auditing,sales}/
    |-- tests/
    |   |-- unit/domain/{test_pedidos_online,test_clientes_promociones_reportes}.py
    |   |-- unit/domain/test_rf030_050_contratos.py
    |   |-- unit/application/test_reportes_administracion.py
    |   |-- integration/{test_pedidos_online,test_pedidos_online_mysql,test_rf038_050}.py
    |   |-- integration/{test_smtp_real,test_redis_celery_real}.py
    |   |-- integration/test_rf030_050_contratos.py
    |   |-- integration/test_reportes_administracion.py
    |   |-- system/{test_pedidos_online_playwright,test_rf038_050_playwright}.py
    |   |-- system/test_rf030_050_contratos.py
    |   |-- system/test_reportes_administracion_playwright.py
    |   |-- system/{test_k6_pos_real,test_pedidos_online_k6,test_rf038_050_k6}.py
    |   |-- performance/{k6_cobro,k6_pedidos,k6_reportes}.js
    |   `-- uat/
    |       |-- features/{pedidos_online,clientes_promociones_admin}.feature
    |       `-- {test_pedidos_online_bdd,test_clientes_promociones_admin_bdd}.py
    |-- tests/uat/features/reportes_administracion_contratos.feature
    |-- tests/uat/test_reportes_administracion_contratos_bdd.py
    |-- tests/uat/features/reportes_administracion.feature
    |-- tests/uat/test_reportes_administracion_bdd.py
    |-- scripts/{qa_inventory_mysql,qa_inventory_mysql_native,qa_redis_native}.py
    |-- scripts/qa_build_rf030_050_report.py
    |-- docs/testing/plan_maestro_rf030_050.md
    `-- reports/  (JUnit, cobertura, traces, k6; ignorado por Git)
```

# 4. NIVEL 1: PRUEBAS UNITARIAS (UNIT TESTING)

## 4.1 Qué se evalúa en este módulo

Estados, cantidades, hora de recojo, frecuencia, combos completos/incompletos, vencimiento exacto,
reconfirmación sin nueva reserva y propiedad de conservación de centavos al distribuir descuentos.
También margen positivo/negativo/desconocido, redondeo 3.125 → 3.13, total ponderado,
acciones de auditoría, trazas y usuarios desactivados en todos los roles.

## 4.2 Aplicativos y Librerías a usar

pytest, unittest.mock e Hypothesis. Las propiedades monetarias no usan BD, navegador ni red.

## 4.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
rtk proxy .venv-rf030-050/Scripts/python.exe -m pytest tests/unit -q -p no:cacheprovider --cov=src --cov-fail-under=0 --cov-report=json:reports/audit_unit_coverage.json --junitxml=reports/rf030-050-unit.xml
rtk proxy .venv-rf030-050/Scripts/python.exe scripts/qa_unit_gate.py
rtk proxy .venv-rf030-050/Scripts/python.exe scripts/qa_reportes_unit_gate.py --junit reports/rf030-050-unit.xml
```

El gate mide dominio y aplicación a partir de pruebas unitarias, mínimo 80%; no confunde cobertura integrada con unitaria.
Ese primer indicador comprende los archivos instrumentados incluidos en el JSON de coverage.py.
El gate del núcleo de reportes/auditoría analiza doce archivos explícitos e incluye los no importados.
Su alcance y denominador están en `scripts/qa_reportes_unit_gate.py`; no representa todas las vistas de esos módulos.

## 4.4 Código Completo del Test Unitario
""")
for ruta in ("tests/unit/domain/test_pedidos_online.py", "tests/unit/application/test_confirmar_pedido.py", "tests/unit/domain/test_clientes_promociones_reportes.py", "tests/unit/application/test_beneficios_venta.py", "tests/unit/domain/test_rf030_050_contratos.py", "tests/unit/application/test_reportes_administracion.py", "scripts/qa_reportes_unit_gate.py"):
    codigo(ruta)

texto("""
# 5. NIVEL 2: PRUEBAS DE INTEGRACIÓN (INTEGRATION TESTING)

## 5.1 Qué se evalúa en este módulo

Registro/login, stock, persistencia, pagos, historial, fidelización automática, promociones, rangos,
utilidad estable, edición, permisos, revocación de sesión y rollback si la auditoría falla.
Dos escritores compiten por confirmar/cancelar el mismo pedido. La suite completa también enfrenta inventario y secuencias.

## 5.2 Aplicativos y Librerías a usar

MySQL 8.4.3/InnoDB efímero en Testcontainers; Redis para worker real; SMTP de prueba por socket.
Los tests con locmem demuestran selección de destinatario y flujo, no envío a un proveedor externo.
SQLite solo sirve para iteración: no demuestra SELECT FOR UPDATE ni carreras de InnoDB.
El wrapper usa la API real de [MySqlContainer](https://testcontainers-python.readthedocs.io/en/latest/modules/mysql/README.html).
No se añaden httpx ni pytest-asyncio: las vistas de este proyecto son síncronas y se prueban con Django Client.

## 5.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
rtk proxy docker version
rtk proxy docker run --detach --rm --name rf030-050-redis --publish 127.0.0.1:16379:6379 redis:7-alpine
$env:QA_REDIS_URL = 'redis://127.0.0.1:16379/15'
rtk proxy .venv-rf030-050/Scripts/python.exe scripts/qa_inventory_mysql.py tests/integration --junitxml=reports/rf-integration.xml
```

Mantener esa instancia exclusiva durante los niveles 2 y 3 y detenerla al terminar:
`rtk proxy docker stop rf030-050-redis`. CI ya proporciona Redis como servicio.
Si ese puerto/nombre ya está ocupado, escoger otro puerto/nombre de QA y actualizar la variable;
no detener servicios ajenos.
Alternativa nativa **aislada**, disponible en este equipo sin Docker; no conecta a la BD del negocio:

```powershell
rtk proxy .venv/Scripts/python.exe scripts/qa_inventory_mysql_native.py --basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --target tests/integration/test_rf038_050.py --target tests/integration/test_pedidos_online.py --target tests/integration/test_pedidos_online_mysql.py --report-prefix rf-integration
```

## 5.4 Código Completo del Test de Integración
""")
for ruta in ("scripts/qa_inventory_mysql.py", "tests/integration/test_pedidos_online.py", "tests/integration/test_pedidos_online_mysql.py", "tests/integration/test_rf038_050.py", "tests/integration/test_rf030_050_contratos.py", "tests/integration/test_reportes_administracion.py", "tests/integration/test_smtp_real.py", "tests/integration/test_redis_celery_real.py"):
    codigo(ruta)

texto("""
# 6. NIVEL 3: PRUEBAS DE SISTEMA (SYSTEM / E2E & PERFORMANCE)

## 6.1 Qué se evalúa en este módulo

Registro → login → carrito → recojo → confirmación/cancelación con Chromium y CSRF.
Administración: categoría, promoción de porcentaje, combo mediante selectores, reportes e historial propio.
También se comprueba Pendiente → En preparación → Listo → Entregado desde botones reales,
con reserva conservada durante preparación y stock consumido solo al entregar.
k6 verifica dos sesiones de clientes y dos roles, además de seis cobros reales y coherencia del stock.
Son smoke tests de concurrencia, no certificación de capacidad máxima de producción.

## 6.2 Aplicativos y Librerías a usar

Playwright/Chromium, k6 2.3.0, MySQL. Linux ejecuta carga contra Gunicorn del proyecto; Windows contra servidor HTTP de QA.
Se bloquean CDN externos en el navegador; se esperan elementos/navegación, sin sleeps para sincronizar UI.

## 6.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
rtk proxy .venv-rf030-050/Scripts/python.exe -m playwright install chromium
rtk proxy .venv-rf030-050/Scripts/python.exe scripts/qa_download_tools.py k6 --asset k6-v2.3.0-windows-amd64.zip
$env:QA_REQUIRE_BROWSER = '1'
$env:QA_K6_BINARY = 'C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/k6/v2.3.0/k6-v2.3.0-windows-amd64/k6.exe'
rtk proxy .venv-rf030-050/Scripts/python.exe scripts/qa_inventory_mysql.py tests/system --junitxml=reports/rf-system.xml
```

Usar la ruta que devuelve el descargador en otra máquina. No ejecutar dos cargas al mismo tiempo.
Presupuestos conservados: cobro p95 <100 ms, búsqueda <200 ms, HTTP/reportes/pedidos <500 ms; checks=100%, error inesperado=0.
Los [thresholds de k6](https://grafana.com/docs/k6/latest/using-k6/thresholds/) determinan el exit code;
un check aislado no bloquea CI por sí solo. Los scripts incluyen ambos.
Los [traces de Playwright](https://playwright.dev/python/docs/trace-viewer-intro) facilitan reproducir fallos:
`rtk proxy python -m playwright show-trace reports/browser/ARCHIVO.zip` abre el trace seleccionado.
Los traces contienen datos/cookies de cuentas efímeras de QA: tratarlos como artifacts privados y de retención corta.

## 6.4 Código Completo del Test de Sistema (E2E) + Script rápido de Carga/Performance
""")
for ruta in ("tests/system/test_pedidos_online_playwright.py", "tests/system/test_rf038_050_playwright.py", "tests/system/test_rf030_050_contratos.py", "tests/system/test_reportes_administracion_playwright.py", "tests/system/test_rf038_050_k6.py"):
    codigo(ruta)
for ruta in ("tests/performance/k6_cobro.js", "tests/performance/k6_pedidos.js", "tests/performance/k6_reportes.js"):
    codigo(ruta, "javascript")

texto("""
# 7. NIVEL 4: PRUEBAS DE ACEPTACIÓN (UAT / BDD)

## 7.1 Escenarios de Negocio en Formato Gherkin

Diecinueve escenarios específicos de estos módulos: cuatro de pedidos y quince comerciales/administrativos,
incluidos cancelación de promoción vencida, utilidad/margen, consulta de auditoría y revocación de sesión.
""")
for ruta in ("tests/uat/features/pedidos_online.feature", "tests/uat/features/clientes_promociones_admin.feature", "tests/uat/features/reportes_administracion_contratos.feature", "tests/uat/features/reportes_administracion.feature"):
    codigo(ruta, "gherkin")
texto("## 7.2 Automatización del UAT (Step Definitions) o Checklist de Validación Manual para el Product Owner / Cliente")
for ruta in ("tests/uat/test_pedidos_online_bdd.py", "tests/uat/test_clientes_promociones_admin_bdd.py", "tests/uat/test_reportes_administracion_contratos_bdd.py", "tests/uat/test_reportes_administracion_bdd.py"):
    codigo(ruta)
texto("""
## 7.3 Guía Paso a Paso para ejecutar y aprobar el UAT

```powershell
rtk proxy .venv-rf030-050/Scripts/python.exe -m pytest tests/uat -q -p no:cacheprovider --junitxml=reports/rf-uat.xml
```

El Product Owner valida reglas/supuestos, nombres de estados, totales y permisos con cuentas de QA y registra versión,
fecha, resultado y aprobación. Su firma no se sustituye con un pytest verde. No se envían mensajes a clientes reales.
Para aceptación con el mismo motor de producción:
`rtk proxy python scripts/qa_inventory_mysql.py tests/uat --junitxml=reports/rf-uat-mysql.xml`.
Checklist de aprobación: comprobar los diecinueve escenarios, validar los porcentajes/umbrales de frecuencia,
confirmar política de horarios y permisos de GERENTE, validar la transición Vencida → Cancelada implementada,
verificar el email de Listo en un buzón de staging,
y registrar nombre del aprobador, commit, fecha, incidencias y decisión. Esa aprobación queda pendiente del PO.

# 8. GUÍA DE AI SKILLS, MCP Y AUTOMATIZACIÓN AGÉNTICA (CONTEXTO 2026-2027)

## 8.1 Configuración de Skill / Rule para el Agente de Código

Regla lista para Cursor, aplicada al trabajar sobre los archivos coincidentes; no implica que el IDE ejecute tests sin una tarea del usuario.
""")
codigo("../.cursor/rules/rf030-050-testing.mdc", "markdown")
texto("""
## 8.2 Servidores MCP (Model Context Protocol) recomendados

| Herramienta / Skill | Aplicación concreta | Configuración y límite |
|---|---|---|
| [Playwright MCP de Microsoft](https://github.com/microsoft/playwright-mcp) | Inspeccionar accesibilidad de checkout, gestión y estados | Node.js >=18; navegador contra entorno efímero; pytest conserva el oráculo |
| [GitHub MCP oficial](https://github.com/github/github-mcp-server) | Inspeccionar fallos de checks y artifacts | Acceso de lectura al repositorio y artifacts privados; no es dependencia de pytest |
| MySQL mediante ORM/CLI | Consultas de estado, reservas y auditoría | Preferido a instalar un MCP PostgreSQL/SQLite ajeno al motor usado |
| Postman `api-engineer`, `api-testing`, `ci-integration` | Reutilizar contratos HTTP y seleccionar assertions/gates | En esta revisión se usaron sus instrucciones; no se publicó workspace ni se afirmó un run de Postman |
| Testcontainers local; Cloud opcional | Infraestructura efímera de CI | El camino local no requiere cuenta Cloud; no se presupone licencia o conexión externa |

Configuración opcional para un cliente MCP compatible, usando el arranque documentado por Microsoft:

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest", "--headless", "--isolated"]
    }
  }
}
```

El alias `latest` sirve para el arranque exploratorio documentado; fijar la versión validada antes de usarlo en CI.
Una regla de Cursor se activa por contexto de archivos; no equivale a un hook automático de ejecución.
No se instalaron conexiones externas. Mantener credenciales fuera del prompt y limitar permisos del servidor;
las anotaciones de herramientas no son controles de acceso.
[Guía oficial de seguridad MCP](https://modelcontextprotocol.io/specification/draft/basic/security_best_practices).

## 8.3 Flujo de Auto-Healing (Autoreparación de Tests)

1. Adjuntar al agente el traceback, trace de navegador y resumen k6 del fallo.
2. Leer reglas y RF; reproducir el nodo exacto con pytest.
3. Reparar la causa y verificar Unit → MySQL → Sistema/Carga → UAT, sin modificar el oráculo para ocultar regresiones.
4. Si cambió el negocio, actualizar primero su criterio de aceptación y obtener revisión del cambio.
5. Conservar evidencias antes/después y explicar límites del resultado.

Con Claude Code ya instalado y autenticado, desde la raíz Git, comando explícito de revisión agéntica:

```powershell
rtk proxy claude -p "Lee .cursor/rules/rf030-050-testing.mdc y puntoventa_total/docs/testing/plan_maestro_rf030_050.md. Reproduce el fallo indicado, corrige la causa y ejecuta los cuatro niveles. No reduzcas umbrales, no elimines escenarios ni publiques cambios. Reporta evidencias y limitaciones."
```

Es un comando para un entorno con ese CLI; no se ejecutó ni se presupone una cuenta/licencia disponible.
[Sintaxis oficial de Claude Code](https://code.claude.com/docs/en/cli-reference).

# 9. PIPELINE CI/CD (QUALITY GATES)

El workflow de la **raíz Git** descubre estos tests nuevos sin listas manuales. Cada perfil ejecuta los pasos en orden:
Unit → gates unitarios general y de núcleo → MySQL → Sistema/Carga → UAT → cobertura global. Chromium/k6/Redis forman parte del job.
La ejecución completa rechaza skips/xfails y cobertura inferior a 80%; los presupuestos k6 también bloquean.
Un YAML verde no bloquea por sí mismo el merge: se requieren checks obligatorios en la protección de main,
con nombres `quality (production-declared)` y `quality (qa)`.
La protección remota no se verificó ni modificó en esta revisión. Esta ampliación se entrega localmente,
sin afirmar un nuevo check remoto ejecutado. Configurar ambos como required status checks
en la [protección de la rama](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
Cada nivel rechaza omisiones/xfails; UAT también usa MySQL efímero. Artifacts se conservan siete días.
[Semántica oficial del workflow](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).
""")
codigo("../.github/workflows/full-quality.yml", "yaml")
texto("""
# 10. MATRIZ DE TRAZABILIDAD DE PRUEBAS DEL MÓDULO

U = `rtk proxy python -m pytest tests/unit -q`.
I = `rtk proxy python scripts/qa_inventory_mysql.py tests/integration`.
S = `rtk proxy python scripts/qa_inventory_mysql.py tests/system` (Chromium/k6 disponibles).
A = `rtk proxy python -m pytest tests/uat -q`.
La primera tabla relaciona requisitos con componentes; la segunda proporciona nodos pytest exactos.

| ID Caso | Funcionalidad / Método del Módulo | Nivel (Unit / Int / Sys / UAT) | Tipo (Positivo / Negativo / Borde) | Resultado Esperado | Comando de Ejecución |
|---|---|---|---|---|---|
| RF-030 | registro_web_view | Int/Sys | Positivo/Negativo | Cuenta CLIENTE; DNI/email únicos; hash; datos obligatorios | I / S |
| RF-031 | login_view / AutenticarUsuario | Int/Sys | Positivo/Negativo | Email y contraseña; fallo no autentica | I / S |
| RF-032 | AgregarProductoPedido | Unit/Int/Sys | Positivo/Borde | Cantidad positiva acumulada dentro del stock | U / I / S |
| RF-033 | checkout_view / ConfirmarPedido | Unit/Int/Sys/UAT | Positivo/Negativo | Recojo, reservas y confirmación atómicos | U / I / S / A |
| RF-034 | asignar_hora_recojo / PedidoForm | Unit/Int/Sys | Positivo/Borde | Hora futura, minutos 00/30, sin segundos | U / I / S |
| RF-035 | detalle/mis_pedidos/seguimiento | Int/Sys | Positivo/Negativo | Estados reales; pedido ajeno no se revela | I / S |
| RF-036 | CancelarPedido | Unit/Int/Sys/UAT | Positivo/Negativo/Borde | Solo Pendiente; reserva liberada una vez | U / I / S / A |
| RF-037 | cambiar_estado_view / tarea run | Int/UAT | Positivo/Negativo | Email al pasar a Listo; SMTP real y pendientes recuperables | I / A |
| RF-038 | registro_cliente_view | Int/UAT | Positivo | Cajero registra DNI/teléfono sin adjudicarse la cuenta | I / A |
| RF-039 | HistorialComprasAdapter / FrecuenciaCompra | Unit/Int/UAT | Positivo/Borde | Importe y frecuencia solo de ventas pagadas | U / I / A |
| RF-040 | PrepararBeneficiosVenta | Unit/Int/Sys/UAT | Positivo/Negativo | Fidelización automática antes del primer pago, persistida | U / I / S / A |
| RF-041 | CrearPromocion / descuento_combo | Unit/Int/Sys/UAT | Positivo/Negativo | Porcentaje, 2x1 y combo completos con precio definido | U / I / S / A |
| RF-042 | programar / actualizar_estado_promociones / cancelar | Unit/Int/Sys/UAT | Positivo/Borde | Rango válido; vencida no se publica; admite Cancelada sin reactivarse | U / I / S / A |
| RF-043 | historial_compras_view | Int/Sys/UAT | Positivo/Negativo | Cliente consulta el propio, no el ajeno | I / S / A |
| RF-044 | ReporteVentasDiarias / ventas_reporte_view | Int/Sys/UAT | Positivo | Total, tickets y métodos de pago | I / S / A |
| RF-045 | RangoReporteForm / ReporteVentasPorFecha | Int/Sys | Positivo/Negativo | Filtra fechas; inválido da 400 y no 500 | I / S |
| RF-046 | productos_reporte_view | Int/Sys | Positivo | Ranking por cantidad o monto neto | I / S |
| RF-047 | agrupar_utilidad / ReporteUtilidad | Unit/Int/Sys/UAT | Positivo/Borde | Costo congelado, descuento repartido, margen por producto/total y HALF_UP | U / I / S / A |
| RF-048 | crear/editar/desactivar_usuario | Unit/Int/Sys/UAT | Positivo/Negativo | Roles, edición, baja y revocación de sesión | U / I / S / A |
| RF-049 | categoria_view | Int/Sys/UAT | Positivo/Negativo | Creación y edición con permisos | I / S / A |
| RF-050 | RequestAuditMiddleware / auditoría de venta | Int/Sys/UAT | Positivo/Negativo | Actor, agregado y fecha; fallo de auditoría revierte | I / S / A |

Casos añadidos en esta revisión, con selección exacta ejecutable desde `puntoventa_total`:

| ID Caso | Funcionalidad / Método del Módulo | Nivel | Tipo | Resultado Esperado | Comando de Ejecución |
|---|---|---|---|---|---|
| QA-U01 | Pedido.transicionar_a, 36 combinaciones | Unit | Positivo/Negativo | Solo seis transiciones válidas; rechazo conserva estado | `rtk proxy python -m pytest tests/unit/domain/test_rf030_050_contratos.py::test_matriz_completa_de_transiciones_del_pedido -q` |
| QA-U02 | Promocion.esta_vigente, cinco estados y cuatro instantes | Unit | Borde | Inicio inclusivo; fin exclusivo; solo ACTIVA | `rtk proxy python -m pytest tests/unit/domain/test_rf030_050_contratos.py::test_vigencia_inicio_inclusivo_fin_exclusivo -q` |
| QA-U03 | Promocion.activar | Unit | Negativo | FINALIZADA/CANCELADA no reactivan | `rtk proxy python -m pytest tests/unit/domain/test_rf030_050_contratos.py::test_promocion_terminal_no_se_reactiva -q` |
| QA-I01 | Rango diario en America/Lima | Int | Borde | Dos tickets y 50 soles; días adyacentes/anuladas excluidos | `rtk proxy python scripts/qa_inventory_mysql.py tests/integration/test_rf030_050_contratos.py::test_reporte_incluye_dia_local_completo_y_excluye_dias_adyacentes` |
| QA-I02 | Ranking por cantidad/monto | Int | Positivo | Cambia orden; seis unidades y 40 soles | `rtk proxy python scripts/qa_inventory_mysql.py tests/integration/test_rf030_050_contratos.py::test_ranking_cambia_segun_criterio_sin_incluir_anuladas` |
| QA-I03 | Desactivar/degradar último administrador | Int | Negativo | Cuenta activa y rol ADMINISTRADOR conservados | `rtk proxy python scripts/qa_inventory_mysql.py tests/integration/test_rf030_050_contratos.py::test_ultimo_administrador_conserva_acceso` |
| QA-S01 | Atención desde navegador hasta Entregado | Sys | Positivo | Reserva 2 hasta Listo; entrega deja stock 8 y reserva 0 | `rtk proxy python scripts/qa_inventory_mysql.py tests/system/test_rf030_050_contratos.py` |
| QA-A01..03 | Ranking, fechas invertidas y último administrador | UAT | Positivo/Negativo | Criterios Gherkin verificados por HTTP | `rtk proxy python scripts/qa_inventory_mysql.py tests/uat/test_reportes_administracion_contratos_bdd.py` |
| QA-U04 | Ciclo completo de promoción | Unit | Positivo/Negativo | Borrador → Activa → Vencida → Cancelada; cancelada terminal | `rtk proxy python -m pytest tests/unit/domain/test_rf030_050_contratos.py::test_ciclo_promocion_borrador_activa_vencida_cancelada -q` |
| QA-I04 | Cancelar vencida y auditar | Int | Positivo/Negativo | Persiste CANCELADA; no reactiva ni concede descuentos | `rtk proxy python scripts/qa_inventory_mysql.py tests/integration/test_rf038_050.py::test_rf042_admin_cancela_vencida_sin_reactivarla_y_audita` |
| QA-S02 | Cancelación de vencida por UI | Sys | Positivo | Etiqueta Cancelada; sin botones de activar/cancelar | `rtk proxy python scripts/qa_inventory_mysql.py tests/system/test_rf038_050_playwright.py::test_admin_cancela_promocion_vencida_desde_navegador` |
| QA-A04 | Ciclo Vencida → Cancelada | UAT | Positivo | Escenario de cancelación vencida aprobado | `rtk proxy python scripts/qa_inventory_mysql.py tests/uat/test_clientes_promociones_admin_bdd.py` |
| QA-R01..49 | Márgenes, auditoría, usuarios y categorías | Unit/Int/Sys/UAT | Positivo/Negativo/Borde | Contratos de 3.6 cubiertos por la suite consolidada | `rtk proxy python scripts/qa_inventory_mysql.py tests/integration/test_reportes_administracion.py tests/system/test_reportes_administracion_playwright.py tests/uat/test_reportes_administracion_bdd.py` |

# EVALUACIÓN FINAL DEL MÓDULO AUDITADO

Escala cualitativa, no porcentaje medido ni certificación ISO:

- Testabilidad del Código Actual: **8/10**. Dominio aislable; algunos adaptadores construyen repositorios concretos.
- Cobertura Unitaria Alcanzable: **9/10**. Propiedades y reglas puras automatizadas; cobertura real se informa debajo.
- Aislamiento de Dependencias: **8/10**. Puertos en unitarias; BD/worker/SMTP reales para evidencia integrada.
- Preparación para CI/CD: **8/10**. Dos perfiles, cuatro niveles, artifacts y gates; antecedente de latencia POS y CI remoto pendiente. El resultado actual se detalla debajo.
- Resiliencia ante Fallos (Edge Cases): **8/10**. Rollback, carreras, permisos y avisos fallidos; límites SMTP e históricos explicitados. No equivale a cumplir presupuestos de latencia.

# ESTADO DE CALIDAD (QUALITY READINESS)

Los estados definitivos dependen de las evidencias finales de esta ejecución, que aparecen a continuación.
La aceptación formal del negocio y la configuración del SMTP productivo no se sustituyen por tests locales.
No se promete ausencia absoluta de flakiness ni 100% de cobertura de código.
""")
resultados = []
for perfil in ("production", "qa"):
    prefix = f"rf030-050-{perfil}"
    try:
        suites = list(ET.parse(ROOT / f"reports/{prefix}.xml").getroot().iter("testsuite"))
        datos = {k: sum(int(s.get(k, 0)) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
        datos["coverage"] = round(json.loads((ROOT / f"reports/{prefix}-coverage.json").read_text())["totals"]["percent_covered"], 2)
        resultados.append((perfil, datos))
    except (FileNotFoundError, ET.ParseError, KeyError):
        pass
try:
    validada = {nombre: validar_perfil(nombre) for nombre in ("production", "qa")}
except (FileNotFoundError, ValueError, KeyError):
    validada = {}
if len(resultados) == 2 and all(d["tests"] and validada.get(p, {}).get("tests") == d["tests"]
                              and validada[p].get("coverage") == d["coverage"] for p, d in resultados):
    texto("| Perfil | Pruebas | Fallos / errores / omitidas | Cobertura global |\n|---|---|---|---|")
    for perfil, datos in resultados:
        pasadas = datos['tests'] - datos['failures'] - datos['errors'] - datos['skipped']
        texto(f"| {perfil} | {pasadas}/{datos['tests']} | {datos['failures']} / {datos['errors']} / {datos['skipped']} | {datos['coverage']}% |")
    texto("| Perfil | Unit | Integration | System/E2E/Functional/Performance | UAT |\n|---|---|---|---|---|")
    for perfil, _ in resultados:
        niveles = validada[perfil]["niveles"]
        texto(f"| {perfil} | {niveles['unit']} | {niveles['integration']} | {niveles['system']} | {niveles['uat']} |")
    texto("| Perfil | Unit: dominio/aplicación instrumentados | Unit: núcleo explícito de reportes/auditoría |\n|---|---|---|")
    for perfil, _ in resultados:
        unidad = validada[perfil]["unit"]
        texto(f"| {perfil} | {unidad['instrumented_domain_application_pct']}% | {unidad['reporting_core_pct']}% ({unidad['reporting_core_statements']} líneas) |")
    texto("| Perfil | Cobro p95 (100 ms) | Pedidos HTTP p95 (500 ms) | Reportes HTTP p95 (500 ms) |\n|---|---|---|---|")
    for perfil, _ in resultados:
        cargas = validada[perfil]["k6"]
        texto(f"| {perfil} | {cargas['pos'].get('cobro_p95_ms', 'ver JUnit')} | {cargas['pedidos'].get('http_p95_ms', 'sin evidencia')} | {cargas['reportes'].get('http_p95_ms', 'sin evidencia')} |")
    for perfil, _ in resultados:
        evidencia = validada[perfil]
        texto(f"**{perfil}:** ejecutado {evidencia['provenance']['executed_at']}; Python {evidencia['provenance']['python']}; MySQL {evidencia['provenance']['database']['version']} nativo efímero.")
        if not evidencia["ready"]:
            texto("Gate no aprobado: " + "; ".join(evidencia["problems"]) + ".")
            for caso in evidencia["failed_cases"]:
                texto(f"- Fallo: `{caso}`.")
    if all(validada[p]["ready"] for p, _ in resultados):
        texto("Unit Test Ready → ✅ Listo. Integration Ready → ✅ Listo (MySQL nativo efímero). System/E2E Ready → ✅ Listo para los flujos y smoke de carga probados. UAT/Business Ready → ⚠ Aprobación formal del PO pendiente; el ciclo solicitado está implementado y automatizado.")
    else:
        texto("Unit Test Ready → ✅ Listo. Integration Ready → ✅ Listo (MySQL nativo efímero). System/E2E Ready → ⚠ Requiere resolver el presupuesto de rendimiento; consultar los nodos fallidos antes de concluir sobre otros flujos. UAT/Business Ready → ⚠ Aprobación formal del PO pendiente; el ciclo solicitado está implementado y automatizado. El gate global permanece bloqueado.")
else:
    texto("**Validación final en curso:** no declarar los cuatro niveles listos mientras falten perfiles o existan fallos.")
unit_path = ROOT / "reports/audit_unit_coverage.json"
if unit_path.exists():
    unit = json.loads(unit_path.read_text(encoding="utf-8"))
    resumos = [entrada["summary"] for ruta, entrada in unit["files"].items()
               if {"domain", "application"} & set(ruta.replace("\\", "/").split("/"))]
    total = sum(resumen["num_statements"] for resumen in resumos)
    cubiertas = sum(resumen["covered_lines"] for resumen in resumos)
    if total:
        texto(f"Último indicador unitario de dominio/aplicación instrumentados: **{100 * cubiertas / total:.2f}%** ({cubiertas}/{total} líneas); umbral 80%. Fuente: `reports/audit_unit_coverage.json`. Las capturas por perfil anteriores conservan sus propias mediciones.")
texto("""
Reproducir suite completa local con infraestructura aislada instalada en este equipo:

```powershell
rtk proxy .venv-production/Scripts/python.exe -m pytest tests/unit -q -p no:cacheprovider --cov=src --cov-fail-under=0 --cov-report=json:reports/audit_unit_coverage.json --junitxml=reports/rf030-050-unit.xml
rtk proxy .venv-production/Scripts/python.exe scripts/qa_unit_gate.py
rtk proxy .venv-production/Scripts/python.exe scripts/qa_reportes_unit_gate.py --junit reports/rf030-050-unit.xml
rtk proxy .venv-production/Scripts/python.exe scripts/qa_redis_native.py --binary C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/redis/8.10.2/Redis-8.10.2-Windows-x64-cygwin/redis-server.exe --mysql-basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --k6-binary C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/k6/v2.3.0/k6-v2.3.0-windows-amd64/k6.exe --coverage --report-prefix rf030-050-production
rtk proxy .venv-production/Scripts/python.exe scripts/qa_rf030_050_evidence.py --capture production
rtk proxy .venv/Scripts/python.exe -m pytest tests/unit -q -p no:cacheprovider --cov=src --cov-fail-under=0 --cov-report=json:reports/audit_unit_coverage.json --junitxml=reports/rf030-050-unit.xml
rtk proxy .venv/Scripts/python.exe scripts/qa_unit_gate.py
rtk proxy .venv/Scripts/python.exe scripts/qa_reportes_unit_gate.py --junit reports/rf030-050-unit.xml
rtk proxy .venv/Scripts/python.exe scripts/qa_redis_native.py --binary C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/redis/8.10.2/Redis-8.10.2-Windows-x64-cygwin/redis-server.exe --mysql-basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --k6-binary C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/k6/v2.3.0/k6-v2.3.0-windows-amd64/k6.exe --coverage --report-prefix rf030-050-qa
rtk proxy .venv/Scripts/python.exe scripts/qa_rf030_050_evidence.py --capture qa
rtk proxy .venv/Scripts/python.exe scripts/qa_rf030_050_evidence.py
rtk proxy .venv/Scripts/python.exe scripts/qa_build_rf030_050_report.py
```

Ejecutar los perfiles secuencialmente. El wrapper exige cero skips/xfails en la suite completa.
Capturar cada perfil inmediatamente después de su ejecución, antes de sobrescribir resúmenes k6 con otro run.
El verificador guarda timestamps, versiones y SHA256 de código, pruebas, configuración, requisitos,
templates y estáticos; vincula JUnit/cobertura unitaria por perfil con la suite completa.
Devuelve 1 si hay fallos y aun así conserva la evidencia.
Un resumen de carga sobrescrito por una ejecución posterior se marca no disponible; se consulta el fallo original en JUnit.
No reutilizar conteos históricos para declarar una ejecución nueva aprobada.
Evidencias: reports/rf030-050-*.xml, *-coverage.json, *-provenance.json, resúmenes k6 y browser/*.zip.
Son servicios nativos efímeros; no se etiquetan como Testcontainers ejecutado en esta máquina.
El workflow utiliza contenedores y está listo para validar el mismo código cuando se publique una PR.

Antecedentes de latencia de la ejecución anterior (no sustituyen los resultados actuales de las tablas):

- La suite QA completa registró cobro p95 = 228,64 ms con cobertura instrumentada;
  el límite existente es 100 ms y el gate falló. Sus 36 checks funcionales de k6 aprobaron.
- Una ejecución aislada sin cobertura volvió a incumplir: cobro p95 = 137,49 ms y
  HTTP p95 = 798,10 ms (límite 500 ms). Por tanto, no se atribuye todo el fallo a coverage.
- Evidencia de esta segunda medición: `reports/master-20261017-pos-uninstrumented.xml`.
  Es una muestra corta en Windows, con dos VUs y seis cobros, no un benchmark de capacidad productiva.
- No se modificaron límites ni se repitió hasta obtener verde. Queda pendiente perfilar
  el cobro y repetir en un runner de recursos controlados. El gate conserva el fallo.

Activación en el entorno del negocio: revisar las nuevas migraciones sales/0003..0004 y promotions/0002, además de
las migraciones de Pedidos si aún no se aplicaron; ejecutar `rtk proxy python manage.py migrate` en ese entorno,
configurar SMTP con .env.example y reiniciar web/worker/Beat. No se migró ni modificó la base del negocio en esta auditoría.
""")
destino = ROOT / "docs/testing/plan_maestro_rf030_050.md"
destino.write_text("\n".join(PARTES), encoding="utf-8")
print(f"Plan completo generado: {destino.relative_to(ROOT)} ({destino.stat().st_size} bytes)")
