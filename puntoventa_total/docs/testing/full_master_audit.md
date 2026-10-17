# 1. DIAGNÓSTICO ARQUITECTÓNICO Y DE TESTABILIDAD DEL MÓDULO

> Este documento conserva la auditoría inicial. Las correcciones y sus resultados actuales se
> registran en [full_fixes_results.md](full_fixes_results.md); sus estados sustituyen los hallazgos abiertos de esta instantánea.

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

Archivo `tests/unit/domain/test_auditoria_transversal.py`:

```python
"""Reglas de clientes y reportes fuera del flujo principal del POS."""
from datetime import date, timedelta

import pytest

from src.modules.customers.domain.entities.cliente import Cliente
from src.modules.reporting.domain.value_objects.rango_fechas import RangoFechas
from src.shared.domain.exceptions.validation_exception import ValidationException

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("campo,valor", [("email", "sin-arroba"), ("telefono", "abc"), ("puntos_fidelidad", -1)])
def test_cliente_rechaza_datos_invalidos(campo, valor):
    with pytest.raises(ValidationException):
        Cliente(nombre="Ana", **{campo: valor})


def test_canje_descuenta_saldo_y_rechaza_exceso_sin_mutarlo():
    cliente = Cliente(nombre="Ana", puntos_fidelidad=20)
    cliente.canjear_puntos(15)
    assert cliente.puntos_fidelidad == 5
    with pytest.raises(ValidationException):
        cliente.canjear_puntos(6)
    assert cliente.puntos_fidelidad == 5


def test_anonimizar_elimina_contacto_y_desactiva_cliente():
    cliente = Cliente(nombre="Ana", email="ana@example.test", telefono="999888777", direccion="Local 1")
    cliente.anonimizar()
    assert cliente.nombre == "CLIENTE ELIMINADO"
    assert (cliente.email, cliente.telefono, cliente.direccion, cliente.dni) == ("", "", "", None)
    assert not cliente.activo


def test_rango_mes_bisiesto_incluye_29_febrero():
    rango = RangoFechas.del_mes(date(2024, 2, 15))
    assert rango.desde == date(2024, 2, 1)
    assert rango.hasta == date(2024, 2, 29)
    assert len(rango.en_dias()) == 29


@pytest.mark.parametrize("dias", [-1, 367])
def test_rango_rechaza_inversion_y_exceso(dias):
    inicio = date(2026, 1, 1)
    with pytest.raises(ValidationException):
        RangoFechas(inicio, inicio + timedelta(days=dias))
```

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

Archivo `tests/integration/test_auditoria_seguridad.py`:

```python
"""Contratos de seguridad pendientes. --runxfail reproduce los defectos."""
import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User

from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@pytest.mark.xfail(strict=True, reason="AUD-01: login acepta next externo sin validar host")
def test_login_no_redirige_a_dominio_externo(client):
    usuario = SimpleNamespace(username="qa_login", rol="CLIENTE", nombre_completo="QA", id=str(uuid.uuid4()))
    with patch("src.modules.identity.presentation.views.login_view.AutenticarUsuario") as caso:
        caso.return_value.ejecutar.return_value = usuario
        respuesta = client.post("/login/?next=https://example.invalid/", {"username": "qa_login", "password": "Prueba123!"})
    assert respuesta.status_code == 302
    assert not respuesta["Location"].startswith("https://example.invalid")


@pytest.fixture
def cliente_ajeno(db):
    return ClienteModel.objects.create(id=uuid.uuid4(), nombre="Cliente privado", email="privado@example.test", usuario_id=uuid.uuid4())


def test_perfil_rechaza_anonimo(client, cliente_ajeno):
    respuesta = client.get(f"/clientes/perfil/{cliente_ajeno.id}/")
    assert respuesta.status_code == 302
    assert "/login/" in respuesta["Location"]


@pytest.mark.xfail(strict=True, reason="AUD-02: perfil permite leer clientes ajenos")
def test_cliente_no_lee_perfil_ajeno(client, cliente_ajeno):
    client.force_login(User.objects.create_user(username="qa_otro"))
    sesion = client.session
    sesion["rol"] = "CLIENTE"
    sesion["usuario_id"] = str(uuid.uuid4())
    sesion.save()
    respuesta = client.get(f"/clientes/perfil/{cliente_ajeno.id}/")
    assert respuesta.status_code in (403, 404)


@pytest.mark.xfail(strict=True, reason="AUD-03: pagina no numerica provoca ValueError")
def test_listado_ventas_rechaza_paginacion_invalida(client):
    client.force_login(User.objects.create_user(username="qa_cajero"))
    sesion = client.session
    sesion["rol"] = "CAJERO"
    sesion.save()
    client.raise_request_exception = False
    respuesta = client.get("/pos/ventas/?pagina=abc")
    assert respuesta.status_code in (200, 400)
```

