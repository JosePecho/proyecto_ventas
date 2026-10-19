# PuntoVenta Total

Sistema integral de punto de venta, inventario, pedidos web, caja, promociones y reportes.

Arquitectura: **monolito modular con Clean Architecture** por modulo (identidad, catalogo, inventario,
ventas, caja, pedidos, clientes, promociones, reportes, auditoria).

## Requisitos

- Python 3.11+
- MySQL 8
- Redis
- (Opcional) Docker + Docker Compose

## Instalacion local

    cd puntoventa_total
    python -m venv .venv
    .venv\Scripts\activate        (Linux/macOS: source .venv/bin/activate)
    pip install -r requirements/development.txt
    cp .env.development.example .env  # ajustar credenciales MySQL local
    python scripts/generar_clave_local.py
    python manage.py migrate
    python scripts/crear_admin.py
    python manage.py runserver

## Instalacion con Docker

Copiar `.env.example` a `.env`, generar una clave Django aleatoria y configurar
DB_PASSWORD, DB_ROOT_PASSWORD, hosts y correo. El proxy de produccion debe
terminar HTTPS. El override HTTPS proporciona la configuracion para Nginx;
`TLS_CERT_DIR` debe contener `fullchain.pem` y `privkey.pem` del dominio.
Para una demostracion local sin TLS usar el override indicado abajo.

    docker compose -f docker-compose.yml -f docker-compose.local.yml up --build

En produccion, con TLS configurado:

    docker compose -f docker-compose.yml -f docker-compose.https.yml up --build -d

## Estructura

    config/            Configuracion multi-entorno (base/development/production/testing)
    src/shared/        Capa transversal (dominio base, uow, cache, logging, seguridad)
    src/modules/       Modulos del negocio: domain / application / infrastructure / presentation
    templates/         Plantillas Django por modulo
    static/            CSS/JS (cola offline, IndexedDB, service worker)
    tests/             unit / integration / functional / e2e / performance
    scripts/           Semilla de datos, admin, backups, health checks
    deployment/        nginx, gunicorn, celery, init MySQL
    monitoring/        Prometheus y alertas
    docs/              Arquitectura, BD, requisitos, API, despliegue, testing

## Tests

La revision integral mas reciente esta en
[`docs/testing/revision_integral_2026_10_17.md`](docs/testing/revision_integral_2026_10_17.md).
Los planes anteriores conservan evidencia historica de la revision indicada en
cada documento. Para comprobar la conexion, migraciones y recursos del entorno
actual ejecutar `python scripts/check_runtime.py` (no muestra credenciales).

    pytest -m unit
    pytest -m integration
    pytest --cov=src

### Validacion transversal de los cuatro niveles

El workflow raiz `.github/workflows/full-quality.yml` ejecuta unitarias, integracion
MySQL efimera, sistema/navegador y UAT, en ese orden. Comprueba dos perfiles:
Python 3.11 con `requirements/testing.txt` (incluye base de produccion declarada),
y Python 3.14.7 con `requirements/qa-inventory-mysql.txt`.
Produccion usa Django 5.2.18 LTS; el perfil QA adicional usa Django 6.1.2.

Desde este directorio, con el entorno QA instalado:

    rtk proxy python -m pytest tests/unit --cov=src --cov-fail-under=0 --cov-report=json:reports/audit_unit_coverage.json --junitxml=reports/full-unit.xml
    rtk proxy python scripts/qa_unit_gate.py
    rtk proxy python scripts/qa_reportes_unit_gate.py --junit reports/full-unit.xml
    rtk proxy python scripts/qa_inventory_mysql.py tests/integration --runxfail
    rtk proxy python -m playwright install chromium
    rtk proxy python scripts/qa_inventory_mysql.py tests/system tests/e2e tests/functional tests/performance
    rtk proxy python scripts/qa_inventory_mysql.py tests/uat

Los comandos con Testcontainers requieren Docker iniciado. Para exigir los cuatro
niveles sin omisiones, definir `QA_REQUIRE_ALL_TESTS=1`, `QA_REQUIRE_BROWSER=1`,
`QA_REDIS_URL` hacia Redis exclusivo y `QA_K6_BINARY` hacia el ejecutable k6.
El plan siguiente incluye preparacion y comandos PowerShell completos.

### Planes y contratos RF-030 a RF-050

- [Plan maestro consolidado: diez secciones, codigo completo y evidencia de los cuatro niveles](docs/testing/plan_maestro_rf030_050.md).
- [Contrato de clientes frecuentes y promociones](docs/requirements/clientes_promociones_rf038_rf043.md).
- [Contrato de reportes y administracion](docs/requirements/reportes_admin_rf044_rf050.md).
- [Plan detallado del modulo 3.6](docs/testing/plan_maestro_rf044_050.md).

Regenerar el plan general con `rtk proxy python scripts/qa_build_rf030_050_report.py`
despues de capturar las evidencias de cada perfil. El verificador comprueba
SHA256 de fuentes, templates, estaticos, pruebas y artefactos; los resultados
historicos no acreditan automaticamente una revision posterior.

Para Redis/Celery real, CI levanta un Redis exclusivo y define `QA_REDIS_URL`.
Localmente, definir esa variable solo hacia una instancia aislada de QA;
`tests/integration/test_redis_celery_real.py` ejecuta un worker real, sin modo eager.
El resto de las pruebas usa locmem/eager y no sustituye esa comprobacion.

La carga de cobro con k6 requiere `BASE_URL`, `PMV_USERNAME_PREFIX`, `PMV_PASSWORD`
y `PMV_CODIGO`. Crear un cajero distinto por VU (prefijo1, prefijo2...), sin turno
abierto previo, y stock suficiente para `VUS * ITERATIONS`. Cada VU conserva su
propia sesion y toma el CSRF actualizado. Ejecutar solo en un entorno QA.

El adaptador SMS devuelve False mientras no exista proveedor configurado;
no representa una entrega real. Las correcciones y evidencia se documentan en
`docs/testing/full_fixes_results.md`.

### Suite completa sin omisiones (Windows)

La validacion con MySQL + Redis + worker real + SMTP local + navegador + k6 se
documenta en `docs/testing/complete_validation.md`, con comandos y evidencias por
perfil. El wrapper `scripts/qa_redis_native.py` crea procesos temporales aislados
y `QA_REQUIRE_ALL_TESTS=1` rechaza cualquier skip/xfail en la ejecucion completa.
La carga usa un proceso WSGI independiente sin instrumentacion de cobertura:
Gunicorn en Linux y Waitress 3.0.2 en Windows. El umbral de cobro sigue siendo
p95 < 100 ms. La cobertura de negocio se mide en las pruebas unitarias,
integracion y los otros flujos de sistema del mismo recorrido completo.

