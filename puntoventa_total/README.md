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
    cp .env.example .env          # ajustar valores
    python manage.py migrate
    python scripts/crear_admin.py
    python manage.py runserver

## Instalacion con Docker

    docker compose up --build

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

    pytest -m unit
    pytest -m integration
    pytest --cov=src

### Validacion transversal de los cuatro niveles

El workflow raiz `.github/workflows/full-quality.yml` ejecuta unitarias, integracion
MySQL efimera, sistema/navegador y UAT, en ese orden. Comprueba dos perfiles:
Python 3.11 con `requirements/testing.txt` (incluye base de produccion declarada),
y Python 3.14.7 con `requirements/qa-inventory-mysql.txt`.
No se cambiaron automaticamente las versiones de produccion al perfil QA.

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
En Linux, la carga usa Gunicorn con la configuracion del despliegue; el umbral de
cobro sigue siendo p95 < 100 ms. En Windows utiliza el servidor de Django.