Archivo `scripts/qa_inventory_mysql.py`:

```python
"""Crea MySQL efimero y ejecuta pytest. Sin Docker/dependencias termina con 2."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import unquote, urlsplit


def main():
    docker = shutil.which("docker")
    if docker is None:
        print("Falta Docker CLI/Desktop. Instale e inicie Docker; este nivel NO se ejecuto.")
        return 2
    if subprocess.run([docker, "info"], capture_output=True).returncode:
        print("Docker Engine no responde. Este nivel NO se ejecuto.")
        return 2
    if importlib.util.find_spec("testcontainers") is None:
        print("Instale requirements/qa-inventory-mysql.txt. Este nivel NO se ejecuto.")
        return 2
    from testcontainers.mysql import MySqlContainer

    root = Path(__file__).resolve().parents[1]
    image = os.environ.get("INVENTORY_MYSQL_IMAGE", "mysql:8.4.3")
    with MySqlContainer(image, dialect="pymysql") as mysql:
        url = urlsplit(mysql.get_connection_url())
        env = dict(os.environ)
        env.update(
            DJANGO_SETTINGS_MODULE="config.settings.testing_mysql",
            INVENTORY_EPHEMERAL_MYSQL="1",
            QA_MYSQL_DATABASE=url.path.lstrip("/"),
            QA_MYSQL_USER=unquote(url.username),
            QA_MYSQL_PASSWORD=unquote(url.password),
            QA_MYSQL_HOST=url.hostname,
            QA_MYSQL_PORT=str(url.port),
        )
        targets = sys.argv[1:] or [
            "tests/integration/test_inventario_requisitos.py",
            "tests/integration/test_inventario_mysql.py",
        ]
        command = [sys.executable, "-m", "pytest", *targets, "--reuse-db", "-q", "-p", "no:cacheprovider"]
        return subprocess.run(command, cwd=root, env=env).returncode


if __name__ == "__main__":
    raise SystemExit(main())
```

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

Archivo `tests/system/test_e2e_pos_playwright.py`:

