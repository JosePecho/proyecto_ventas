# 1. DIAGNÓSTICO ARQUITECTÓNICO Y DE TESTABILIDAD DEL MÓDULO

## 1.1 Lenguaje, Runtime y Framework detectado

Python/Django, monolito modular con dominio, aplicación, infraestructura y presentación HTML.
El perfil declarado utiliza Python 3.11 y Django 5.0.6; QA utiliza Python 3.14.7 y Django 6.1.2.
Las versiones efectivas están fijadas en `requirements/testing.txt` y `requirements/qa-inventory-mysql.txt`.
No se presupone disponibilidad de herramientas futuras de 2027.

## 1.2 Mapa de Dependencias del Módulo

| Dependencia | Nivel 1 | Niveles 2/3/4 |
|---|---|---|
| Identity: cuentas, password hash y sesión | Dobles del repositorio/hasher cuando corresponda | Cuenta real y login por email; se conserva username para personal |
| Customers: DNI, contacto, usuario asociado | Validaciones puras | Persistencia real y registro transaccional cuenta/cliente |
| Catalog | Producto de dominio | Productos ORM y catálogo HTML |
| Inventory | Puerto simulado | InnoDB, reservas permanentes para pedidos, liberación y salida por lote |
| Orders | Agregado y reglas puras | Cabecera bloqueada antes de reservar/cancelar/entregar |
| Celery/Redis | Sin worker | Redis y worker reales en la suite completa |
| Email | Sin red en unitarias | SMTP por socket local; backend locmem para escenarios funcionales deterministas |
| Navegador | No aplica | Chromium real, formularios con CSRF y trazas |

El `cliente_id` de Pedido contiene el UUID de **Usuario de identidad**, el mismo de `session.usuario_id`.
No contiene el UUID del registro de Customers. Esta convención coincide con «Mis pedidos».

## 1.3 Deuda Técnica o Problemas de Testabilidad

Se corrigieron: carrito sin propietario, consulta pública de datos ajenos, búsqueda del carrito por número usando un UUID,
checkout que ignoraba datos, ausencia de hora/modalidad, cantidades negativas/acumuladas, cancelación durante preparación,
modificación de líneas confirmadas, reserva previa a validar estado, numeración COUNT+1 concurrente, entrega antes de validar
estado, ausencia de envío automático y configuración incompleta del correo/Beat.

La reserva del pedido confirmado ahora es permanente: permanece hasta cancelación o entrega; las reservas de carrito de otros
módulos mantienen su vencimiento normal. Los productos que no requieren stock no generan reserva.
Se incluyen migraciones incrementales y actualización de pedidos/reservas anteriores que todavía conservan su asociación.
Los pedidos históricos sin propietario no se asignan automáticamente a una persona.

La tarea usa bloqueo y `notificado_listo` para evitar reenvíos normales. Existe la ventana habitual SMTP aceptado/commit
fallido: no se promete entrega exactamente una vez ni recepción en bandeja del destinatario. Un email aceptado por el SMTP
de pruebas demuestra entrega al servidor, no a un proveedor externo de producción.

# 2. MATRIZ DE APLICATIVOS Y HERRAMIENTAS REQUERIDAS (STACK 2026-2027)

| Nivel de Prueba | Librería / Framework Principal | Aplicativo / Motor Necesario | Propósito en el Módulo | Comando de Instalación |
|---|---|---|---|---|
| Unit | pytest 8.2.0, pytest-cov 5.0.0, unittest.mock | Python 3.11 | Estados, cantidades, horarios y reconfirmación | `rtk proxy python -m pip install -r requirements/testing.txt` |
| Integration | pytest-django 4.8.0, testcontainers[mysql] 4.15.0, mysqlclient 2.2.4 | Docker con motor Linux + MySQL 8.4.3 | ORM, rollback y dos escritores | Mismo requirements; `rtk proxy docker version` verifica el motor instalado |
| System/E2E | Playwright 1.64.0 | Chromium | Registro → login → carrito → recojo → cancelación | `rtk proxy python -m playwright install chromium` |
| Performance | k6 2.3.0 | CLI k6 | Dos clientes, consultas propias y rechazo de pedidos ajenos | Windows: `rtk proxy python scripts/qa_download_tools.py k6` |
| UAT | pytest-bdd 9.0.0 | pytest | Cuatro escenarios Gherkin sobre vistas y BD reales | Incluido en requirements/testing.txt |
| Mensajería | Celery 5.4.0, redis 5.0.4 | Redis y SMTP | Worker real y entrega por socket | Incluidos en requirements; servicios en docker-compose.yml |