```python
"""Nivel 3 - Sistema (navegador): flujo real del POS en Chromium con Playwright.

Requisitos (seccion 6.3 del plan):
  pip install playwright && playwright install chromium
  pytest -m system tests/system/test_e2e_pos_playwright.py

Si Chromium no esta instalado o el modulo falta, el test se omite sin romper
la suite (el nivel 3 ya queda cubierto igualmente por test_flujo_pos_sistema).
"""
import os
from pathlib import Path
import re
import uuid
from datetime import date
from decimal import Decimal

import pytest

# La API sincrona de Playwright mantiene un event loop de asyncio corriendo en
# el hilo principal mientras dura el contexto; Django bloquearia el ORM con
# SynchronousOnlyOperation. En un unico test de sistema este escape hatch es
# seguro (documentado por Django como "unsafe" solo para escenarios como este).
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")

try:
    import playwright.sync_api as playwright_sync
except ImportError:
    if os.environ.get("QA_REQUIRE_BROWSER") == "1":
        raise
    pytest.skip("Requiere: pip install playwright", allow_module_level=True)

from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO  # noqa: E402
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario  # noqa: E402
from src.modules.identity.domain.enums.rol_usuario import RolUsuario  # noqa: E402
from src.modules.identity.infrastructure.factories import (  # noqa: E402
    construir_hasher,
    construir_repositorio,
)
from src.modules.cash_register.infrastructure.persistence.django_models.turno_caja_model import (  # noqa: E402
    TurnoCajaModel,
)
from src.modules.catalog.infrastructure.persistence.django_models.producto_model import (  # noqa: E402
    ProductoModel,
)
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import (  # noqa: E402
    ExistenciaModel,
)
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import (  # noqa: E402
    LoteModel,
)
from src.modules.sales.infrastructure.persistence.django_models.venta_model import (  # noqa: E402
    VentaModel,
)

pytestmark = [pytest.mark.system, pytest.mark.e2e, pytest.mark.django_db]

CODIGO_BARRAS = "7759998887777"
USUARIO = "cajero_ui"
PASSWORD = "Secreta123"


@pytest.fixture
def navegador(request):
    motor = playwright_sync.sync_playwright().start()
    try:
        browser = motor.chromium.launch()
    except playwright_sync.Error as exc:
        motor.stop()
        if os.environ.get("QA_REQUIRE_BROWSER") == "1":
            pytest.fail(f"Chromium requerido por el gate de CI: {exc}")
        pytest.skip(f"Chromium no disponible (playwright install chromium): {exc}")
    contexto = browser.new_context()
    # La suite valida recursos locales; no depende de disponibilidad de CDN.
    from urllib.parse import urlsplit
    contexto.route("**/*", lambda route: route.continue_()
                   if urlsplit(route.request.url).hostname in {"localhost", "127.0.0.1"} else route.abort())
    contexto.tracing.start(screenshots=True, snapshots=True, sources=True)
    try:
        yield contexto
    finally:
        carpeta = Path("reports/browser")
        carpeta.mkdir(parents=True, exist_ok=True)
        nombre = re.sub(r"[^a-zA-Z0-9_-]", "_", request.node.nodeid)
        contexto.tracing.stop(path=str(carpeta / f"{nombre}.zip"))
        contexto.close()
        browser.close()
        motor.stop()


@pytest.fixture
def datos_pos():
    """Usuario cajero real (login por UI) + producto con stock sembrado."""
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(
        UsuarioInputDTO(
            username=USUARIO,
            password=PASSWORD,
            nombre_completo="Cajero UI",
            rol=RolUsuario.CAJERO.value,
        )
    )
    producto = ProductoModel.objects.create(
        id=uuid.uuid4(),
        nombre="Arroz 1kg",
        codigo_barras=CODIGO_BARRAS,
        costo=Decimal("5.00"),
        precio_venta=Decimal("8.50"),
        estado="ACTIVO",
    )
    ExistenciaModel.objects.create(
        id=uuid.uuid4(), producto_id=producto.id, cantidad=10, reservada=0
    )
    LoteModel.objects.create(
        id=uuid.uuid4(),
        producto_id=producto.id,
        numero_lote="L-UI-01",
        cantidad_inicial=10,
        cantidad_restante=10,
        fecha_recepcion=date.today(),
    )
    return producto


def _login(page, base_url: str):
    page.goto(f"{base_url}/")
    page.fill("input[name=username]", USUARIO)
    page.fill("input[name=password]", PASSWORD)
    page.click("button:has-text('Ingresar')")


def test_flujo_completo_del_pos_en_el_navegador(live_server, navegador, datos_pos):
    page = navegador.new_page()

    # 1. autenticacion por UI (login real del sistema)
    _login(page, live_server.url)

    # 2. apertura de caja
    page.goto(f"{live_server.url}/caja/apertura/")
    page.fill("input[name=monto_apertura]", "150.00")
    page.click("button:has-text('Abrir caja')")
    page.wait_for_url("**/pos/**")
    assert TurnoCajaModel.objects.count() == 1

    # 3. el POS crea la venta en sesion (se lee del encabezado)
    page.wait_for_selector("#buscador-pos")
    venta_id = re.search(r"Ticket en curso:\s*([0-9a-f-]{36})", page.content()).group(1)

    # 4. escanear codigo de barras -> un solo resultado -> auto-agrega al carrito
    page.fill("#buscador-pos", CODIGO_BARRAS)
    page.press("#buscador-pos", "Enter")
    page.wait_for_load_state("networkidle")
    assert VentaModel.objects.get(pk=venta_id).total == Decimal("8.50")

    # 5. cobrar en efectivo: 8.50 de 10.00 (vuelto 1.50)
    page.goto(f"{live_server.url}/pos/venta/{venta_id}/pago/")
    page.select_option("select[name=metodo]", "EFECTIVO")
    page.fill("input[name=monto]", "8.50")
    page.fill("input[name=monto_entregado]", "10.00")
    # Chromium sin interfaz puede descargar el PDF inline sin cambiar la URL.
    # La respuesta del ticket y la BD prueban el cobro en ambos modos.
    with page.expect_response(
        lambda response: response.url.endswith(f"/pos/venta/{venta_id}/ticket/")
    ) as ticket_emitido:
        page.click("button:has-text('Confirmar cobro')")
    assert ticket_emitido.value.status == 200
    assert ticket_emitido.value.headers["content-type"] == "application/pdf"

    # 6. verificacion de negocio directamente en la BD
    venta = VentaModel.objects.get(pk=venta_id)
    assert venta.estado == "PAGADA"
    assert venta.total == Decimal("8.50")
    assert ExistenciaModel.objects.get(producto_id=datos_pos.id).cantidad == 9

    # 7. descarga autenticada con las mismas cookies del navegador
    ticket = page.context.request.get(f"{live_server.url}/pos/venta/{venta_id}/ticket/")
    assert ticket.status == 200
    assert ticket.headers["content-type"] == "application/pdf"
    assert ticket.body().startswith(b"%PDF")
```

Archivo `tests/performance/k6_catalog_audit.js`:

```javascript
// Carga de lectura: apuntar solo a un despliegue QA con catalogo sembrado.
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '20s',
  thresholds: {
    http_req_failed: ['rate==0'],
    checks: ['rate==1'],
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
  const base = __ENV.BASE_URL;
  if (!base) throw new Error('Defina BASE_URL de un entorno QA');
  const response = http.get(`${base}/catalogo/`);
  check(response, {
    'catalogo publico HTTP 200': (r) => r.status === 200,
    'pagina de catalogo, sin login': (r) => r.body.includes('producto') && !r.body.includes('name="password"'),
  });
  sleep(0.5);
}
```

# 7. NIVEL 4: PRUEBAS DE ACEPTACIÓN (UAT / BDD)

## 7.1 Escenarios de Negocio en Formato Gherkin

Se conserva la feature real de ventas (cinco escenarios), junto con inventario y catálogo existentes.

Archivo `tests/uat/features/ventas_pos.feature`:

```gherkin
Feature: Cobro y anulacion en el punto de venta
  Como cajero del local
  Quiero cobrar ventas con efectivo, aplicar descuentos autorizados y anular tickets
  Para que el ticket, el vuelto y el stock siempre reflejen la venta real

  Rule: RN-08 - El vuelto nunca puede ser negativo
  Rule: RN-06 - Una venta no se cierra sin pago total ni se anula dos veces
  Rule: RN-07 - El descuento total no puede superar 50%

  Scenario: Cobro completo en efectivo genera el vuelto correcto
    Given una venta en borrador con 1 "Pan" a "10.00"
    And la caja registra un pago de "10.00" con "20.00" entregados en efectivo
    When el cajero cierra la venta
    Then la venta queda "PAGADA"
    And el vuelto del cajero es "10.00"

  Scenario: Un pago parcial no puede cerrar la venta
    Given una venta en borrador con 1 "Pan" a "10.00"
    And la caja registra un pago de "4.00" con "4.00" entregados en efectivo
    When el cajero intenta cerrar la venta
    Then el cierre se rechaza por saldo pendiente
    And la venta sigue en estado "BORRADOR"

  Scenario: El gerente no puede aplicar un descuento mayor al 50%
    Given una venta en borrador con 1 "Camiseta" a "20.00"
    When el gerente aplica un descuento del "60" por ciento a la venta
    Then el descuento se rechaza con el tope de 50 por ciento
    And la venta sigue en estado "BORRADOR"

  Scenario: Aplicar exactamente el tope de descuento del 50% si es posible
    Given una venta en borrador con 1 "Camiseta" a "20.00"
    When el gerente aplica un descuento del "50" por ciento a la venta
    Then el total de la venta queda en "10.00"
    And la venta sigue en estado "BORRADOR"

  Scenario: Anular una venta pagada devuelve stock y solo puede hacerse una vez
    Given una venta pagada con 1 "Pan" a "10.00"
    When el gerente anula la venta con motivo "cliente se equivoco"
    Then la venta queda "ANULADA"
    And el inventario recibe una devolucion de stock
    When el gerente anula la venta con motivo "segundo intento"
    Then la segunda anulacion se rechaza
    And el inventario no recibe una segunda devolucion
```