Docker Desktop es una opción en Windows; se necesita el **motor Docker**, no dos instalaciones.
Testcontainers normaliza `localhost` a `127.0.0.1` para utilizar TCP y el puerto publicado, evitando el socket MySQL local.
La validación local de este equipo puede usar MySQL/Redis portables aislados porque Docker no está instalado.
Ese resultado se identifica como nativo, no como ejecución de Testcontainers.

# 3. ESTRUCTURA DE DIRECTORIOS DE TESTING (SCAFFOLDING)

```text
proyecto_ventas/
|-- .cursor/rules/orders-testing.mdc
|-- .github/workflows/full-quality.yml
`-- puntoventa_total/
    |-- docs/testing/pedidos_online.md
    |-- tests/
    |   |-- unit/domain/test_pedidos_online.py
    |   |-- integration/
    |   |   |-- test_pedidos_online.py
    |   |   |-- test_pedidos_online_mysql.py
    |   |   |-- test_smtp_real.py
    |   |   `-- test_redis_celery_real.py
    |   |-- system/
    |   |   |-- test_pedidos_online_playwright.py
    |   |   `-- test_pedidos_online_k6.py
    |   |-- performance/k6_pedidos.js
    |   `-- uat/
    |       |-- features/pedidos_online.feature
    |       `-- test_pedidos_online_bdd.py
    |-- scripts/qa_inventory_mysql.py
    |-- scripts/qa_inventory_mysql_native.py
    |-- scripts/qa_redis_native.py
    `-- reports/  (JUnit, cobertura, k6 y browser/*.zip; ignorado por Git)
```

# 4. NIVEL 1: PRUEBAS UNITARIAS (UNIT TESTING)

## 4.1 Qué se evalúa en este módulo

Los estados terminales no aceptan cancelación; preparación tampoco. El borrador admite descarte interno y Pendiente admite
cancelación; la vista del cliente restringe explícitamente la operación a Pendiente. Se rechazan cantidades no enteras,
negativas/cero, segundos en la franja, cambios de líneas confirmadas y reconfirmación antes de tocar inventario.

## 4.2 Aplicativos y Librerías a usar

pytest + unittest.mock; ninguna BD ni servidor para las reglas del agregado.

## 4.3 Guía Paso a Paso de Configuración y Ejecución

Desde `puntoventa_total`, con el entorno activado:

```powershell
rtk proxy python -m pip install -r requirements/testing.txt
rtk proxy python -m pytest tests/unit/domain/test_pedido.py tests/unit/domain/test_pedidos_online.py tests/unit/application/test_confirmar_pedido.py -q -p no:cacheprovider
rtk proxy python -m pytest tests/unit -q -p no:cacheprovider --cov=src --cov-fail-under=0 --cov-report=json:reports/audit_unit_coverage.json
rtk proxy python scripts/qa_unit_gate.py
```

## 4.4 Código Completo del Test Unitario

Código ejecutable completo: `tests/unit/domain/test_pedidos_online.py` y
`tests/unit/application/test_confirmar_pedido.py`. Utilizan `PedidoAggregate`, `Pedido`, `EstadoPedido` y `ConfirmarPedido`
del proyecto; incluyen éxito, borde y excepciones, sin entidades ficticias de ejemplo.