## 7.2 Automatización del UAT (Step Definitions) o Checklist de Validación Manual

Los steps de ventas validan reglas con puertos externos simulados; no prueban entrega de SMS,
stock persistido ni permisos UI. Esas garantías corresponden a integración/sistema.

Archivo `tests/uat/test_ventas_bdd.py`:

```python
"""Nivel 4 - UAT/BDD: automatizacion de los escenarios Gherkin del POS.

Los step definitions ejercitan los casos de uso y el agregado REALES del
modulo sales; solo los puertos externos (inventario, auditoria) se sustituyen
por dobles. Aprobacion formal del Product Owner: ver
docs/testing/test_master_plan.md, seccion 7.3.
"""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from src.modules.sales.application.use_cases.anular_venta import AnularVenta
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.pago import Pago
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.exceptions.venta_exceptions import (
    PagoInsuficiente,
    VentaException,
)
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.uat

scenarios("features/ventas_pos.feature")


# --- fixtures compartidas --------------------------------------------------


@pytest.fixture
def contexto():
    """Memoria del escenario: ultimo error capturado y dobles de inventario."""
    return {"error": None, "inventario": None, "devoluciones": 0}


def _venta(cantidad: int, producto: str, precio: str) -> VentaAggregate:
    agregado = VentaAggregate(venta=Venta(numero_ticket="TUAT", cajero_id="cajero-1"))
    agregado.agregar_producto("p1", producto, cantidad, Monto(Decimal(precio)))
    agregado.calcular_totales()
    return agregado


# --- Given -----------------------------------------------------------------


@given(
    parsers.parse('una venta en borrador con {cantidad:d} "{producto}" a "{precio}"'),
    target_fixture="venta",
)
def venta_en_borrador(cantidad: int, producto: str, precio: str) -> VentaAggregate:
    return _venta(cantidad, producto, precio)


@given(
    parsers.parse('una venta pagada con {cantidad:d} "{producto}" a "{precio}"'),
    target_fixture="venta",
)
def venta_pagada(cantidad: int, producto: str, precio: str) -> VentaAggregate:
    agregado = _venta(cantidad, producto, precio)
    total = Decimal(str(agregado.venta.total))
    agregado.registrar_pago(Pago.efectivo("TUAT", Monto(total)))
    agregado.cerrar()
    return agregado


@given(parsers.parse('la caja registra un pago de "{monto}" con "{entregado}" entregados en efectivo'))
def caja_registra_pago(venta: VentaAggregate, monto: str, entregado: str) -> None:
    venta.registrar_pago(
        Pago.efectivo("TUAT", Monto(Decimal(monto)), Monto(Decimal(entregado)))
    )


# --- When ------------------------------------------------------------------


@when("el cajero cierra la venta")
def cajero_cierra(venta: VentaAggregate) -> None:
    venta.cerrar()


@when("el cajero intenta cerrar la venta")
def cajero_intenta_cerrar(venta: VentaAggregate, contexto: dict) -> None:
    try:
        venta.cerrar()
    except PagoInsuficiente as exc:
        contexto["error"] = exc


@when(parsers.parse('el gerente aplica un descuento del "{pct:d}" por ciento a la venta'))
def gerente_aplica_descuento(venta: VentaAggregate, pct: int, contexto: dict) -> None:
    try:
        venta.aplicar_descuento_venta(Decimal(pct))
        venta.calcular_totales()
    except VentaException as exc:
        contexto["error"] = exc


@when(parsers.parse('el gerente anula la venta con motivo "{motivo}"'))
def gerente_anula(venta: VentaAggregate, motivo: str, contexto: dict) -> None:
    repo, inventario, auditoria = MagicMock(), MagicMock(), MagicMock()
    repo.buscar_por_id.return_value = venta
    contexto["inventario"] = inventario
    try:
        AnularVenta(repo, inventario, auditoria).ejecutar("v1", motivo, "gerente-1")
    except VentaException as exc:
        contexto["error"] = exc
    else:
        if inventario.devolver.call_count:
            contexto["devoluciones"] += 1


# --- Then ------------------------------------------------------------------


@then(parsers.parse('la venta queda "{estado}"'))
def venta_queda(venta: VentaAggregate, estado: str) -> None:
    assert venta.venta.estado.value == estado


@then(parsers.parse('la venta sigue en estado "{estado}"'))
def venta_sigue_en(venta: VentaAggregate, estado: str) -> None:
    assert venta.venta.estado.value == estado


@then(parsers.parse('el vuelto del cajero es "{vuelto}"'))
def vuelto_es(venta: VentaAggregate, vuelto: str) -> None:
    ultimo_pago = venta.pagos[-1]
    assert ultimo_pago.vuelto is not None
    assert ultimo_pago.vuelto.valor == Decimal(vuelto)


@then("el cierre se rechaza por saldo pendiente")
def cierre_rechazado(contexto: dict) -> None:
    assert isinstance(contexto["error"], PagoInsuficiente)
    assert contexto["error"].faltante == 6.0


@then("el descuento se rechaza con el tope de 50 por ciento")
def descuento_rechazado(contexto: dict) -> None:
    assert isinstance(contexto["error"], VentaException)
    assert "50%" in str(contexto["error"])


@then(parsers.parse('el total de la venta queda en "{total}"'))
def total_es(venta: VentaAggregate, total: str) -> None:
    assert Decimal(str(venta.venta.total)) == Decimal(total)


@then("el inventario recibe una devolucion de stock")
def inventario_recibe_devolucion(contexto: dict) -> None:
    assert contexto["inventario"].devolver.call_count == 1


@then("la segunda anulacion se rechaza")
def segunda_anulacion_rechazada(contexto: dict) -> None:
    assert isinstance(contexto["error"], VentaException)
    assert contexto["error"].codigo == "VENTA_NO_MODIFICABLE"


@then("el inventario no recibe una segunda devolucion")
def sin_segunda_devolucion(contexto: dict) -> None:
    assert contexto["inventario"].devolver.call_count == 0
    assert contexto["devoluciones"] == 1
```

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

Archivo `../.cursor/rules/full-testing.mdc`:

```markdown
---
description: Pruebas y auditoria transversal de PuntoVenta Total
globs: puntoventa_total/src/**/*.py,puntoventa_total/tests/**/*.py
alwaysApply: false
---

Deriva criterios de las reglas de negocio documentadas; no conviertas el comportamiento actual en especificacion.
Conserva cambios locales ajenos. Ejecuta comandos desde puntoventa_total y aplica las instrucciones AGENTS.md/RTK.md.
Unit: dominio y casos de uso con puertos aislados, sin ORM ni servicios externos.
Integration: ORM real; usa scripts/qa_inventory_mysql.py para locking, rollback y concurrencia InnoDB.
System: HTTP, CSRF, roles, propiedad de recursos, Chromium y evidencia de ticket/stock.
UAT: Gherkin y pytest-bdd; requiere aprobacion del responsable de negocio para declarar aceptacion.
Una reparacion nunca reduce assertions, gates o permisos para conseguir verde.
Los AUD-01/02/03 en test_auditoria_seguridad.py son defectos pendientes, no exenciones: ejecutar --runxfail.
Si se corrige un defecto, quitar su xfail y verificar positivo/negativo, aislamiento y suite relacionada.
Reportar aprobados, fallidos, omitidos, xfail, cobertura exacta y codigo de salida.
No equiparar SQLite a MySQL, eager a worker Celery real o locmem a Redis.
No afirmar zero-flakiness ni cobertura completa por una sola ejecucion.
No usar credenciales reales, publicar artefactos ni enviar datos a MCP externos sin autorizacion.
```

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