# 5. NIVEL 2: PRUEBAS DE INTEGRACIÓN (INTEGRATION TESTING)

## 5.1 Qué se evalúa en este módulo

RF-030..037 por formularios y ORM reales: normalización y duplicados de email/DNI, hash, login, aislamiento por propietario,
CSRF, horarios, datos persistidos, reservas acumuladas, rollback ante agotamiento, cancelación tardía, estados de tienda,
entrega y recuperación del aviso fallido. InnoDB enfrenta dos confirmaciones o dos cancelaciones simultáneas.

## 5.2 Aplicativos y Librerías a usar

MySQL 8.4.3 efímero + Testcontainers. La suite completa agrega Redis/worker y SMTP local real.
SQLite sirve para iteración rápida, pero no demuestra bloqueos ni concurrencia de InnoDB.

## 5.3 Guía Paso a Paso de Configuración y Ejecución

Con Docker arrancado:

```powershell
rtk proxy docker version
rtk proxy python scripts/qa_inventory_mysql.py tests/integration/test_pedidos_online.py tests/integration/test_pedidos_online_mysql.py tests/integration/test_smtp_real.py --junitxml=reports/pedidos-integration.xml
```

Alternativa **nativa aislada de este equipo**, sin tocar el MySQL del negocio:

```powershell
rtk proxy .venv/Scripts/python.exe scripts/qa_inventory_mysql_native.py --basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --target tests/integration/test_pedidos_online.py --target tests/integration/test_pedidos_online_mysql.py --target tests/integration/test_smtp_real.py --report-prefix pedidos-integration
```

## 5.4 Código Completo del Test de Integración

Archivos completos: `tests/integration/test_pedidos_online.py`, `test_pedidos_online_mysql.py`, `test_smtp_real.py` y
`test_redis_celery_real.py`. La prueba SMTP comprueba RCPT, destinatario y asunto, incluyendo la tarea real; la prueba Redis
publica una tarea de pedido Listo en un worker real y verifica persistencia y mensaje.

# 6. NIVEL 3: PRUEBAS DE SISTEMA (SYSTEM / E2E & PERFORMANCE)

## 6.1 Qué se evalúa en este módulo

Chromium recorre registro público, login por email, catálogo, carrito, selección de hora, confirmación y cancelación.
Se verifica persistencia y stock, no solo texto visible. k6 usa dos sesiones independientes: cada cliente consulta su pedido
y obtiene 404 al consultar el ajeno. Son 10 iteraciones/20 peticiones; es un smoke de concurrencia, no una certificación de
capacidad máxima. Presupuesto p95 <500 ms, checks=100% y fallos HTTP inesperados=0.

## 6.2 Aplicativos y Librerías a usar

Playwright/Chromium y k6. El runner k6 utiliza el servidor de pruebas en Windows y Gunicorn del proyecto en Linux.
Las pruebas bloquean recursos CDN externos y esperan navegación/elementos, sin sleeps fijos.