Archivo `../.github/workflows/full-quality.yml`:

```yaml
name: Full quality audit
on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: full-quality-${{ github.ref }}
  cancel-in-progress: true
defaults:
  run:
    working-directory: puntoventa_total
jobs:
  quality:
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    env:
      DJANGO_SETTINGS_MODULE: config.settings.testing
      QA_REQUIRE_BROWSER: '1'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14.7'
          cache: pip
          cache-dependency-path: puntoventa_total/requirements/*.txt
      - name: System dependencies
        run: sudo apt-get update && sudo apt-get install -y pkg-config default-libmysqlclient-dev build-essential
      - name: Python dependencies
        run: python -m pip install -r requirements/qa-inventory-mysql.txt
      - name: Django checks
        run: python manage.py check --settings=config.settings.testing
      - name: '1 - Unit'
        run: python -m pytest tests/unit -q --cov=src --cov-fail-under=0 --cov-report=json:reports/audit_unit_coverage.json --junitxml=reports/full-unit.xml
      - name: Unit domain and application coverage gate
        run: python scripts/qa_unit_gate.py
      - name: '2 - Integration on disposable MySQL (including known security defects)'
        run: python scripts/qa_inventory_mysql.py tests/integration --runxfail --junitxml=reports/full-integration.xml
      - name: Install Chromium
        run: python -m playwright install --with-deps chromium
      - name: '3 - System and performance budgets'
        run: python -m pytest tests/system tests/e2e tests/functional tests/performance -q --junitxml=reports/full-system.xml
      - name: '4 - Acceptance'
        run: python -m pytest tests/uat -q --junitxml=reports/full-uat.xml
      - name: Global coverage gate (all levels)
        run: python -m pytest -q --runxfail --cov=src --cov-fail-under=80 --cov-report=xml:reports/full-coverage.xml --junitxml=reports/full-suite.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: full-quality-evidence
          path: puntoventa_total/reports/
```

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
| e2e | 4 | 0 | 0 | 0 |
| functional | 8 | 0 | 0 | 0 |
| integration | 88 | 0 | 5 | 3 |
| performance | 3 | 0 | 0 | 0 |
| system | 13 | 0 | 0 | 0 |
| uat | 15 | 0 | 0 | 0 |
| unit | 219 | 0 | 0 | 0 |

Cobertura de líneas por módulo, sumando todos los niveles (no branches):

| Módulo | Líneas cubiertas/ejecutables | Cobertura |
|---|---:|---:|
| __init__.py | 0/0 | 0.00% |
| auditing | 146/221 | 66.06% |
| cash_register | 318/457 | 69.58% |
| catalog | 616/705 | 87.38% |
| customers | 253/388 | 65.21% |
| identity | 375/498 | 75.30% |
| inventory | 1095/1164 | 94.07% |
| orders | 429/609 | 70.44% |
| promotions | 307/482 | 63.69% |
| reporting | 245/326 | 75.15% |
| sales | 960/1079 | 88.97% |
| shared | 241/272 | 88.60% |


Suite inicial: **341 passed, 5 skipped**, cobertura **79.76%**, salida 1 por gate.
Suite tras agregar 12 casos: **350 passed, 5 skipped, 3 xfailed**, cobertura
**80.39%**, salida 0. Unitaria aislada: **219 passed**.
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