## 6.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
rtk proxy python -m playwright install chromium
$env:QA_REQUIRE_BROWSER = '1'
$env:QA_K6_BINARY = 'C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/k6/v2.3.0/k6-v2.3.0-windows-amd64/k6.exe'
rtk proxy python scripts/qa_inventory_mysql.py tests/system/test_pedidos_online_playwright.py tests/system/test_pedidos_online_k6.py --junitxml=reports/pedidos-system.xml
```

## 6.4 Código Completo del Test de Sistema (E2E) + Script rápido de Carga/Performance

Los archivos completos son `tests/system/test_pedidos_online_playwright.py`, `test_pedidos_online_k6.py` y
`tests/performance/k6_pedidos.js`. El runner crea datos y sesiones efímeros; no se ejecuta contra clientes reales.
Evidencias: `reports/browser/*.zip`, `reports/k6-pedidos-summary.json` y `reports/k6-pedidos-output.txt`.

# 7. NIVEL 4: PRUEBAS DE ACEPTACIÓN (UAT / BDD)

## 7.1 Escenarios de Negocio en Formato Gherkin

`tests/uat/features/pedidos_online.feature` incluye cuatro escenarios completos Given/When/Then:
confirmar con hora, cancelar Pendiente, rechazar cancelación en preparación y avisar Listo por email.

## 7.2 Automatización del UAT o Checklist de Validación Manual

Step definitions completos en `tests/uat/test_pedidos_online_bdd.py`; ejercitan las vistas, repositorios y stock reales.
Para aceptación del negocio, revisar con una cuenta de cliente y una cuenta de tienda:

| Acción | Criterio verificable |
|---|---|
| Crear cuenta e iniciar sesión | DNI/nombre/email/teléfono obligatorios; acceso con email y contraseña |
| Agregar y confirmar | Total correcto, recojo en tienda, franja futura, estado Pendiente |
| Cancelar Pendiente | Cancelado y unidades nuevamente disponibles |
| Iniciar preparación e intentar cancelar | Sigue En preparación; conserva reserva |
| Marcar Listo | Se envía aviso al email de la cliente; error SMTP no se registra como éxito |
| Entregar | Entregado y descuento físico/lote exactamente una vez |
| Abrir pedido de otra cuenta | No revela pedido ni datos personales |

## 7.3 Guía Paso a Paso para ejecutar y aprobar el UAT

```powershell
rtk proxy python -m pytest tests/uat/test_pedidos_online_bdd.py -q -p no:cacheprovider --junitxml=reports/pedidos-uat.xml
```

El Product Owner registra fecha, versión, resultado y firma tras el checklist. Tests automatizados aprobados no sustituyen
su aceptación formal. No se inventaron horarios comerciales, cupos por franja ni políticas de no-show no proporcionadas.

# 8. GUÍA DE AI SKILLS, MCP Y AUTOMATIZACIÓN AGÉNTICA (CONTEXTO 2026-2027)

## 8.1 Configuración de Skill / Rule para el Agente de Código

Regla lista en `../.cursor/rules/orders-testing.mdc` respecto a la raíz `puntoventa_total`.
Mantiene invariantes, cuatro niveles, evidencias y prohibición de debilitar expectativas al reparar regresiones.
No instala plugins ni concede acceso a servicios del negocio.

## 8.2 Servidores MCP recomendados

Playwright MCP es opcional para explorar el flujo local y reproducir un fallo de UI; las pruebas versionadas permanecen
en pytest/Playwright. Configuración y limitaciones: [documentación oficial](https://playwright.dev/python/docs/getting-started-mcp).
Para datos, usar MySQL efímero y los repositorios de pruebas antes que añadir un servidor PostgreSQL ajeno al stack.
Un MCP de GitHub solo aporta valor al inspeccionar checks/artifacts; no es requisito del runner.
Las anotaciones read-only de MCP son metadatos, no sustituyen permisos efectivos:
[explicación oficial](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/).

## 8.3 Flujo de Auto-Healing

Dar al agente esta instrucción y el traceback: «Reproduce el fallo con los comandos de este documento; contrasta RF-030..037;
repara la causa; conserva permisos, estados y umbrales; ejecuta los cuatro niveles y adjunta las evidencias».
Primero ejecutar el nodo de pytest que falla, después el módulo y finalmente la suite completa con MySQL/Redis/k6.
Una modificación de negocio requiere actualizar primero el criterio de aceptación; el agente no debe inferirla de un fallo.
La tarea conserva pendientes, reintenta errores de transporte y se recupera por Beat cada 60 s;
[semántica de reintento de Celery 5.4](https://docs.celeryq.dev/en/v5.4.0/userguide/tasks.html).

# 9. PIPELINE CI/CD (QUALITY GATES)

Workflow ejecutable completo en `../.github/workflows/full-quality.yml` (raíz Git, no la carpeta .github anidada).
Orden existente, que descubre automáticamente estos archivos nuevos:

```yaml
# Comandos de los pasos del workflow completo; conservan dependencias y servicios de dicho archivo.
steps:
  - name: Unit
    run: python -m pytest tests/unit -q --cov=src --cov-fail-under=0 --cov-report=json:reports/audit_unit_coverage.json
  - name: Unit gate
    run: python scripts/qa_unit_gate.py
  - name: Integration
    run: python scripts/qa_inventory_mysql.py tests/integration
  - name: System
    run: python scripts/qa_inventory_mysql.py tests/system tests/e2e tests/functional tests/performance
  - name: UAT
    run: python -m pytest tests/uat -q
  - name: Global gate
    env:
      QA_REQUIRE_ALL_TESTS: '1'
    run: python scripts/qa_inventory_mysql.py tests --cov=src --cov-fail-under=80 --cov-report=xml:reports/full-coverage.xml --junitxml=reports/full-suite.xml
```

Usar el workflow completo, que instala dependencias/Chromium/k6 y provee Redis. El umbral efectivo es >=80%, tanto global
como dominio/aplicación desde unitarias. La validación completa rechaza skips/xfails. Main ya exige ambos perfiles de calidad;
las evidencias locales de esta ampliación no equivalen a un nuevo check remoto ejecutado.

# 10. MATRIZ DE TRAZABILIDAD DE PRUEBAS DEL MÓDULO

Comando base I: `rtk proxy python scripts/qa_inventory_mysql.py tests/integration/test_pedidos_online.py`.
U: `rtk proxy python -m pytest tests/unit/domain/test_pedidos_online.py -q`.
S: `rtk proxy python scripts/qa_inventory_mysql.py tests/system/test_pedidos_online_playwright.py tests/system/test_pedidos_online_k6.py`.
A: `rtk proxy python -m pytest tests/uat/test_pedidos_online_bdd.py -q`.

| ID Caso | Funcionalidad / Método del Módulo | Nivel | Tipo | Resultado Esperado | Comando de Ejecución |
|---|---|---|---|---|---|
| RF-030 | registro_web_view | Int/Sys | Positivo/Negativo | Cuenta CLIENTE, hash, datos obligatorios; duplicados no dejan cuentas huérfanas | I / S |
| RF-031 | login_view / AutenticarUsuario | Int/Sys | Positivo/Negativo | Email sin distinción de mayúsculas; contraseña errónea no autentica | I / S |
| RF-032 | AgregarProductoPedido | Unit/Int/Sys | Positivo/Borde | Total correcto, entero positivo, acumulado <= stock, solo borrador | U / I / S |
| RF-033 | checkout_view / ConfirmarPedido | Int/Sys/UAT | Positivo/Negativo | Recojo en tienda; confirmación y reservas atómicas | I / S / A |
| RF-034 | Pedido.asignar_hora_recojo / PedidoForm | Unit/Int/Sys | Positivo/Borde | Franja futura de 30 minutos, sin segundos | U / I / S |
| RF-035 | detalle/mis_pedidos/seguimiento | Int/Sys | Positivo/Negativo | Cinco estados visibles y aislamiento por dueño | I / S |
| RF-036 | CancelarPedido / cancelar_pedido_view | Unit/Int/Sys/UAT | Positivo/Negativo | Solo Pendiente; libera una vez; preparación bloquea | U / I / S / A |
| RF-037 | cambiar_estado_view / run / EmailNotifier | Int/UAT | Positivo/Negativo | LISTO encola tras commit; SMTP real; pendientes recuperables | I / A + tests SMTP/Redis |
| CONC-01 | confirmar/cancelar con SELECT FOR UPDATE | Int | Borde | Dos escritores: un éxito y un rechazo; una reserva | `rtk proxy python scripts/qa_inventory_mysql.py tests/integration/test_pedidos_online_mysql.py` |
| SEC-01 | pedido_propio / CSRF | Int/Sys | Negativo | 404 ajeno; 403 sin CSRF; GET no cancela | I / S |

# EVALUACIÓN FINAL DEL MÓDULO AUDITADO

Escala cualitativa técnica, no medición de cobertura ni garantía contractual:

- Testabilidad del Código Actual: **8/10**; dominio aislado, algunos casos de uso todavía construyen adaptadores de reservas.
- Cobertura Unitaria Alcanzable: **9/10**; reglas puras cubiertas; la cobertura medida se publica en los reportes.
- Aislamiento de Dependencias: **8/10**; puertos y dobles en unitarias; infraestructura real en integración.
- Preparación para CI/CD: **9/10**; cuatro niveles y dos perfiles existentes, pendiente ejecutar CI remoto de estos cambios.
- Resiliencia ante Fallos: **8/10**; rollback, bloqueo, pendientes de correo y carreras probados; SMTP externo no garantiza exactly-once.

# ESTADO DE CALIDAD (QUALITY READINESS)

| Área | Estado | Evidencia / límite |
|---|---|---|
| Unit Test Ready | Listo | pytest y gate de dominio/aplicación |
| Integration Ready | Listo | MySQL/InnoDB real, dos escritores, Redis/worker y SMTP local |
| System / E2E Ready | Listo | Chromium y k6 reales |
| UAT / Business Ready | Automatización lista; aprobación PO pendiente | Cuatro escenarios y checklist; la firma del negocio no se sustituye |

## Activación del módulo en el entorno del negocio

1. Revisar las migraciones incrementales `orders/0002..0004` e `inventory/0002` y el respaldo habitual del entorno.
2. Ejecutar `rtk proxy python manage.py migrate` con la configuración de **ese entorno**.
3. Configurar `EMAIL_HOST`, `EMAIL_PORT`, usuario/password si aplican, TLS/SSL y `DEFAULT_FROM_EMAIL`, según `.env.example`.
4. Reiniciar web, worker y Beat. En despliegue Docker existente: `rtk proxy docker compose up -d --build web worker beat`.
5. Confirmar un pedido de prueba, marcarlo Listo y verificar entrega al correo autorizado.

Development usa consola de correo; testing usa locmem salvo prueba SMTP explícita. Producción usa SMTP configurable.
El canal implementado para RF-037 es **email**. SMS sigue sin proveedor real; no se registra un SMS simulado como entrega.
Los tests se ejecutan contra infra efímera; no aplican migraciones ni envían mensajes a la base/cuentas reales del negocio.

## Evidencias de esta ejecución

Validación del 16 de octubre de 2026 (America/Lima), con infraestructura efímera nativa:

| Perfil | Pruebas aprobadas | Fallos / errores / omitidas | Cobertura global |
|---|---|---|---|
| Python 3.11.16 / Django 5.0.6 | 436/436 | 0 / 0 / 0 | 84,48% |
| Python 3.14.7 / Django 6.1.2 | 436/436 | 0 / 0 / 0 | 84,15% |

Unitarias: 238 aprobadas; gate de dominio/aplicación del perfil declarado: 89,99% (mínimo 80%).
k6 de pedidos: checks 100%, p95 20,49 ms (presupuesto 500 ms), dos sesiones aisladas.
MySQL 8.4.3/InnoDB, Redis 8.10.2, worker Celery real, SMTP local, Chromium y k6 2.3.0.
También pasaron el chequeo Django, consistencia de migraciones y análisis de nombres/importaciones de los archivos revisados.

Resultados finales y porcentajes en `reports/pedidos-production.xml`, `reports/pedidos-production-coverage.json`,
`reports/pedidos-qa.xml`, `reports/pedidos-qa-coverage.json` y `reports/k6-pedidos-summary.json`.
`reports/pedidos-final-evidence.json` resume ambos perfiles y valida conteos/umbrales.
Los cambios están en la copia local, sin nuevo despliegue ni ejecución remota de CI de esta ampliación.
No se afirma 100% de cobertura de código.
