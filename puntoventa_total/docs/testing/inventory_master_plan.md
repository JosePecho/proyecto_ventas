# 1. DIAGNÓSTICO ARQUITECTÓNICO Y DE TESTABILIDAD DEL MÓDULO

Auditoria del 16/10/2026 sobre Inventario RF-016 a RF-024 y sus adaptadores de
Catalogo, Ventas, Pedidos y Reportes. Los archivos de este documento existen en el
repositorio; los bloques de codigo completos son una instantanea de esos archivos.
Las rutas y comandos siguientes parten de `puntoventa_total`, salvo indicacion.
No se presume la disponibilidad futura de productos o versiones de 2027.

## 1.1 Lenguaje, Runtime y Framework detectado

| Componente | Requisitos anteriores del repositorio | Observado y fijado en perfil QA / CI |
|---|---|---|
| Lenguaje | Python >= 3.11 | CPython 3.14.7, Windows; CI en 3.14.7 |
| Framework | Django 5.0.6 | Django 6.1.2 |
| Test runner | pytest 8.2.0, pytest-django 4.8.0 | pytest 9.1.1, pytest-django 4.14.0 |
| Cobertura | pytest-cov 5.0.0, coverage 7.5.3 | pytest-cov 7.1.0, coverage 7.16.2 |
| Propiedades / BDD | No declaradas anteriormente | Hypothesis 6.169.4, pytest-bdd 9.0.0 |
| Navegador | No declarado anteriormente | Playwright 1.64.0 con Chromium funcional |
| Persistencia | MySQL 8; contenedor QA mysql:8.4.3 | SQLite; Docker y mysqlclient ausentes |
| Redis / tareas | Redis 5.0.4, Celery 5.4.0 declarados | Cache local y tareas eager en testing |

El perfil QA independiente fija las versiones probadas y no modifica los requisitos
anteriores de produccion. Django 5.0 ya no recibe soporte segun la
[tabla oficial de Django](https://www.djangoproject.com/download/#supported-versions).
Hace falta resolver esa discrepancia antes de certificar un despliegue actual.
El runner Linux y los extras MySQL todavia no se ejecutaron en esta sesion.

Arquitectura: monolito modular Django con dominio, aplicacion, infraestructura y
presentacion. Modelo V: reglas/componentes -> unitarias; interfaces/persistencia ->
integracion; flujos -> sistema; RF y valor de negocio -> UAT. El plan toma como
referencia los procesos de prueba de [ISO/IEC/IEEE 29119-2:2021](https://www.iso.org/standard/79428.html),
sin afirmar una certificacion ISO ni conformidad integral con esa norma.

## 1.2 Mapa de Dependencias del Módulo

| Dependencia real | Aislar en nivel 1 | Verificar con infraestructura / frontera real |
|---|---|---|
| Existencia, Lote, MovimientoStock, ReservaStock, PoliticaStock | Entidades reales; reloj fijo en limites | Persistencia y conversion de fechas en nivel 2 |
| StockRepository, LoteRepository, MovimientoRepository, ReservaRepository | Mock con spec del puerto | ORM real, rollback y consistencia stock/lotes/kardex |
| UnitOfWork | NullUnitOfWork o espia por test | transaction.atomic y bloqueos de InnoDB |
| Catalogo y ventas | DTO y entidades reales segun unidad | Campos de producto, pago parcial/total y reintento |
| Reportes | Puerto aislado cuando corresponda | Ventas PAGADA de 60 dias y orden por margen |
| Email de stock minimo | Espia del notificador | outbox real en memoria tras commit; SMTP externo pendiente |
| Cache | No cachear cantidades del stock | Cache locmem en suite; Redis desplegado no ejercitado |
| Celery / beat | No broker ni worker | Eager no equivale a probar worker, beat, Redis o reintentos |
| UI, sesiones, roles y CSRF | Fuera de unitarias | Cliente Django, servidor HTTP y Chromium |

No hay cliente HTTP a un proveedor externo en el flujo de inventario analizado.
Por ello no se agregan httpx, asyncio, MSW ni un mock de una API inexistente.
Las pantallas actuales son HTML con sesiones y CSRF, no una API REST de inventario.

## 1.3 Deuda Técnica o Problemas de Testabilidad

| ID | Hallazgo inicial | Evidencia y efecto inicial | Correccion aplicada o trabajo pendiente |
|---|---|---|---|
| QA-INV-01, corregido | Liberacion de reserva sin idempotencia | Segunda liberacion consumia otra reserva | Retorno sin escrituras si ya liberada; bloqueo transaccional existente; regresiones unitarias y ORM aprobadas |
| QA-INV-02, corregido | datetime naive contra aware | Expiracion fallaba con fechas aware del ORM | Comparacion y extension conservan timezone; normalizacion al guardar y consulta con timezone.now; regresiones aprobadas |
| QA-INV-03, corregido | Cantidad no validada como entero | Existencia admitia cantidades fraccionarias | Constructor y cinco operaciones rechazan valores no enteros y bool sin cambiar estado; regresiones aprobadas |
| QA-INV-04 | PoliticaStock importa django.conf.settings | El dominio consulta configuracion global | Inyectar umbrales/configuracion desde aplicacion |
| QA-INV-05 | Otros modulos siguen sin migraciones iniciales versionadas | Tests crean sus tablas mediante sincronizacion | Versionar migraciones y probar upgrade desde esquema previo |
| QA-INV-06 | Dependencias declaradas distintas del runtime instalado | Django 5.0.6 frente a 6.1.2, entre otras | Resolver una baseline soportada y generar lock completo verificado |
| QA-INV-07 | CI previo fuera de la raiz y deploy con needs inexistente | Workflows en puntoventa_total/.github; deploy depende de tests de otro workflow | Nuevo workflow de QA en .github/workflows de la raiz; despliegue separado pendiente |

Los tres primeros hallazgos se reprodujeron en la auditoria inicial y ya fueron
corregidos: liberacion idempotente, comparacion de fechas con su zona horaria y
cantidades enteras estrictas. Se agregaron 53 regresiones unitarias y una prueba
de persistencia. El gate incluido ahora termina con codigo 0 y se conserva para
detectar reapariciones:

```powershell
python -m scripts.qa_inventory_findings
```

Archivo: `scripts/qa_inventory_findings.py`

```python
"""Reproduce riesgos de dominio detectados; no modifica BD ni codigo.

Exit 1 = hay hallazgos reproducidos. No es una prueba de aceptacion aprobada.
"""
from datetime import datetime, timezone
import json
from unittest.mock import Mock

from src.modules.inventory.application.use_cases.liberar_reserva import LiberarReserva
from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.entities.reserva_stock import ReservaStock
from src.modules.inventory.domain.exceptions.stock_exceptions import StockException
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.modules.inventory.domain.repositories.reserva_repository import ReservaRepository


def main():
    existencia = Existencia(producto_id="p1", cantidad=10, reservada=2)
    reserva = ReservaStock(producto_id="p1", cantidad=3, liberada=True)
    stock, reservas = Mock(spec=StockRepository), Mock(spec=ReservaRepository)
    stock.obtener.return_value = existencia
    reservas.buscar_por_id.return_value = reserva
    LiberarReserva(stock, reservas).ejecutar("reserva_ya_liberada")
    resultados = {
        "QA-INV-01": {"descripcion": "Liberar dos veces puede consumir la reserva de otro pedido",
                      "reservada_esperada": 2, "reservada_observada": existencia.reservada,
                      "reproducido": existencia.reservada != 2},
    }
    r = ReservaStock(producto_id="p1", cantidad=1, expira_en=datetime.now(timezone.utc))
    try:
        r.expirada
    except TypeError:
        resultados["QA-INV-02"] = {"descripcion": "Expiracion mezcla datetime naive y aware", "reproducido": True}
    else:
        resultados["QA-INV-02"] = {"reproducido": False}
    e = Existencia(producto_id="p1")
    try:
        e.aplicar_entrada(0.5)
    except StockException:
        fraccion_aceptada = False
    else:
        fraccion_aceptada = e.cantidad == 0.5
    resultados["QA-INV-03"] = {"descripcion": "El dominio admite cantidad fraccionaria pese al contrato entero",
                               "reproducido": fraccion_aceptada}
    print(json.dumps(resultados, ensure_ascii=False, indent=2))
    return int(any(r["reproducido"] for r in resultados.values()))


if __name__ == "__main__":
    raise SystemExit(main())
```

La configuracion de pruebas ahora usa un archivo SQLite temporal por proceso:
el servidor multihilo con una unica conexion SQLite en memoria produjo errores
de transaccion y cursores. Se retiro ademas el monkeypatch global de
transaction.atomic de las unitarias: los puertos/UoW se inyectan por caso.

# 2. MATRIZ DE APLICATIVOS Y HERRAMIENTAS REQUERIDAS (STACK 2026-2027)

| Nivel de Prueba | Libreria / Framework Principal | Aplicativo / Motor Necesario | Proposito en el Modulo | Comando de Instalacion |
| :--- | :--- | :--- | :--- | :--- |
| Unit | pytest 9.1.1, pytest-cov 7.1.0, Hypothesis 6.169.4, unittest.mock | Python 3.14.7, terminal | Invariantes, puertos y propiedades; gate 80 % | python -m pip install -r requirements/qa-inventory.txt |
| Integracion | pytest-django 4.14.0, testcontainers[mysql] 4.15.0, PyMySQL 1.2.3, mysqlclient 2.3.0 | Docker Desktop/Engine o MySQL 8.4.3 nativo efimero | Rollback y dos escritores InnoDB reales | python -m pip install -r requirements/qa-inventory-mysql.txt |
| Sistema / E2E | Playwright 1.64.0; pytest | Chromium descargado por Playwright | Operacion de almacen y cobro completo por UI, trazas | python -m playwright install chromium |
| Seguridad basica | Django Client con CSRF activo | Python / Django real | CSRF, escape HTML y X-Frame-Options | Incluido en requirements/qa-inventory.txt |
| Carga | Biblioteca estandar urllib + ThreadPoolExecutor | Servidor HTTP local o entorno QA desplegado | GET autenticados, errores, p95 y concurrencia acotada | No requiere Locust/k6 ni libreria adicional |
| UAT | pytest-bdd 9.0.0 | pytest y usuario de negocio para firma | Gherkin sobre vistas y repositorios reales | python -m pip install -r requirements/qa-inventory.txt |
| Exploracion opcional | Postman CLI / plugin existente | Postman, segun capacidades instaladas | Diagnostico HTTP puntual; no duplica el gate de formularios | postman --help |

Versiones exactas adicionales:

Archivo: `requirements/qa-inventory.txt`

```text
# Perfil QA independiente: versiones observadas y probadas con CPython 3.14.7.
# No altera los requisitos de produccion ni incluye el driver MySQL opcional.
Django==6.1.2
djangorestframework==3.18.3
django-environ==0.14.0
celery==5.6.3
redis==8.1.0
django-redis==7.0.0
Pillow==12.3.0
python-dateutil==2.9.0.post0
reportlab==5.0.1
cryptography==50.0.2
pytest==9.1.1
pytest-django==4.14.0
pytest-cov==7.1.0
coverage[toml]==7.16.2
hypothesis==6.169.4
pytest-bdd==9.0.0
playwright==1.64.0
```

Archivo: `requirements/qa-inventory-mysql.txt`

```text
# Extras verificados en PyPI; ejecucion con contenedor pendiente en esta maquina.
-r qa-inventory.txt
mysqlclient==2.3.0
testcontainers[mysql]==4.15.0
PyMySQL[rsa]==1.2.3
```

Los extras aun no instalados se fijaron consultando sus publicaciones primarias:
[Testcontainers](https://pypi.org/project/testcontainers/),
[mysqlclient](https://pypi.org/project/mysqlclient/) y [PyMySQL](https://pypi.org/project/PyMySQL/).
Esto verifica su publicacion, no una ejecucion del contenedor.

Instalacion de aplicaciones en Windows, si faltan (la instalacion puede requerir
permisos de administrador y reinicio para Docker/WSL2):

```powershell
winget install --exact --id Python.Python.3.14
winget install --exact --id Docker.DockerDesktop
docker version
docker info
```

En Linux, Docker Engine y sus permisos deben estar configurados. Para compilar el
driver MySQL en Ubuntu: `sudo apt-get install -y pkg-config default-libmysqlclient-dev build-essential`.
No es necesario instalar Postman, un MCP ni un IDE para ejecutar los cuatro niveles.

# 3. ESTRUCTURA DE DIRECTORIOS DE TESTING (SCAFFOLDING)

```text
proyecto_ventas/
|-- .github/workflows/inventory-quality.yml
|-- .cursor/rules/inventory-testing.mdc
`-- puntoventa_total/
    |-- config/settings/
    |   |-- testing.py
    |   `-- testing_mysql.py
    |-- requirements/qa-inventory.txt
    |-- requirements/qa-inventory-mysql.txt
    |-- scripts/
    |   |-- qa_inventory_mysql.py
    |   |-- qa_inventory_load.py
    |   `-- qa_inventory_findings.py
    |-- tests/
    |   |-- conftest.py
    |   |-- unit/
    |   |   |-- conftest.py
    |   |   `-- inventory/test_inventario_unitario.py
    |   |-- integration/
    |   |   |-- test_inventario_requisitos.py
    |   |   `-- test_inventario_mysql.py
    |   |-- system/
    |   |   |-- test_inventario_playwright.py
    |   |   |-- test_e2e_pos_playwright.py
    |   |   `-- test_inventario_seguridad_carga.py
    |   `-- uat/
    |       |-- features/inventario.feature
    |       `-- test_inventario_bdd.py
    |-- docs/testing/inventory_master_plan.md
    `-- reports/                     # generado e ignorado por Git
        |-- inventory-unit-coverage.xml
        |-- inventory-unit-coverage.json
        |-- inventory-load.json
        |-- inventory-regression.xml
        `-- browser/*.zip
```

# 4. NIVEL 1: PRUEBAS UNITARIAS (UNIT TESTING)

## 4.1 Qué se evalúa en este módulo

Existencia: entradas, salidas, reservas, disponible, minimo y rechazo de estados
imposibles. Lote: vencimiento, agotamiento y descuento. PoliticaStock: distribucion
PEPS y limites 0/30/31 dias. Aplicacion: recepcion, merma, ajuste, descuento,
reserva, confirmacion, liberacion, consultas y notificaciones. Una propiedad genera
75 combinaciones reproducibles de entradas/salidas y comprueba conservacion de stock.
No se reemplazan entidades ni reglas de negocio por mocks.

## 4.2 Aplicativos y Librerías a usar

Python, pytest, Hypothesis, unittest.mock, pytest-cov. Sin Docker, red ni ORM.
pytest-django bloquea consultas a BD en estos tests. El espia UoW comprueba su uso;
el rollback efectivo corresponde al nivel 2. Cobertura medida: lineas de
`inventory.domain` y `inventory.application`, no cobertura total del monolito ni
puntaje de mutacion.

## 4.3 Guía Paso a Paso de Configuración y Ejecución

Abrir PowerShell en el proyecto. Se crea otro entorno para preservar el instalado.
`$qaPython` se usa en los siguientes bloques dentro de la misma terminal:

```powershell
Set-Location C:\Users\mallq\OneDrive\Desktop\proyecto_ventas\puntoventa_total
py -3.14 -m venv .venv-qa
$qaPython = Join-Path (Get-Location) '.venv-qa\Scripts\python.exe'
& $qaPython -m pip install --upgrade pip
& $qaPython -m pip install -r requirements/qa-inventory.txt
& $qaPython -m pytest tests/unit/inventory -q --cov=src.modules.inventory.domain --cov=src.modules.inventory.application --cov-fail-under=80 --cov-report=xml:reports/inventory-unit-coverage.xml --cov-report=json:reports/inventory-unit-coverage.json
```

Resultado local observado usando el entorno ya instalado: **106 aprobadas, 95,95 %**
(635 de 662 sentencias). Esto no demuestra las invariantes que faltan: los
hallazgos QA-INV-01..03 son un contraejemplo concreto a equiparar cobertura con calidad.
La instalacion de la baseline aislada anterior no se ejecuto en esta sesion.

## 4.4 Código Completo del Test Unitario

Archivo: `tests/unit/inventory/test_inventario_unitario.py`

```python
"""Nivel 1: reglas reales de inventario sin ORM, red ni broker."""
from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from hypothesis import given, settings, strategies as st

from src.modules.inventory.application.dto.lote_dto import RecepcionLoteDTO
from src.modules.inventory.application.dto.stock_dto import AjusteStockDTO
from src.modules.inventory.application.use_cases.ajustar_stock import AjustarStock
from src.modules.inventory.application.use_cases.alertar_stock_minimo import AlertarStockMinimo
from src.modules.inventory.application.use_cases.alertar_vencimientos import AlertarVencimientos
from src.modules.inventory.application.use_cases.confirmar_salida_reservada import ConfirmarSalidaReservada
from src.modules.inventory.application.use_cases.consultar_kardex import ConsultarKardex
from src.modules.inventory.application.use_cases.consultar_lotes import ConsultarLotes
from src.modules.inventory.application.use_cases.consultar_stock import ConsultarStock
from src.modules.inventory.application.use_cases.descontar_stock import DescontarStock
from src.modules.inventory.application.use_cases.liberar_reserva import LiberarReserva
from src.modules.inventory.application.use_cases.recibir_mercaderia import RecibirMercaderia
from src.modules.inventory.application.use_cases.registrar_merma import RegistrarMerma
from src.modules.inventory.application.use_cases.reservar_stock import ReservarStock
from src.modules.inventory.domain.entities.existencia import Existencia
from src.modules.inventory.domain.entities.lote import Lote
from src.modules.inventory.domain.entities.movimiento_stock import MovimientoStock
from src.modules.inventory.domain.entities.reserva_stock import ReservaStock
from src.modules.inventory.domain.enums.tipo_movimiento import TipoMovimiento
from src.modules.inventory.domain.exceptions.stock_exceptions import (
    ExistenciaNegativa, LoteNoEncontrado, ReservaNoEncontrada, ReservaYaConfirmada,
    StockException, StockInsuficiente,
)
from src.modules.inventory.domain.repositories.lote_repository import LoteRepository
from src.modules.inventory.domain.repositories.movimiento_repository import MovimientoRepository
from src.modules.inventory.domain.repositories.reserva_repository import ReservaRepository
from src.modules.inventory.domain.repositories.stock_repository import StockRepository
from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit
HOY = date(2026, 10, 16)


@pytest.fixture(autouse=True)
def reloj_fijo(monkeypatch):
    class FechaFija(date):
        @classmethod
        def today(cls):
            return HOY

    class InstanteFijo(datetime):
        @classmethod
        def now(cls, tz=None):
            instante = datetime(2026, 10, 16, 12)
            return instante if tz is None else instante.replace(tzinfo=tz)

    monkeypatch.setattr("src.modules.inventory.domain.entities.lote.date", FechaFija)
    monkeypatch.setattr("src.modules.inventory.domain.entities.reserva_stock.datetime", InstanteFijo)
    monkeypatch.setattr("src.modules.inventory.domain.services.politica_stock.date", FechaFija)


def lote(cantidad=10, dias=10, producto="p1"):
    return Lote(producto_id=producto, numero_lote="L-UNIT", cantidad_inicial=cantidad,
                cantidad_restante=cantidad, costo_unitario=Monto(5),
                fecha_vencimiento=HOY + timedelta(days=dias))


@pytest.fixture
def puertos():
    stock = Mock(spec=StockRepository)
    stock.obtener.return_value = Existencia(producto_id="p1", cantidad=10)
    stock.umbral_minimo.return_value = 5
    lotes = Mock(spec=LoteRepository)
    lotes.listar_por_producto.return_value = [lote()]
    lotes.buscar_por_id.return_value = lote()
    movimientos = Mock(spec=MovimientoRepository)
    reservas = Mock(spec=ReservaRepository)
    reservas.buscar_por_id.return_value = ReservaStock(producto_id="p1", cantidad=2, referencia="PEDIDO:1")
    return SimpleNamespace(stock=stock, lotes=lotes, mov=movimientos, reservas=reservas)


@settings(max_examples=75, derandomize=True, deadline=None)
@given(inicial=st.integers(0, 10000), entrada=st.integers(1, 1000), salida=st.integers(1, 1000))
def test_propiedad_stock_se_conserva_y_nunca_es_negativo(inicial, entrada, salida):
    existencia = Existencia(producto_id="p1", cantidad=inicial)
    existencia.aplicar_entrada(entrada)
    antes = existencia.cantidad
    if salida > antes:
        with pytest.raises(StockInsuficiente):
            existencia.aplicar_salida(salida)
        assert existencia.cantidad == antes
    else:
        existencia.aplicar_salida(salida)
        assert existencia.cantidad == inicial + entrada - salida
    assert 0 <= existencia.reservada <= existencia.cantidad


@pytest.mark.parametrize("cantidad,reservada", [(-1, 0), (0, -1), (2, 3)])
def test_existencia_rechaza_estado_imposible(cantidad, reservada):
    with pytest.raises(ExistenciaNegativa):
        Existencia(producto_id="p1", cantidad=cantidad, reservada=reservada)


@pytest.mark.parametrize("metodo", ["aplicar_entrada", "aplicar_salida", "reservar", "liberar", "confirmar_reserva"])
@pytest.mark.parametrize("cantidad", [0, -1])
def test_cantidades_no_positivas_rechazadas(metodo, cantidad):
    with pytest.raises(StockException):
        getattr(Existencia(producto_id="p1", cantidad=10), metodo)(cantidad)


def test_reserva_libera_y_confirma_sin_alterar_disponible_indebidamente():
    existencia = Existencia(producto_id="p1", cantidad=10)
    existencia.reservar(4)
    existencia.liberar(1)
    assert existencia.disponible == 7
    existencia.confirmar_reserva(3)
    assert (existencia.cantidad, existencia.reservada, existencia.disponible) == (7, 0, 7)
    assert not existencia.con_stock_minimo(7)
    assert existencia.con_stock_minimo(8)
    with pytest.raises(StockInsuficiente):
        existencia.confirmar_reserva(1)


def test_peps_distribuye_y_omite_lotes_vencidos_sin_mutarlos():
    vencido, cercano, lejano = lote(10, -1), lote(3, 1), lote(9, 20)
    plan = PoliticaStock.planificar_salida_peps([lejano, vencido, cercano], 5)
    assert plan == [(cercano, 3), (lejano, 2)]
    assert [l.cantidad_restante for l in (vencido, cercano, lejano)] == [10, 3, 9]
    with pytest.raises(StockInsuficiente):
        PoliticaStock.planificar_salida_peps([vencido], 1)


@pytest.mark.parametrize("dias,esperado", [(-1, False), (0, True), (30, True), (31, False)])
def test_limites_alerta_vencimiento(dias, esperado):
    assert PoliticaStock.requiere_alerta_vencimiento(lote(dias=dias)) == esperado


def test_lote_valida_cantidad_y_agotamiento():
    with pytest.raises(ValidationException):
        lote(0)
    l = lote(2)
    with pytest.raises(ValidationException):
        l.descontar(0)
    with pytest.raises(StockInsuficiente):
        l.descontar(3)
    l.descontar(2)
    assert l.agotado
    l.fecha_vencimiento = None
    assert l.dias_para_vencer is None and not l.vencido()
    l.cantidad_restante = 3
    with pytest.raises(ValidationException):
        l.__post_init__()


def test_movimiento_signo_y_validaciones():
    entrada = MovimientoStock(producto_id="p1", tipo="ENTRADA", cantidad=2, stock_resultante=2)
    salida = MovimientoStock(producto_id="p1", tipo="MERMA", cantidad=1, stock_resultante=1)
    assert entrada.signo() == 1 and salida.signo() == -1
    with pytest.raises(ValidationException):
        MovimientoStock(producto_id="p1", cantidad=0)
    with pytest.raises(ValidationException):
        MovimientoStock(producto_id="p1", cantidad=1, stock_resultante=-1)
    assert TipoMovimiento.MERMA in PoliticaStock.tipos_que_descuentan()


def test_reserva_estados_y_expiracion():
    r = ReservaStock(producto_id="p1", cantidad=2, referencia="P:1")
    assert r.activa
    r.extender(30)
    r.confirmar()
    with pytest.raises(ReservaYaConfirmada):
        r.confirmar()
    with pytest.raises(ReservaYaConfirmada):
        r.liberar()
    with pytest.raises(ReservaYaConfirmada):
        r.extender()
    vencida = ReservaStock(producto_id="p1", cantidad=1, expira_en=datetime(2026, 10, 15))
    assert vencida.expirada and not vencida.activa
    with pytest.raises(ValidationException):
        ReservaStock(producto_id="p1", cantidad=0)


@pytest.mark.parametrize("fecha", [HOY, HOY.isoformat(), None])
def test_recibir_crea_lote_existencia_y_kardex(puertos, fecha):
    puertos.stock.obtener.return_value = None
    dto = RecepcionLoteDTO("p1", "L-UNIT", 4, 5, fecha_vencimiento=fecha)
    resultado = RecibirMercaderia(puertos.stock, puertos.lotes, puertos.mov).ejecutar(dto)
    assert resultado.cantidad_restante == 4
    assert puertos.stock.guardar.call_args.args[0].cantidad == 4
    assert puertos.mov.guardar.call_args.args[0].tipo == TipoMovimiento.ENTRADA


def test_descontar_distribuye_salidas_y_usa_uow(puertos):
    uow = Mock()
    uow.__enter__ = Mock(return_value=uow)
    uow.__exit__ = Mock(return_value=False)
    assert DescontarStock(puertos.stock, puertos.lotes, puertos.mov, uow=uow).ejecutar("p1", 3) == 7
    uow.__enter__.assert_called_once()
    uow.__exit__.assert_called_once_with(None, None, None)
    salida = puertos.mov.guardar.call_args.args[0]
    assert salida.cantidad == 3 and salida.stock_resultante == 7 and salida.lote_id


def test_descontar_sin_existencia_no_guarda(puertos):
    puertos.stock.obtener.return_value = None
    with pytest.raises(StockInsuficiente):
        DescontarStock(puertos.stock, puertos.lotes, puertos.mov).ejecutar("p1", 1)
    puertos.mov.guardar.assert_not_called()


@pytest.mark.parametrize("motivo", ["VENCIDO", "DANADO", "ROBO"])
def test_merma_con_motivo_y_lote(puertos, motivo):
    caso = RegistrarMerma(puertos.stock, puertos.lotes, puertos.mov)
    assert caso.ejecutar("p1", 2, motivo, "u1", lote_id="l1") == 8
    assert puertos.mov.guardar.call_args.args[0].referencia == f"MERMA:{motivo}"


@pytest.mark.parametrize("fallo", ["motivo", "sin_stock", "sin_lote", "otro_producto", "exceso_lote", "sin_cobertura"])
def test_merma_invalida_no_persiste(puertos, fallo):
    motivo, lote_id = "ROBO", "l1"
    if fallo == "motivo":
        motivo = "INVALIDO"
    elif fallo == "sin_stock":
        puertos.stock.obtener.return_value = None
    elif fallo == "sin_lote":
        puertos.lotes.buscar_por_id.return_value = None
    elif fallo == "otro_producto":
        puertos.lotes.buscar_por_id.return_value = lote(producto="p2")
    elif fallo == "exceso_lote":
        puertos.lotes.buscar_por_id.return_value = lote(1)
    else:
        lote_id = None
        puertos.lotes.listar_por_producto.return_value = [lote(1)]
    with pytest.raises((ValidationException, LoteNoEncontrado)):
        RegistrarMerma(puertos.stock, puertos.lotes, puertos.mov).ejecutar("p1", 2, motivo, "u1", lote_id=lote_id)
    puertos.stock.guardar.assert_not_called()
    puertos.lotes.guardar.assert_not_called()
    puertos.mov.guardar.assert_not_called()


def test_merma_sin_lote_incluye_vencidos(puertos):
    puertos.lotes.listar_por_producto.return_value = [lote(2, -1), lote(8, 10)]
    assert RegistrarMerma(puertos.stock, puertos.lotes, puertos.mov).ejecutar("p1", 3, "VENCIDO", "u1") == 7
    assert puertos.lotes.guardar.call_count == 2


@pytest.mark.parametrize("cantidad,tipo", [(2, TipoMovimiento.AJUSTE_POSITIVO), (-2, TipoMovimiento.AJUSTE_NEGATIVO)])
def test_ajustar_stock_guarda_diferencia_absoluta(puertos, cantidad, tipo):
    assert AjustarStock(puertos.stock, puertos.mov).ejecutar(AjusteStockDTO("p1", cantidad, "u1")) == 10 + cantidad
    movimiento = puertos.mov.guardar.call_args.args[0]
    assert movimiento.tipo == tipo and movimiento.cantidad == 2


def test_ajuste_cero_rechazado(puertos):
    with pytest.raises(ValidationException):
        AjustarStock(puertos.stock, puertos.mov).ejecutar(AjusteStockDTO("p1", 0, "u1"))


def test_reservar_y_liberar(puertos):
    reserva_id = ReservarStock(puertos.stock, puertos.reservas).ejecutar("p1", 2, "P:1")
    assert reserva_id and puertos.stock.obtener.return_value.reservada == 2
    LiberarReserva(puertos.stock, puertos.reservas).ejecutar(reserva_id)
    assert puertos.stock.obtener.return_value.reservada == 0


@pytest.mark.parametrize("operacion", ["reservar", "liberar", "confirmar"])
def test_reservas_ausentes_rechazadas(puertos, operacion):
    puertos.stock.obtener.return_value = None
    puertos.reservas.buscar_por_id.return_value = None
    with pytest.raises((ReservaNoEncontrada, StockInsuficiente)):
        if operacion == "reservar":
            ReservarStock(puertos.stock, puertos.reservas).ejecutar("p1", 1, "P:1")
        elif operacion == "liberar":
            LiberarReserva(puertos.stock, puertos.reservas).ejecutar("r1")
        else:
            ConfirmarSalidaReservada(puertos.stock, puertos.reservas, puertos.mov).ejecutar("r1")


def test_liberar_confirmada_rechaza_y_expiradas_se_procesan(puertos):
    puertos.reservas.buscar_por_id.return_value.confirmar()
    with pytest.raises(ReservaYaConfirmada):
        LiberarReserva(puertos.stock, puertos.reservas).ejecutar("r1")
    r = ReservaStock(producto_id="p1", cantidad=1)
    puertos.reservas.buscar_por_id.return_value = r
    puertos.reservas.listar_activas_expiradas.return_value = [r]
    puertos.stock.obtener.return_value.reservada = 1
    assert LiberarReserva(puertos.stock, puertos.reservas).liberar_expiradas() == 1


def test_confirmar_reserva_descuenta_lotes(puertos):
    puertos.stock.obtener.return_value.reservada = 2
    caso = ConfirmarSalidaReservada(puertos.stock, puertos.reservas, puertos.mov, lote_repo=puertos.lotes)
    assert caso.ejecutar("r1", "PEDIDO:1") == 8
    assert puertos.lotes.guardar.call_args.args[0].cantidad_restante == 8


def test_alertas_usan_minimo_individual_y_notificador(puertos):
    notificador = Mock()
    puertos.stock.productos_bajo_minimo.return_value = [{"producto_id": "p1", "disponible": 3, "stock_minimo": 8}]
    assert AlertarStockMinimo(puertos.stock, notificador).ejecutar() == 1
    notificador.notificar_stock_minimo.assert_called_once_with("p1", 3, 8)
    puertos.lotes.lotes_por_vencer.return_value = [lote(dias=0)]
    assert AlertarVencimientos(puertos.lotes, notificador).ejecutar() == 1
    assert notificador.notificar_vencimiento.call_args.args[2] == 0


def test_consultas_stock_lotes_y_kardex(puertos):
    assert ConsultarStock(puertos.stock).ejecutar("p1").disponible == 10
    puertos.stock.obtener.return_value = None
    assert ConsultarStock(puertos.stock).ejecutar("p1").bajo_minimo
    puertos.lotes.lotes_vencidos.return_value = [lote(dias=-1)]
    assert len(ConsultarLotes(puertos.lotes).ejecutar("p1")) == 1
    assert ConsultarLotes(puertos.lotes).ejecutar_vencidos()[0].vencido
    puertos.mov.kardex.return_value = [MovimientoStock(producto_id="p1", cantidad=1, stock_resultante=1)]
    puertos.mov.contar_kardex.return_value = 1
    assert ConsultarKardex(puertos.mov).ejecutar("p1", "2026-10-01", "2026-10-16").total == 1


@pytest.mark.parametrize("kwargs", [{"pagina": 0}, {"por_pagina": 0}, {"desde": "x"},
                                   {"desde": "2026-10-16", "hasta": "2026-10-01"}])
def test_kardex_valida_filtros(puertos, kwargs):
    with pytest.raises(ValueError):
        ConsultarKardex(puertos.mov).ejecutar("p1", **kwargs)
```

# 5. NIVEL 2: PRUEBAS DE INTEGRACIÓN (INTEGRATION TESTING)

## 5.1 Qué se evalúa en este módulo

Los 48 casos verifican RF-016..024 y reservas con ORM y vistas reales: campos,
permisos, entradas invalidas, pago parcial/total, rollback de varias lineas,
notificacion solo tras commit, fechas limite, stock/lotes, kardex paginado,
anulaciones, reservas, baja rotacion y margen. Cinco casos de concurrencia prueban
salidas, reservas, liberacion y confirmacion repetidas y primeras recepciones.
En salidas y reservas, dos peticiones de cuatro unidades compiten por cinco:
exactamente una debe ganar.
SQLite puede comprobar persistencia y rollback, pero no SELECT FOR UPDATE.

## 5.2 Aplicativos y Librerías a usar

Docker Engine y Testcontainers crean un MySQL desechable. Django usa el driver
mysqlclient; PyMySQL/SQLAlchemy pertenecen al arranque de Testcontainers. Se parsea
su URL sin imprimir credenciales y se pasan los parametros a un subprocess pytest.
El contexto de Testcontainers detiene el contenedor al terminar.
Referencia del contrato de [MySqlContainer](https://testcontainers-python.readthedocs.io/en/latest/modules/mysql/README.html).

## 5.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
docker info
& $qaPython -m pip install -r requirements/qa-inventory-mysql.txt
& $qaPython scripts/qa_inventory_mysql.py
```

El wrapper usa `--reuse-db` solo dentro de ese contenedor nuevo y el nombre de su
BD, ya creada para el usuario de pruebas. No apunta a la base de desarrollo ni a
produccion. `testing_mysql` exige el indicador de entorno que configura el wrapper.
Si falta Docker o sus dependencias, el wrapper termina con error: no es un pase.

Para comprobar solamente los 48 casos RF/reservas en SQLite:

```powershell
& $qaPython -m pytest tests/integration/test_inventario_requisitos.py -q
```

**Estado observado:** 53 casos de integracion aprobados en MySQL 8.4.3/InnoDB
nativo efimero, incluidos los cinco casos de concurrencia. La suite completa
aprobo 300 pruebas sin omisiones; ver 5.5. La ruta Docker/Testcontainers no se
ejecuto localmente. SQLite omite los cinco casos exclusivos de MySQL; para ejecutar
todo se debe usar uno de los runners de MySQL.

## 5.4 Código Completo del Test de Integración

Archivo: `tests/integration/test_inventario_requisitos.py`

```python
"""Aceptacion RF-016..RF-024 con vistas, repositorios y transacciones reales."""
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core import mail
from django.db import transaction
from django.utils import timezone

from src.modules.catalog.infrastructure.persistence.django_models.categoria_model import CategoriaModel
from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
from src.modules.catalog.infrastructure.factories import construir_producto_repository
from src.modules.inventory.application.dto.lote_dto import RecepcionLoteDTO
from src.modules.inventory.application.use_cases.consultar_kardex import ConsultarKardex
from src.modules.inventory.application.use_cases.consultar_stock import ConsultarStock
from src.modules.inventory.application.use_cases.recibir_mercaderia import RecibirMercaderia
from src.modules.inventory.infrastructure.factories import (
    construir_lote_repository, construir_movimiento_repository, construir_stock_repository,
)
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import LoteModel
from src.modules.inventory.infrastructure.persistence.django_models.movimiento_model import MovimientoModel
from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente
from src.modules.reporting.application.use_cases.reporte_baja_rotacion import ReporteBajaRotacion
from src.modules.reporting.infrastructure.factories import construir_reporte_repository
from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoModificable
from src.modules.sales.infrastructure.factories import (
    construir_auditoria_port, construir_inventario_port, construir_venta_repository,
)
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def test_reserva_orm_aware_y_liberacion_idempotente():
    from src.modules.inventory.application.use_cases.liberar_reserva import LiberarReserva
    from src.modules.inventory.domain.entities.reserva_stock import ReservaStock
    from src.modules.inventory.infrastructure.persistence.repositories.django_reserva_repository import DjangoReservaRepository

    p = producto()
    ExistenciaModel.objects.create(id=uuid.uuid4(), producto_id=p.id, cantidad=10, reservada=5)
    reservas = DjangoReservaRepository()
    primera = reservas.guardar(ReservaStock(producto_id=str(p.id), cantidad=3))
    segunda = reservas.guardar(ReservaStock(producto_id=str(p.id), cantidad=2))
    cargada = reservas.buscar_por_id(primera.id)
    assert timezone.is_aware(cargada.expira_en)
    assert cargada.activa
    cargada.extender(30)
    reservas.guardar(cargada)
    liberar = LiberarReserva(construir_stock_repository(), reservas, uow=transaction.atomic())
    liberar.ejecutar(str(primera.id))
    liberar.ejecutar(str(primera.id))
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 2
    assert reservas.buscar_por_id(segunda.id).activa
    assert reservas.listar_activas_expiradas() == []
    vencida = reservas.buscar_por_id(segunda.id)
    vencida.expira_en = timezone.now() - timedelta(seconds=1)
    reservas.guardar(vencida)
    assert [r.id for r in reservas.listar_activas_expiradas()] == [segunda.id]
    assert liberar.liberar_expiradas() == 1
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 0
    assert liberar.liberar_expiradas() == 0


@pytest.fixture
def almacen(client, django_user_model):
    user = django_user_model.objects.create_user(username="almacen_inventario", password="test")
    client.force_login(user)
    session = client.session
    session["rol"] = "ALMACENERO"
    session["usuario_id"] = str(uuid.uuid4())
    session.save()
    return client


def producto(**kwargs):
    datos = dict(id=uuid.uuid4(), nombre="Producto inventario", codigo_barras=f"{uuid.uuid4().int % 10**13:013d}",
                 costo=Decimal("5"), precio_venta=Decimal("10"), estado="ACTIVO", stock_minimo=5)
    datos.update(kwargs)
    return ProductoModel.objects.create(**datos)


def recibir(p, cantidad=10, dias=20):
    return RecibirMercaderia(
        construir_stock_repository(), construir_lote_repository(), construir_movimiento_repository(),
        uow=transaction.atomic(),
    ).ejecutar(RecepcionLoteDTO(producto_id=str(p.id), numero_lote=f"L-{uuid.uuid4().hex[:8]}",
                              cantidad=cantidad, costo_unitario=Decimal("5"),
                              fecha_vencimiento=date.today() + timedelta(days=dias)))


def venta_guardada(*productos, cantidad=2):
    agregado = VentaAggregate(venta=Venta(numero_ticket=f"INV-{uuid.uuid4().hex[:12]}", cajero_id=str(uuid.uuid4())))
    for p in productos:
        agregado.agregar_producto(str(p.id), p.nombre, cantidad, Monto(p.precio_venta))
    agregado.calcular_totales()
    construir_venta_repository().guardar(agregado)
    return agregado


def cobrar(venta, monto):
    return ProcesarPago(construir_venta_repository(), construir_inventario_port(), construir_auditoria_port(),
                        uow=transaction.atomic()).ejecutar(
        ProcesarPagoDTO(venta_id=str(venta.venta.id), metodo="EFECTIVO", monto=monto))


def datos_producto(categoria, **kwargs):
    datos = {"nombre": "Leche", "codigo_barras": "7751234567890", "costo": "5", "precio_venta": "8",
             "categoria_id": str(categoria.id), "stock_minimo": "8",
             "fecha_vencimiento": (date.today() + timedelta(days=20)).isoformat()}
    datos.update(kwargs)
    return datos


def test_rf016_almacenero_crea_y_edita_todos_los_campos(almacen):
    categoria = CategoriaModel.objects.create(id=uuid.uuid4(), nombre="Lacteos", slug="lacteos")
    datos = datos_producto(categoria)
    respuesta = almacen.post("/catalogo/productos/nuevo/", datos)
    assert respuesta.status_code == 302
    p = ProductoModel.objects.get(codigo_barras=datos["codigo_barras"])
    entidad = construir_producto_repository().buscar_por_id(str(p.id))
    assert entidad.categoria_id == str(categoria.id)
    assert entidad.stock_minimo == 8
    assert entidad.fecha_vencimiento == date.fromisoformat(datos["fecha_vencimiento"])
    form = almacen.get(f"/catalogo/productos/{p.id}/editar/").context["form"]
    assert form.initial["nombre"] == "Leche"
    assert form.initial["stock_minimo"] == 8
    datos.update(nombre="Leche entera", stock_minimo="3", fecha_vencimiento="", codigo_barras="7751234567891")
    assert almacen.post(f"/catalogo/productos/{p.id}/editar/", datos).status_code == 302
    p.refresh_from_db()
    assert (p.nombre, p.stock_minimo, p.fecha_vencimiento, p.codigo_barras) == ("Leche entera", 3, None, "7751234567891")


@pytest.mark.parametrize("campo,valor", [("stock_minimo", "-1"), ("categoria_id", ""), ("codigo_barras", "abc"),
                                         ("precio_venta", "5.01"), ("fecha_vencimiento", "2026-02-30")])
def test_rf016_datos_invalidos_no_crean_producto(almacen, campo, valor):
    categoria = CategoriaModel.objects.create(id=uuid.uuid4(), nombre="Categoria", slug="categoria")
    respuesta = almacen.post("/catalogo/productos/nuevo/", datos_producto(categoria, **{campo: valor}))
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    assert not ProductoModel.objects.exists()


def test_rf016_codigo_duplicado_no_deja_actualizacion_parcial(almacen):
    categoria = CategoriaModel.objects.create(id=uuid.uuid4(), nombre="Categoria", slug="categoria")
    primero, segundo = producto(categoria=categoria), producto(categoria=categoria, nombre="Original")
    respuesta = almacen.post(f"/catalogo/productos/{segundo.id}/editar/",
                             datos_producto(categoria, nombre="No guardar", codigo_barras=primero.codigo_barras))
    assert respuesta.context["form"].non_field_errors()
    segundo.refresh_from_db()
    assert segundo.nombre == "Original"


def test_rf017_cobro_parcial_total_y_reintento(almacen):
    p = producto()
    recibir(p)
    venta = venta_guardada(p)
    assert cobrar(venta, 5)["estado"] == "PENDIENTE"
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 10
    assert cobrar(venta, 15)["estado"] == "PAGADA"
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 8
    assert LoteModel.objects.get(producto_id=p.id).cantidad_restante == 8
    salida = MovimientoModel.objects.get(producto_id=p.id, tipo="SALIDA_VENTA")
    assert salida.cantidad == 2 and salida.stock_resultante == 8
    assert str(salida.usuario_id) == venta.venta.cajero_id
    with pytest.raises(VentaNoModificable):
        cobrar(venta, 20)
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 8


def test_rf017_segunda_linea_sin_stock_revierte_venta_lotes_y_kardex(django_capture_on_commit_callbacks):
    p, otro = producto(), producto()
    recibir(p, cantidad=6)
    recibir(otro, cantidad=1)
    venta = venta_guardada(p, otro)
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        with pytest.raises(StockInsuficiente):
            cobrar(venta, 40)
    assert callbacks == []
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 6
    assert LoteModel.objects.get(producto_id=p.id).cantidad_restante == 6
    assert not MovimientoModel.objects.filter(tipo="SALIDA_VENTA").exists()
    recuperada = construir_venta_repository().buscar_por_id(str(venta.venta.id))
    assert recuperada.venta.es_borrador and not recuperada.pagos


def test_rf017_consultas_stock_sin_cache_obsoleta_ni_cruce_entre_productos():
    p, otro = producto(), producto()
    recibir(p, 10)
    recibir(otro, 20)
    consulta = ConsultarStock(construir_stock_repository())
    assert consulta.ejecutar(str(p.id)).disponible == 10
    assert consulta.ejecutar(str(otro.id)).disponible == 20
    construir_inventario_port().descontar(str(p.id), 2, "VENTA:consulta")
    assert consulta.ejecutar(str(p.id)).disponible == 8
    assert consulta.ejecutar(str(otro.id)).disponible == 20


def test_rf017_peps_omite_vencidos_y_salida_conserva_trazabilidad():
    p = producto()
    vencido, cercano, lejano = recibir(p, 5, -1), recibir(p, 2, 3), recibir(p, 8, 90)
    construir_inventario_port().descontar(str(p.id), 4, "VENTA:PEPS")
    assert LoteModel.objects.get(pk=vencido.id).cantidad_restante == 5
    assert LoteModel.objects.get(pk=cercano.id).cantidad_restante == 0
    assert LoteModel.objects.get(pk=lejano.id).cantidad_restante == 6
    salidas = list(MovimientoModel.objects.filter(tipo="SALIDA_VENTA").order_by("fecha"))
    assert [s.cantidad for s in salidas] == [2, 2]
    assert [s.stock_resultante for s in salidas] == [13, 11]
    assert {str(s.lote_id) for s in salidas} == {cercano.id, lejano.id}


def test_rf017_stock_solo_vencido_no_se_vende():
    p = producto()
    recibir(p, 5, -1)
    with pytest.raises(StockInsuficiente):
        construir_inventario_port().descontar(str(p.id), 2, "VENTA:vencido")
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 5
    assert not MovimientoModel.objects.filter(tipo="SALIDA_VENTA").exists()


def test_anular_venta_repone_lotes_y_permite_otra_venta():
    from src.modules.sales.application.use_cases.anular_venta import AnularVenta
    p = producto()
    lote = recibir(p, 2)
    venta = venta_guardada(p)
    cobrar(venta, 20)
    AnularVenta(construir_venta_repository(), construir_inventario_port(), construir_auditoria_port(),
                uow=transaction.atomic()).ejecutar(str(venta.venta.id), "Error", venta.venta.cajero_id)
    assert LoteModel.objects.get(pk=lote.id).cantidad_restante == 2
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 2
    assert cobrar(venta_guardada(p), 20)["estado"] == "PAGADA"


def test_salida_reservada_descuenta_lotes_y_no_se_confirma_dos_veces():
    from src.modules.orders.infrastructure.adapters.inventario_adapter import InventarioAdapter
    from src.modules.inventory.domain.exceptions.stock_exceptions import ReservaYaConfirmada
    p = producto()
    lote = recibir(p, 10)
    adapter = InventarioAdapter()
    reserva_id = adapter.reservar(str(p.id), 3, "PEDIDO:inventario")
    assert adapter.confirmar_reserva(reserva_id, "PEDIDO:inventario") == 7
    existencia = ExistenciaModel.objects.get(producto_id=p.id)
    assert existencia.reservada == 0 and existencia.cantidad == 7
    assert LoteModel.objects.get(pk=lote.id).cantidad_restante == 7
    with pytest.raises(ReservaYaConfirmada):
        adapter.confirmar_reserva(reserva_id, "PEDIDO:inventario")
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 7


def test_rf018_igualdad_no_alerta_cruce_notifica_tras_commit(django_capture_on_commit_callbacks):
    p = producto(stock_minimo=5)
    recibir(p, 6)
    with django_capture_on_commit_callbacks(execute=True):
        construir_inventario_port().descontar(str(p.id), 1, "VENTA:igual")
    assert not mail.outbox
    assert not construir_stock_repository().productos_bajo_minimo()
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        construir_inventario_port().descontar(str(p.id), 1, "VENTA:cruce")
        assert not mail.outbox
    assert len(callbacks) == 1 and len(mail.outbox) == 1
    assert str(p.id) in mail.outbox[0].body
    with django_capture_on_commit_callbacks(execute=True):
        construir_inventario_port().descontar(str(p.id), 1, "VENTA:ya-bajo")
    assert len(mail.outbox) == 1


def test_rf018_minimo_individual_incluye_productos_sin_existencia(almacen):
    alto, bajo, cero = producto(stock_minimo=12), producto(stock_minimo=1), producto(stock_minimo=0)
    recibir(alto, 10)
    recibir(bajo, 10)
    faltante = producto(nombre="Sin recepcion", stock_minimo=3)
    ids = {f["producto_id"] for f in construir_stock_repository().productos_bajo_minimo()}
    assert ids == {str(alto.id), str(faltante.id)}
    respuesta = almacen.get("/inventario/")
    assert len(respuesta.context["existencias"]) == 4
    assert b"Sin recepcion" in respuesta.content
    assert not ConsultarStock(construir_stock_repository()).ejecutar(str(cero.id)).bajo_minimo


def test_rf019_limites_vencimiento_y_lotes_agotados(almacen):
    p = producto()
    esperados = set()
    for dias in (-1, 0, 30, 31):
        lote = recibir(p, dias=dias)
        if dias in (0, 30):
            esperados.add(lote.numero_lote)
    agotado = recibir(p, dias=10)
    LoteModel.objects.filter(pk=agotado.id).update(cantidad_restante=0)
    respuesta = almacen.get("/inventario/alertas/")
    assert {l.numero_lote for l in respuesta.context["por_vencer"]} == esperados
    assert len(respuesta.context["vencidos"]) == 1
    assert p.nombre.encode() in respuesta.content


def test_rf019_vencimiento_del_producto_sin_lote(almacen):
    p = producto(fecha_vencimiento=date.today() + timedelta(days=30))
    respuesta = almacen.get("/inventario/alertas/")
    assert respuesta.context["por_vencer"][0]["producto_nombre"] == p.nombre


def test_rf020_recepcion_http_guarda_fecha_lote_stock_y_entrada(almacen):
    p = producto()
    datos = dict(producto_id=str(p.id), numero_lote="LOTE-HTTP", cantidad=15, costo_unitario="5",
                 fecha_vencimiento=(date.today() + timedelta(days=25)).isoformat())
    respuesta = almacen.post("/inventario/recepcion/", datos)
    assert respuesta.status_code == 302
    lote = LoteModel.objects.get(numero_lote="LOTE-HTTP")
    assert lote.fecha_vencimiento == date.fromisoformat(datos["fecha_vencimiento"])
    assert lote.cantidad_restante == ExistenciaModel.objects.get(producto_id=p.id).cantidad == 15
    movimiento = MovimientoModel.objects.get(producto_id=p.id)
    assert movimiento.tipo == "ENTRADA" and movimiento.lote_id == lote.id


@pytest.mark.parametrize("campo,valor", [("cantidad", 0), ("cantidad", -1), ("producto_id", "inexistente"),
                                         ("fecha_vencimiento", "invalida")])
def test_rf020_recepcion_invalida_no_persiste(almacen, campo, valor):
    p = producto()
    datos = dict(producto_id=str(p.id), numero_lote="L", cantidad=2, costo_unitario="5")
    datos[campo] = valor
    respuesta = almacen.post("/inventario/recepcion/", datos)
    assert respuesta.context["form"].errors
    assert not LoteModel.objects.exists() and not ExistenciaModel.objects.exists()


@pytest.mark.parametrize("motivo", ["VENCIDO", "DANADO", "ROBO"])
def test_rf021_merma_descuenta_lote_y_registra_motivo(almacen, motivo):
    p = producto()
    lote = recibir(p, dias=-1 if motivo == "VENCIDO" else 10)
    respuesta = almacen.post("/inventario/mermas/", dict(producto_id=p.id, lote_id=lote.id, cantidad=3, motivo=motivo))
    assert respuesta.status_code == 302
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 7
    assert LoteModel.objects.get(pk=lote.id).cantidad_restante == 7
    movimiento = MovimientoModel.objects.get(tipo="MERMA")
    assert movimiento.referencia == f"MERMA:{motivo}" and movimiento.lote_id == uuid.UUID(lote.id)


def test_rf021_merma_sin_lote_distribuye_entre_lotes_incluidos_vencidos(almacen):
    p = producto()
    vencido, vigente = recibir(p, 2, -1), recibir(p, 5, 10)
    assert almacen.post("/inventario/mermas/", dict(producto_id=p.id, cantidad=4, motivo="DANADO")).status_code == 302
    assert LoteModel.objects.get(pk=vencido.id).cantidad_restante == 0
    assert LoteModel.objects.get(pk=vigente.id).cantidad_restante == 3
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 3


@pytest.mark.parametrize("fallo", ["otro_lote", "exceso", "motivo", "cantidad"])
def test_rf021_merma_invalida_no_modifica_stock_ni_lotes(almacen, fallo):
    p, otro = producto(), producto()
    lote, otro_lote = recibir(p), recibir(otro)
    datos = dict(producto_id=p.id, lote_id=lote.id, cantidad=2, motivo="ROBO")
    if fallo == "otro_lote":
        datos["lote_id"] = otro_lote.id
    elif fallo == "exceso":
        datos["cantidad"] = 100
    elif fallo == "motivo":
        datos["motivo"] = "INVALIDO"
    else:
        datos["cantidad"] = 0
    respuesta = almacen.post("/inventario/mermas/", datos)
    assert respuesta.status_code == 200 and respuesta.context["form"].errors
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 10
    assert LoteModel.objects.get(pk=lote.id).cantidad_restante == 10
    assert not MovimientoModel.objects.filter(tipo="MERMA").exists()


def test_rf022_historial_paginado_completo_y_filtros(almacen):
    p = producto()
    for _ in range(52):
        recibir(p, 1)
    consulta = ConsultarKardex(construir_movimiento_repository())
    pagina = consulta.ejecutar(str(p.id))
    assert pagina.total == 52 and len(pagina.items) == 50 and pagina.tiene_siguiente
    assert len(consulta.ejecutar(str(p.id), pagina=2).items) == 2
    respuesta = almacen.get("/inventario/kardex/", {"producto_id": str(p.id), "pagina": 2,
                                                  "desde": date.today().isoformat()})
    assert respuesta.status_code == 200
    assert respuesta.context["pagina_dto"].total == 52
    assert str(p.id).encode() in respuesta.content
    assert b"desde=" in respuesta.content


@pytest.mark.parametrize("filtro", [{"pagina": "abc"}, {"pagina": "0"}, {"desde": "no-fecha"},
                                    {"desde": "2026-10-10", "hasta": "2026-01-01"}, {"producto_id": "abc"}])
def test_rf022_filtros_invalidos_muestran_error(almacen, filtro):
    p = producto()
    respuesta = almacen.get("/inventario/kardex/", {"producto_id": str(p.id), **filtro})
    assert respuesta.status_code == 200 and respuesta.context["form"].errors


def test_rf023_solo_ventas_pagadas_ventana_60_dias():
    recientes, limite, antigua, anulada, borrador, nunca = [producto() for _ in range(6)]
    for p, dias, estado in [(recientes, 59, "PAGADA"), (limite, 60, "PAGADA"),
                            (antigua, 61, "PAGADA"), (anulada, 1, "ANULADA"), (borrador, 1, "BORRADOR")]:
        venta = venta_guardada(p)
        VentaModel.objects.filter(pk=venta.venta.id).update(estado=estado, fecha_creacion=timezone.now() - timedelta(days=dias))
    ids = {f["producto_id"] for f in ReporteBajaRotacion(construir_reporte_repository()).ejecutar()}
    assert ids == {str(p.id) for p in (antigua, anulada, borrador, nunca)}


def test_rf024_orden_por_margen_y_no_por_ingresos(almacen):
    producto(nombre="Bajo margen", costo=Decimal("100"), precio_venta=Decimal("120"))
    producto(nombre="Alto margen", costo=Decimal("2"), precio_venta=Decimal("8"))
    producto(nombre="Costo cero", costo=Decimal("0"), precio_venta=Decimal("5"))
    producto(nombre="Inactivo", activo=False)
    respuesta = almacen.get("/reportes/inventario/")
    filas = respuesta.context["mayor_ganancia"]
    assert [f["producto_nombre"] for f in filas] == ["Alto margen", "Costo cero", "Bajo margen"]
    assert filas[0]["margen_pct"] == Decimal("300.00")
    assert filas[0]["ganancia_unitaria"] == Decimal("6")


def test_ranking_existente_del_dashboard_sigue_funcionando(almacen):
    sesion = almacen.session
    sesion["rol"] = "ADMINISTRADOR"
    sesion.save()
    assert almacen.get("/reportes/").status_code == 200


@pytest.mark.parametrize("ruta", ["/inventario/", "/inventario/recepcion/", "/inventario/mermas/",
                                  "/inventario/kardex/", "/inventario/alertas/", "/reportes/inventario/",
                                  "/catalogo/productos/nuevo/"])
def test_sin_permiso_no_se_accede_al_modulo(almacen, ruta):
    session = almacen.session
    session["rol"] = "CLIENTE"
    session.save()
    assert almacen.get(ruta).status_code == 302
    almacen.logout()
    assert almacen.get(ruta).status_code == 302
```

Archivo: `tests/integration/test_inventario_mysql.py`

```python
"""InnoDB real: dos escritores compiten por las mismas cinco unidades."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier
from uuid import uuid4

import pytest
from django.db import close_old_connections, connection, connections, transaction

from src.modules.catalog.models import ProductoModel
from src.modules.inventory.models import ExistenciaModel, LoteModel, MovimientoModel
from src.modules.inventory.domain.exceptions.stock_exceptions import StockInsuficiente
from src.modules.sales.infrastructure.adapters.inventario_adapter import InventarioAdapter

pytestmark = [
    pytest.mark.integration, pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(connection.vendor != "mysql", reason="Requiere InnoDB: ejecutar scripts/qa_inventory_mysql.py"),
]


@pytest.mark.parametrize("operacion", ["descontar", "reservar"])
def test_dos_escritores_no_pueden_consumir_el_mismo_stock(operacion):
    p = ProductoModel.objects.create(id=uuid4(), nombre="Concurrencia", codigo_barras="7751234567801",
                                    costo=Decimal("5"), precio_venta=Decimal("10"), estado="ACTIVO")
    ExistenciaModel.objects.create(id=uuid4(), producto_id=p.id, cantidad=5)
    LoteModel.objects.create(id=uuid4(), producto_id=p.id, numero_lote="L-CONC", cantidad_inicial=5,
                            cantidad_restante=5, fecha_recepcion=date.today())
    barrera = Barrier(2, timeout=10)

    def intentar():
        close_old_connections()
        try:
            barrera.wait()
            getattr(InventarioAdapter(), operacion)(str(p.id), 4, f"QA:{uuid4().hex[:8]}")
            return "aceptado"
        except StockInsuficiente:
            return "rechazado"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(intentar) for _ in range(2)]
        resultados = [f.result(timeout=25) for f in futuros]
    assert sorted(resultados) == ["aceptado", "rechazado"]
    existencia = ExistenciaModel.objects.get(producto_id=p.id)
    assert existencia.cantidad - existencia.reservada == 1
    assert 0 <= existencia.reservada <= existencia.cantidad
    if operacion == "descontar":
        assert existencia.cantidad == 1
        assert LoteModel.objects.get(producto_id=p.id).cantidad_restante == 1
        assert MovimientoModel.objects.filter(producto_id=p.id, tipo="SALIDA_VENTA").count() == 1
    else:
        assert existencia.cantidad == 5 and existencia.reservada == 4


@pytest.mark.parametrize("operacion", ["liberar", "confirmar"])
def test_dos_operaciones_sobre_la_misma_reserva_no_afectan_otro_pedido(operacion):
    from src.modules.inventory.application.use_cases.liberar_reserva import LiberarReserva
    from src.modules.inventory.domain.exceptions.stock_exceptions import ReservaYaConfirmada
    from src.modules.inventory.infrastructure.factories import construir_reserva_repository, construir_stock_repository

    p = ProductoModel.objects.create(id=uuid4(), nombre="Reserva simultanea", codigo_barras="7751234567810",
                                    costo=5, precio_venta=10, estado="ACTIVO", stock_minimo=0)
    ExistenciaModel.objects.create(id=uuid4(), producto_id=p.id, cantidad=10)
    LoteModel.objects.create(id=uuid4(), producto_id=p.id, numero_lote="L-RES", cantidad_inicial=10,
                            cantidad_restante=10, fecha_recepcion=date.today())
    adapter = InventarioAdapter()
    primera = adapter.reservar(str(p.id), 3, "pedido-1")
    segunda = adapter.reservar(str(p.id), 2, "pedido-2")
    barrera = Barrier(2, timeout=10)

    def intentar():
        close_old_connections()
        try:
            barrera.wait()
            if operacion == "liberar":
                LiberarReserva(construir_stock_repository(), construir_reserva_repository(),
                               uow=transaction.atomic()).ejecutar(primera)
            else:
                InventarioAdapter().confirmar_reserva(primera, "pedido-1")
            return "aceptado"
        except ReservaYaConfirmada:
            return "rechazado"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(intentar) for _ in range(2)]
        resultados = sorted(f.result(timeout=25) for f in futuros)
    assert resultados == (["aceptado", "aceptado"] if operacion == "liberar" else ["aceptado", "rechazado"])
    existencia = ExistenciaModel.objects.get(producto_id=p.id)
    assert existencia.reservada == 2
    assert construir_reserva_repository().buscar_por_id(segunda).activa
    cantidad = 10 if operacion == "liberar" else 7
    assert existencia.cantidad == cantidad
    assert LoteModel.objects.get(producto_id=p.id).cantidad_restante == cantidad
    assert MovimientoModel.objects.filter(producto_id=p.id, tipo="SALIDA_PEDIDO").count() == int(operacion == "confirmar")
    assert MovimientoModel.objects.filter(producto_id=p.id).count() == int(operacion == "confirmar")


def test_dos_primeras_recepciones_concurrentes_acumulan_stock():
    from src.modules.inventory.application.dto.lote_dto import RecepcionLoteDTO
    from src.modules.inventory.application.use_cases.recibir_mercaderia import RecibirMercaderia
    from src.modules.inventory.infrastructure.factories import (
        construir_lote_repository, construir_movimiento_repository, construir_stock_repository,
    )

    p = ProductoModel.objects.create(id=uuid4(), nombre="Primeras recepciones", codigo_barras="7751234567811",
                                    costo=5, precio_venta=10, estado="ACTIVO", stock_minimo=0)
    barrera = Barrier(2, timeout=10)

    def recibir(cantidad):
        close_old_connections()
        try:
            barrera.wait()
            RecibirMercaderia(construir_stock_repository(), construir_lote_repository(),
                construir_movimiento_repository(), uow=transaction.atomic()).ejecutar(
                    RecepcionLoteDTO(producto_id=str(p.id), numero_lote=f"L-{cantidad}",
                                     cantidad=cantidad, costo_unitario=Decimal("5")))
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(recibir, cantidad) for cantidad in (3, 4)]
        for futuro in futuros:
            futuro.result(timeout=25)
    assert ExistenciaModel.objects.filter(producto_id=p.id).count() == 1
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 7
    assert sum(LoteModel.objects.filter(producto_id=p.id).values_list("cantidad_restante", flat=True)) == 7
    assert MovimientoModel.objects.filter(producto_id=p.id).count() == 2
```

Archivo: `scripts/qa_inventory_mysql.py`

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

Archivo: `config/settings/testing_mysql.py`

```python
"""Solo para el contenedor desechable creado por scripts/qa_inventory_mysql.py."""
import os

from django.core.exceptions import ImproperlyConfigured

from .testing import *  # noqa: F401,F403

if os.environ.get("INVENTORY_EPHEMERAL_MYSQL") != "1":
    raise ImproperlyConfigured("Use scripts/qa_inventory_mysql.py para crear el MySQL aislado")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ["QA_MYSQL_DATABASE"],
        "USER": os.environ["QA_MYSQL_USER"],
        "PASSWORD": os.environ["QA_MYSQL_PASSWORD"],
        "HOST": os.environ["QA_MYSQL_HOST"],
        "PORT": os.environ["QA_MYSQL_PORT"],
        "CONN_MAX_AGE": 0,
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES', innodb_lock_wait_timeout=10",
        },
        "TEST": {"NAME": os.environ["QA_MYSQL_DATABASE"]},
    }
}
```

## 5.5 Alternativa ejecutada sin Docker: MySQL nativo efimero

Se uso el ZIP oficial de MySQL 8.4.3 para Windows, con firma Authenticode valida.
El runner crea un datadir temporal, escucha solo en 127.0.0.1 en un puerto libre,
genera credenciales aleatorias, configura InnoDB y apaga y elimina la instancia al
terminar. No modifica servicios ni bases existentes. La carga de zonas horarias
es una fixture de UTC y America/Lima para las fechas actuales de esta suite;
no sustituye una base historica de zonas horarias productiva.

[Inicializacion oficial de MySQL](https://dev.mysql.com/doc/refman/8.4/en/data-directory-initialization.html)
y [opciones del servidor](https://dev.mysql.com/doc/refman/8.4/en/server-options.html).

```powershell
$qaMysql = Join-Path $env:TEMP 'qa-mysql-binaries/mysql-8.4.3-winx64'
.venv/Scripts/python.exe -m pip install -r requirements/qa-inventory-mysql.txt
.venv/Scripts/python.exe scripts/qa_inventory_mysql_native.py --basedir $qaMysql --full
```

`--basedir` debe apuntar al ZIP oficial ya extraido; las descargas no se realizan
automaticamente. Omitir `--full` ejecuta los 53 casos de integracion RF/reservas y
concurrencia. Con `--full` se ejecutaron los cuatro niveles: 300 aprobados, sin
omisiones ni xfail. Esta ejecucion demuestra MySQL real; no afirma haber usado
un contenedor Docker ni un runner de GitHub Actions.

Archivo: `scripts/qa_inventory_mysql_native.py`

```python
"""MySQL real desechable sin Docker; no utiliza servicios ni datos existentes.

Uso: python scripts/qa_inventory_mysql_native.py --basedir RUTA_MYSQL [--full]
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time

import pymysql


def cargar_zonas(cursor):
    # Las consultas de esta suite usan UTC y America/Lima en fechas actuales.
    # La instancia es desechable: no se instala una tabla historica productiva.
    for nombre, desplazamiento in (("UTC", 0), ("America/Lima", -18000)):
        cursor.execute("INSERT INTO mysql.time_zone (Use_leap_seconds) VALUES ('N')")
        identificador = cursor.lastrowid
        cursor.execute("INSERT INTO mysql.time_zone_name (Name, Time_zone_id) VALUES (%s, %s)",
                       (nombre, identificador))
        cursor.execute("INSERT INTO mysql.time_zone_transition_type "
                       "(Time_zone_id, Transition_type_id, `Offset`, Is_DST, Abbreviation) "
                       "VALUES (%s, 0, %s, 0, %s)", (identificador, desplazamiento, "UTC" if nombre == "UTC" else "-05"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--basedir", type=Path, required=True)
    parser.add_argument("--full", action="store_true", help="Ejecutar los cuatro niveles, no solo integracion")
    args = parser.parse_args()
    basedir = args.basedir.resolve()
    binary = basedir / "bin" / ("mysqld.exe" if os.name == "nt" else "mysqld")
    if not binary.is_file():
        parser.error("No se encontro bin/mysqld en --basedir")
    root = Path(__file__).resolve().parents[1]
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    database = "qa_inventory_" + secrets.token_hex(6)
    password = secrets.token_urlsafe(32)
    with socket.socket() as reservado:
        reservado.bind(("127.0.0.1", 0))
        port = reservado.getsockname()[1]
    temporary_root = Path(tempfile.gettempdir()).resolve()
    with tempfile.TemporaryDirectory(prefix="qa-inventory-mysql-", dir=temporary_root) as temporary:
        Path(temporary).resolve().relative_to(temporary_root)
        datadir = Path(temporary) / "data"
        common = [str(binary), "--no-defaults", f"--basedir={basedir}", f"--datadir={datadir}"]
        with (reports / "mysql-native-init.log").open("w", encoding="utf-8") as log:
            subprocess.run([*common, "--initialize-insecure", "--console"], stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=120)
        with (reports / "mysql-native-server.log").open("w", encoding="utf-8") as log:
            server = subprocess.Popen([*common, *(["--no-monitor"] if os.name == "nt" else []), "--console", "--bind-address=127.0.0.1",
                f"--port={port}", "--mysqlx=0", "--skip-log-bin", "--innodb-buffer-pool-size=64M",
                "--default-time-zone=+00:00"], stdout=log, stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            try:
                deadline = time.monotonic() + 90
                while True:
                    if server.poll() is not None:
                        raise RuntimeError("MySQL no pudo iniciar; consulte reports/mysql-native-server.log")
                    try:
                        db = pymysql.connect(host="127.0.0.1", port=port, user="root", password="",
                                             connect_timeout=2, autocommit=True)
                        break
                    except pymysql.OperationalError:
                        if time.monotonic() >= deadline:
                            raise TimeoutError("MySQL no estuvo disponible en 90 segundos")
                        time.sleep(0.25)
                with db:
                    with db.cursor() as cursor:
                        cursor.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s", (password,))
                        cursor.execute(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4")
                        cargar_zonas(cursor)
                        cursor.execute("SELECT VERSION(), @@default_storage_engine, "
                                       "CONVERT_TZ('2026-10-16 12:00:00', 'UTC', 'America/Lima')")
                        version, engine, converted = cursor.fetchone()
                        assert engine == "InnoDB" and str(converted) == "2026-10-16 07:00:00"
                env = dict(os.environ, DJANGO_SETTINGS_MODULE="config.settings.testing_mysql",
                    INVENTORY_EPHEMERAL_MYSQL="1", QA_MYSQL_DATABASE=database, QA_MYSQL_USER="root",
                    QA_MYSQL_PASSWORD=password, QA_MYSQL_HOST="127.0.0.1", QA_MYSQL_PORT=str(port),
                    QA_REQUIRE_BROWSER="1")
                targets = [] if args.full else ["tests/integration/test_inventario_requisitos.py",
                                              "tests/integration/test_inventario_mysql.py"]
                result = subprocess.run([sys.executable, "-m", "pytest", *targets, "--reuse-db",
                    "-q", "-p", "no:cacheprovider", "--junitxml=reports/inventory-mysql-native.xml"],
                    cwd=root, env=env)
                evidence = dict(engine=engine, version=version, ephemeral=True, container=False,
                                full=args.full, exit_code=result.returncode,
                                executed_at=datetime.now(timezone.utc).isoformat(),
                                timezone_fixture="UTC y America/Lima, fechas actuales")
                (reports / "inventory-mysql-native.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
                print(json.dumps(evidence))
                return result.returncode
            finally:
                try:
                    with pymysql.connect(host="127.0.0.1", port=port, user="root", password=password,
                                         connect_timeout=2, autocommit=True) as shutdown:
                        with shutdown.cursor() as cursor:
                            cursor.execute("SHUTDOWN")
                except pymysql.MySQLError:
                    server.terminate()
                try:
                    server.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
```

# 6. NIVEL 3: PRUEBAS DE SISTEMA (SYSTEM / E2E & PERFORMANCE)

## 6.1 Qué se evalúa en este módulo

Chromium: login real -> producto -> recepcion -> merma -> alertas -> kardex ->
reportes, ademas del cobro POS y ticket PDF. Se prueba CSRF con comprobacion activa,
escape HTML de nombre de producto y X-Frame-Options. La carga usa HTTP real sobre
inventario, alertas y reportes, valida status/contenido/destino y falla ante errores
o p95 superior a 2000 ms. No mide consumo de stock ni reemplaza la concurrencia
InnoDB. Tampoco es una auditoria de seguridad completa.

El ensayo local usa WSGI live_server y SQLite temporal, no nginx/gunicorn/MySQL
desplegados. Se autentican cuatro sesiones antes de medir veinte GET concurrentes.
El login masivo y el conjunto de 50.000 productos requieren perfiles separados.
Se usa IPv4 local explicito para no medir el fallback de resolucion de localhost.

## 6.2 Aplicativos y Librerías a usar

Playwright Python y Chromium. El script de carga usa solo la biblioteca estandar;
no necesita instalar Locust o k6 para repetir este perfil pequeno. Se guardan
trazas con DOM, capturas y codigo; las pruebas usan cuentas sinteticas.
La [guia oficial de Playwright para CI](https://playwright.dev/python/docs/ci)
detalla la instalacion de navegadores y dependencias del runner.

## 6.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
& $qaPython -m playwright install chromium
$env:QA_REQUIRE_BROWSER = '1'
& $qaPython -m pytest tests/system/test_inventario_playwright.py tests/system/test_e2e_pos_playwright.py tests/system/test_inventario_seguridad_carga.py -q -s
```

En Linux usar `python -m playwright install --with-deps chromium`. Si falta el
navegador, QA_REQUIRE_BROWSER=1 hace fallar la prueba; no hay retries que oculten
errores. No se depende de CDN durante las pruebas de navegador. Las trazas se
pueden abrir con `python -m playwright show-trace reports/browser/archivo.zip`,
sustituyendo por el archivo existente que liste `Get-ChildItem reports/browser`.

Contra un servidor QA **ya desplegado**, con un usuario ALMACENERO de pruebas
existente y contraseña provista en INVENTORY_LOAD_PASSWORD:

```powershell
& $qaPython scripts/qa_inventory_load.py --url http://127.0.0.1:8000 --username qa_carga --users 4 --requests 20 --p95-max-ms 2000
```

El test automatizado crea sus propias cuentas. El CLI no crea usuarios en un
despliegue. Para un perfil mayor acordado: `--users 20 --requests 1000`; no inferir
capacidad productiva a partir de veinte solicitudes. En esta sesion solo se
ejecuto el perfil pequeno local; el despliegue completo queda pendiente.

## 6.4 Código Completo del Test de Sistema (E2E) + Script rápido de Carga/Performance

Archivo: `tests/system/test_inventario_playwright.py`

```python
"""Flujo de almacen en Chromium: producto, recepcion, merma, alertas y reportes."""
import uuid
from datetime import date, timedelta

import pytest

from tests.system.test_e2e_pos_playwright import navegador  # noqa: F401
from src.modules.catalog.models import CategoriaModel, ProductoModel
from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.domain.enums.rol_usuario import RolUsuario
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
from src.modules.inventory.models import ExistenciaModel, LoteModel, MovimientoModel

pytestmark = [pytest.mark.system, pytest.mark.e2e, pytest.mark.django_db]


def test_almacenero_completa_flujo_de_inventario(live_server, navegador):
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(
        UsuarioInputDTO(nombre_completo="Almacenero UI", username="almacen_ui", email="almacen_ui@example.test",
                        password="Secreta123", rol=RolUsuario.ALMACENERO.value)
    )
    categoria = CategoriaModel.objects.create(id=uuid.uuid4(), nombre="Lacteos UI", slug="lacteos-ui")
    vencimiento = (date.today() + timedelta(days=20)).isoformat()
    page = navegador.new_page()
    page.goto(live_server.url)
    page.fill("input[name=username]", "almacen_ui")
    page.fill("input[name=password]", "Secreta123")
    page.click("button:has-text('Ingresar')")
    page.wait_for_url("**/catalogo/")

    page.goto(f"{live_server.url}/inventario/")
    page.get_by_role("link", name="Registrar producto", exact=True).click()
    page.fill("input[name=nombre]", "Leche UI")
    page.fill("input[name=codigo_barras]", "7751234567811")
    page.fill("input[name=costo]", "5")
    page.fill("input[name=precio_venta]", "8")
    page.select_option("select[name=categoria_id]", str(categoria.id))
    page.fill("input[name=stock_minimo]", "8")
    page.fill("input[name=fecha_vencimiento]", vencimiento)
    page.get_by_role("button", name="Guardar", exact=True).click()
    page.wait_for_url("**/catalogo/productos/admin/")
    producto = ProductoModel.objects.get(codigo_barras="7751234567811")
    assert producto.stock_minimo == 8 and producto.categoria_id == categoria.id

    page.goto(f"{live_server.url}/inventario/recepcion/")
    page.select_option("select[name=producto_id]", str(producto.id))
    page.fill("input[name=numero_lote]", "LOTE-UI")
    page.fill("input[name=cantidad]", "10")
    page.fill("input[name=costo_unitario]", "5")
    page.fill("input[name=fecha_vencimiento]", vencimiento)
    page.get_by_role("button", name="Registrar ingreso", exact=True).click()
    page.wait_for_url("**/inventario/")
    assert ExistenciaModel.objects.get(producto_id=producto.id).cantidad == 10
    lote = LoteModel.objects.get(producto_id=producto.id)

    page.get_by_role("link", name="Registrar merma", exact=True).click()
    page.select_option("select[name=producto_id]", str(producto.id))
    page.select_option("select[name=lote_id]", str(lote.id))
    page.fill("input[name=cantidad]", "3")
    page.select_option("select[name=motivo]", "DANADO")
    page.get_by_role("button", name="Registrar merma", exact=True).click()
    page.wait_for_load_state("networkidle")
    assert ExistenciaModel.objects.get(producto_id=producto.id).cantidad == 7
    assert LoteModel.objects.get(pk=lote.id).cantidad_restante == 7

    page.goto(f"{live_server.url}/inventario/alertas/")
    assert "Leche UI: 7 u." in page.content()
    assert "LOTE-UI" in page.content()
    page.goto(f"{live_server.url}/inventario/kardex/?producto_id={producto.id}")
    assert "ENTRADA" in page.content() and "MERMA" in page.content()
    assert MovimientoModel.objects.filter(producto_id=producto.id).count() == 2
    page.goto(f"{live_server.url}/reportes/inventario/")
    assert "Leche UI" in page.content() and "60 dias" in page.content()
    assert "Mayor ganancia por producto" in page.content()
```

El fixture `navegador` importado por ese archivo incluye arranque estricto, aislamiento
de CDN y trazas; se entrega completo junto con el flujo POS que valida:

Archivo: `tests/system/test_e2e_pos_playwright.py`

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

Archivo: `tests/system/test_inventario_seguridad_carga.py`

```python
"""HTTP real bajo concurrencia acotada y controles basicos del navegador."""
import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from django.test import Client

from scripts.qa_inventory_load import ejecutar_carga
from src.modules.catalog.models import ProductoModel
from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
from src.modules.inventory.models import MovimientoModel

pytestmark = [pytest.mark.system, pytest.mark.django_db(transaction=True)]


def test_formularios_rechazan_post_sin_csrf_y_escapan_html(django_user_model):
    usuario = django_user_model.objects.create_user(username="qa_seguridad")
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(usuario)
    sesion = cliente.session
    sesion["rol"] = "ALMACENERO"
    sesion.save()
    for ruta in ("/inventario/recepcion/", "/inventario/mermas/", "/catalogo/productos/nuevo/"):
        assert cliente.post(ruta, {"cantidad": 1}).status_code == 403
    assert not MovimientoModel.objects.exists()
    ProductoModel.objects.create(id=uuid4(), nombre='<script>alert("x")</script>', codigo_barras="7751234567804",
                                 costo=5, precio_venta=10, estado="ACTIVO")
    respuesta = cliente.get("/inventario/")
    assert respuesta.status_code == 200
    assert b"<script>alert(" not in respuesta.content
    assert b"&lt;script&gt;" in respuesta.content
    assert respuesta.headers["X-Frame-Options"] == "DENY"


@pytest.mark.performance
def test_carga_http_autenticada_sin_errores(live_server):
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(
        UsuarioInputDTO(username="qa_carga", password="PruebaInventario2026", nombre_completo="QA Carga", rol="ALMACENERO")
    )
    ProductoModel.objects.create(id=uuid4(), nombre="Carga QA", codigo_barras="7751234567805",
                                 costo=5, precio_venta=10, estado="ACTIVO")
    # El servidor de prueba escucha IPv4. Evita medir el fallback IPv6 de localhost.
    url = live_server.url.replace("http://localhost:", "http://127.0.0.1:")
    resultado = ejecutar_carga(url, "qa_carga", "PruebaInventario2026", usuarios=4, peticiones=20,
                              p95_max_ms=float(os.environ.get("INVENTORY_P95_MAX_MS", "2000")))
    print(json.dumps(resultado))
    Path("reports").mkdir(exist_ok=True)
    Path("reports/inventory-load.json").write_text(json.dumps(resultado), encoding="utf-8")
    assert resultado["aprobado"], resultado
```

Archivo: `scripts/qa_inventory_load.py`

```python
"""Carga HTTP autenticada y acotada sobre las pantallas reales de inventario."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from http.cookiejar import CookieJar
import json
import math
import os
from time import perf_counter
from urllib.parse import urlencode, urlsplit
from urllib.request import build_opener, HTTPCookieProcessor, Request


class TokenCSRF(HTMLParser):
    token = None

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if tag == "input" and atributos.get("name") == "csrfmiddlewaretoken":
            self.token = atributos.get("value")


def ejecutar_carga(url, username, password, usuarios=4, peticiones=20, p95_max_ms=2000):
    base = url.rstrip("/")
    rutas = ("/inventario/", "/inventario/alertas/", "/reportes/inventario/")

    def autenticar():
        cliente = build_opener(HTTPCookieProcessor(CookieJar()))
        try:
            with cliente.open(base + "/", timeout=10) as respuesta:
                parser = TokenCSRF()
                parser.feed(respuesta.read().decode("utf-8"))
            if not parser.token:
                raise ValueError("Login sin token CSRF")
            datos = urlencode({"username": username, "password": password, "csrfmiddlewaretoken": parser.token}).encode()
            with cliente.open(Request(base + "/", data=datos, headers={"Referer": base + "/"}), timeout=10) as respuesta:
                if urlsplit(respuesta.geturl()).path != "/catalogo/":
                    raise ValueError("Login rechazado")
                respuesta.read()
        except Exception as exc:
            return None, type(exc).__name__
        return cliente, None

    # Prepara sesiones fuera de la ventana medida. El objetivo son lecturas
    # concurrentes de inventario; autenticacion masiva requiere su propia prueba.
    sesiones = [autenticar() for _ in range(usuarios)]

    def usuario(indice):
        total = peticiones // usuarios + (indice < peticiones % usuarios)
        if not total:
            return []
        cliente, error = sesiones[indice]
        if error:
            return [{"ok": False, "ms": 0, "error": error, "fase": "login"}]
        muestras = []
        for i in range(total):
            ruta = rutas[i % len(rutas)]
            inicio = perf_counter()
            try:
                with cliente.open(base + ruta, timeout=10) as respuesta:
                    cuerpo = respuesta.read()
                    ok = respuesta.status == 200 and urlsplit(respuesta.geturl()).path == ruta and b"<main" in cuerpo
                muestras.append({"ok": ok, "ms": (perf_counter() - inicio) * 1000, "ruta": ruta})
            except Exception as exc:
                muestras.append({"ok": False, "ms": (perf_counter() - inicio) * 1000,
                                 "error": type(exc).__name__, "ruta": ruta})
        return muestras

    with ThreadPoolExecutor(max_workers=usuarios) as pool:
        muestras = [m for lote in pool.map(usuario, range(usuarios)) for m in lote]
    tiempos = sorted(m["ms"] for m in muestras)
    p95 = tiempos[max(0, math.ceil(len(tiempos) * 0.95) - 1)] if tiempos else 0
    errores = sum(not m["ok"] for m in muestras)
    aprobado = len(muestras) == peticiones and errores == 0 and p95 <= p95_max_ms
    return {"aprobado": aprobado, "usuarios": usuarios, "peticiones_solicitadas": peticiones,
            "muestras": len(muestras), "errores": errores, "p95_ms": round(p95, 2), "p95_max_ms": p95_max_ms}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", required=True)
    parser.add_argument("--users", type=int, choices=range(1, 51), default=4)
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--p95-max-ms", type=float, default=2000)
    args = parser.parse_args()
    password = os.environ.get("INVENTORY_LOAD_PASSWORD")
    if not password:
        parser.error("Defina INVENTORY_LOAD_PASSWORD para un usuario de QA con rol ALMACENERO")
    if not 1 <= args.requests <= 10000:
        parser.error("--requests debe estar entre 1 y 10000")
    resultado = ejecutar_carga(args.url, args.username, password, args.users, args.requests, args.p95_max_ms)
    print(json.dumps(resultado, ensure_ascii=False))
    return 0 if resultado["aprobado"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

# 7. NIVEL 4: PRUEBAS DE ACEPTACIÓN (UAT / BDD)

## 7.1 Escenarios de Negocio en Formato Gherkin

Se entregan seis escenarios de recepcion, merma, rechazo sin perdida de datos,
notificacion, vencimiento y reportes. Complementan las pruebas RF-016/017 del flujo
UI completo; no se presenta una prueba unitaria aislada como aprobacion del cliente.

Archivo: `tests/uat/features/inventario.feature`

```gherkin
Feature: Inventario de la tienda RF-016 a RF-024
  Como almacenero quiero controlar entradas y mermas con trazabilidad.

  Background:
    Given un almacenero autenticado con un producto y minimo de 5 unidades

  Scenario: Recepcion de mercaderia con lote
    When registra una recepcion de 10 unidades con lote "UAT-INGRESO"
    Then el stock fisico es de 10 unidades
    And el kardex contiene una entrada de 10 unidades

  Scenario: Merma por dano justificada
    Given una recepcion previa de 10 unidades
    When registra una merma de 3 unidades por "DANADO"
    Then el stock fisico es de 7 unidades
    And el kardex conserva el motivo "MERMA:DANADO"

  Scenario: Una merma excesiva se rechaza sin perdida de datos
    Given una recepcion previa de 10 unidades
    When registra una merma de 11 unidades por "ROBO"
    Then la operacion muestra un error de validacion
    And el stock fisico es de 10 unidades
    And no hay movimientos de merma

  Scenario: Se notifica al caer debajo del minimo
    Given una recepcion previa de 6 unidades
    When registra una merma de 2 unidades por "DANADO"
    Then el stock fisico es de 4 unidades
    And recibe una notificacion de stock minimo

  Scenario: La alerta incluye 30 dias y excluye 31 dias
    Given un lote que vence en 30 dias y otro en 31 dias
    When consulta las alertas de inventario
    Then ve solo el lote que vence en 30 dias

  Scenario: Productos sin ventas aparecen en baja rotacion y ranking
    Given otro producto con margen mayor y sin ventas
    When consulta los reportes de inventario
    Then ambos productos aparecen en baja rotacion
    And el producto con mayor margen encabeza el ranking
```

## 7.2 Automatización del UAT (Step Definitions) o Checklist de Validación Manual

Los steps usan vistas, formularios, transacciones y repositorios reales. Solo el
transporte de correo se limita al outbox de pruebas, comprobando callbacks de commit.

Archivo: `tests/uat/test_inventario_bdd.py`

```python
"""Nivel 4: criterios de negocio sobre vistas y persistencia reales."""
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.core import mail
from django.db import transaction
from pytest_bdd import given, parsers, scenarios, then, when

from src.modules.catalog.models import ProductoModel
from src.modules.inventory.application.dto.lote_dto import RecepcionLoteDTO
from src.modules.inventory.application.use_cases.recibir_mercaderia import RecibirMercaderia
from src.modules.inventory.infrastructure.factories import (
    construir_lote_repository, construir_movimiento_repository, construir_stock_repository,
)
from src.modules.inventory.models import ExistenciaModel, LoteModel, MovimientoModel

pytestmark = [pytest.mark.uat, pytest.mark.django_db]
scenarios("features/inventario.feature")


@given("un almacenero autenticado con un producto y minimo de 5 unidades", target_fixture="contexto")
def almacen(client, django_user_model):
    user = django_user_model.objects.create_user(username="almacen_bdd")
    client.force_login(user)
    session = client.session
    session["rol"] = "ALMACENERO"
    session["usuario_id"] = str(uuid4())
    session.save()
    p = ProductoModel.objects.create(id=uuid4(), nombre="Leche UAT", codigo_barras="7751234567802",
                                    costo=Decimal("5"), precio_venta=Decimal("10"), estado="ACTIVO", stock_minimo=5)
    return {"client": client, "producto": p}


def recepcion(contexto, cantidad, numero="UAT-PREVIO", dias=20):
    return RecibirMercaderia(construir_stock_repository(), construir_lote_repository(), construir_movimiento_repository(),
                            uow=transaction.atomic()).ejecutar(
        RecepcionLoteDTO(str(contexto["producto"].id), numero, cantidad, 5,
                        fecha_vencimiento=date.today() + timedelta(days=dias)))


@when(parsers.parse('registra una recepcion de {cantidad:d} unidades con lote "{numero}"'))
def registrar_recepcion(contexto, cantidad, numero):
    contexto["respuesta"] = contexto["client"].post("/inventario/recepcion/", {
        "producto_id": str(contexto["producto"].id), "numero_lote": numero,
        "cantidad": cantidad, "costo_unitario": "5",
        "fecha_vencimiento": (date.today() + timedelta(days=20)).isoformat(),
    })
    assert contexto["respuesta"].status_code == 302


@given(parsers.parse("una recepcion previa de {cantidad:d} unidades"))
def recepcion_previa(contexto, cantidad):
    recepcion(contexto, cantidad)


@when(parsers.parse('registra una merma de {cantidad:d} unidades por "{motivo}"'))
def registrar_merma(contexto, cantidad, motivo, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        contexto["respuesta"] = contexto["client"].post("/inventario/mermas/", {
            "producto_id": str(contexto["producto"].id), "cantidad": cantidad, "motivo": motivo,
        })


@then(parsers.parse("el stock fisico es de {cantidad:d} unidades"))
def verificar_stock(contexto, cantidad):
    assert ExistenciaModel.objects.get(producto_id=contexto["producto"].id).cantidad == cantidad
    assert sum(LoteModel.objects.filter(producto_id=contexto["producto"].id).values_list("cantidad_restante", flat=True)) == cantidad


@then(parsers.parse("el kardex contiene una entrada de {cantidad:d} unidades"))
def verificar_entrada(contexto, cantidad):
    assert MovimientoModel.objects.filter(producto_id=contexto["producto"].id, tipo="ENTRADA", cantidad=cantidad).count() == 1


@then(parsers.parse('el kardex conserva el motivo "{motivo}"'))
def verificar_motivo(contexto, motivo):
    assert MovimientoModel.objects.filter(producto_id=contexto["producto"].id, tipo="MERMA", referencia=motivo).exists()


@then("la operacion muestra un error de validacion")
def verificar_error(contexto):
    assert contexto["respuesta"].status_code == 200
    assert contexto["respuesta"].context["form"].errors


@then("no hay movimientos de merma")
def verificar_sin_merma(contexto):
    assert not MovimientoModel.objects.filter(producto_id=contexto["producto"].id, tipo="MERMA").exists()


@then("recibe una notificacion de stock minimo")
def verificar_notificacion(contexto):
    assert len(mail.outbox) == 1
    assert str(contexto["producto"].id) in mail.outbox[0].body


@given("un lote que vence en 30 dias y otro en 31 dias")
def lotes_limite(contexto):
    recepcion(contexto, 2, "UAT-30", 30)
    recepcion(contexto, 2, "UAT-31", 31)


@when("consulta las alertas de inventario")
def consultar_alertas(contexto):
    contexto["respuesta"] = contexto["client"].get("/inventario/alertas/")
    assert contexto["respuesta"].status_code == 200


@then("ve solo el lote que vence en 30 dias")
def verificar_alertas(contexto):
    assert [l.numero_lote for l in contexto["respuesta"].context["por_vencer"]] == ["UAT-30"]


@given("otro producto con margen mayor y sin ventas")
def producto_mayor_margen(contexto):
    contexto["otro"] = ProductoModel.objects.create(id=uuid4(), nombre="Mayor margen UAT", codigo_barras="7751234567803",
                                                   costo=Decimal("5"), precio_venta=Decimal("15"), estado="ACTIVO")


@when("consulta los reportes de inventario")
def consultar_reportes(contexto):
    contexto["respuesta"] = contexto["client"].get("/reportes/inventario/")
    assert contexto["respuesta"].status_code == 200


@then("ambos productos aparecen en baja rotacion")
def verificar_baja_rotacion(contexto):
    ids = {p["producto_id"] for p in contexto["respuesta"].context["baja_rotacion"]}
    assert ids == {str(contexto["producto"].id), str(contexto["otro"].id)}


@then("el producto con mayor margen encabeza el ranking")
def verificar_ranking(contexto):
    assert contexto["respuesta"].context["mayor_ganancia"][0]["producto_id"] == str(contexto["otro"].id)
```

Checklist para el responsable del negocio:

- [ ] Crear producto como administrador y almacenero, verificando categoria, costo, precio, minimo y vencimiento.
- [ ] Recepcionar lote; vender parcialmente y completar cobro; comprobar saldo y movimientos sin duplicados.
- [ ] Registrar merma por daño, robo y vencimiento; comprobar que un exceso no cambia cantidades.
- [ ] Ver alertas inferior/al igual al minimo y vencimientos de hoy, 30 y 31 dias.
- [ ] Consultar kardex con filtros y mas de 50 movimientos.
- [ ] Identificar productos sin ventas pagadas por 60 dias y ordenar margen segun formula acordada.
- [x] Corregidos QA-INV-01..03 con regresiones unitarias y persistencia real. Revisar `inventory_uat_approval.md` para la firma de negocio.
- [ ] Registrar version/commit, ambiente, nombre del aprobador, fecha, observaciones y decision.

## 7.3 Guía Paso a Paso para ejecutar y aprobar el UAT

```powershell
& $qaPython -m pytest tests/uat/test_inventario_bdd.py -q --junitxml=reports/inventory-uat.xml
```

Primero ejecutar BDD, luego realizar el checklist en QA con datos sinteticos y
revisar evidencias con el almacenero/administrador. La automatizacion paso localmente;
**no existe firma humana del Product Owner** en esta entrega. No declarar UAT
aprobado por el cliente a partir de un exit code cero.

# 8. GUÍA DE AI SKILLS, MCP Y AUTOMATIZACIÓN AGÉNTICA (CONTEXTO 2026-2027)

## 8.1 Configuración de Skill / Rule para el Agente de Código

Se agrega una regla de Cursor en la raiz; Codex puede leerla explicitamente en
el prompt, junto con AGENTS.md. No se afirma que Cursor rules se carguen
automaticamente en todos los agentes o clientes.

Archivo: `../.cursor/rules/inventory-testing.mdc`

```markdown
---
description: Pruebas del modulo Inventario RF-016 a RF-024
globs: ["puntoventa_total/src/modules/inventory/**/*.py", "puntoventa_total/src/modules/catalog/**/*.py", "puntoventa_total/tests/**/*inventario*.py"]
alwaysApply: false
---

Antes de cambiar pruebas, leer docs/requirements/inventario_rf016_rf024.md y
docs/testing/inventory_master_plan.md (rutas relativas a puntoventa_total).

- Derivar cada asercion de RF-016..024 o de una invariante documentada.
- Unitarias: tests/unit/inventory, puertos con Mock(spec=...), sin ORM/red/broker.
- Integracion: tests/integration; probar rollback y stock/lotes/kardex juntos.
  SQLite no demuestra bloqueos. Ejecutar scripts/qa_inventory_mysql.py con Docker.
- Sistema: Chromium, CSRF, permisos y carga HTTP; guardar trazas. En CI un navegador
  ausente debe fallar con QA_REQUIRE_BROWSER=1. No sustituir errores por skip.
- UAT: actualizar Gherkin y steps reales en tests/uat. La aprobacion del cliente
  es humana y separada del resultado automatizado.
- Congelar reloj o usar fechas relativas coherentes; nunca usar sleeps para sincronizar.
- No debilitar aserciones, subir umbrales de latencia, reducir cobertura, agregar
  xfail/skip/retries ni cambiar requisitos para lograr un resultado verde.
- Un test roto por cambio de negocio necesita evidencia del requisito revisado.
  Si es defecto del producto, conservar una regresion y reportar/corregir el defecto.
- Ejecutar en orden unitarias, integracion, sistema y UAT. Reportar comando,
  runtime, infraestructura, conteos y exit code. Distinguir ejecutado de propuesto.
- No publicar a Postman ni cambiar protecciones de GitHub sin autorizacion.
- Usar las instrucciones AGENTS.md/RTK.md aplicables al ejecutar comandos.
```

Flujo: leer RF y diff -> identificar frontera afectada -> agregar regresion del
contrato -> ejecutar nivel mas pequeno -> integrar -> E2E -> BDD -> adjuntar
comandos, resultados y limitaciones. El agente no debe editar pruebas solo para
acomodar una regresion del producto. Hypothesis conserva ejemplos y usa configuracion
reproducible; la cobertura no sustituye un analisis de mutaciones. No se ejecutaron
mutantes, por lo que no se declara un mutation score.

## 8.2 Servidores MCP recomendados

| Herramienta | Uso concreto | Limite de esta entrega |
|---|---|---|
| Playwright MCP oficial | Inspeccionar UI de QA y proponer locators; reproducir un fallo guardado | No se instalo ni conecto; no sustituye los tests versionados |
| GitHub MCP oficial, opcional | Leer diff y evidencias de Actions | No se publicaron comentarios, PR ni cambios de proteccion |
| Postman skills api-testing / ci-integration | Revisar contratos HTTP/gates cuando existan colecciones | Las pantallas de inventario usan sesiones y CSRF; no se invento una API REST |
| OpenAI Docs MCP, opcional | Consultar sintaxis vigente de Codex y MCP | Usado aqui como documentacion, sin acceso a cuentas del usuario |
| ORM/CLI de BD | Verificar estado dentro del contenedor de pruebas | No se requiere un servidor SQL MCP con permisos de escritura |

El [servidor oficial Playwright MCP](https://github.com/microsoft/playwright-mcp)
documenta su configuracion para agentes. Ejemplo para una instalacion futura,
despues de revisar y fijar la version del paquete que se vaya a usar:

```powershell
codex mcp add playwright -- npx -y @playwright/mcp@latest
codex mcp list
```

El comando de descubrimiento usa latest como en la documentacion del servidor;
no forma parte del lock de CI. Fijar la version seleccionada antes de automatizar.
La [documentacion oficial de OpenAI para MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)
explica el registro de servidores. No es necesario dar acceso a una BD productiva.
Testcontainers Cloud es una alternativa a un Docker remoto, no un servicio conectado
o verificado en esta sesion.

## 8.3 Flujo de Auto-Healing (Autoreparación de Tests)

Desde la raiz del repositorio, con Codex instalado y autenticado:

```powershell
codex exec --sandbox workspace-write -C puntoventa_total "Lee ../.cursor/rules/inventory-testing.mdc y docs/testing/inventory_master_plan.md. Reproduce el primer fallo de inventario. Distingue cambio de contrato, defecto del producto y defecto del test. No elimines aserciones ni agregues skips, xfail o retries para conseguir verde. Agrega una regresion del comportamiento acordado y presenta el diff con la evidencia. No publiques ni cambies protecciones de rama."
```

La [guia oficial de ejecucion no interactiva de Codex](https://learn.chatgpt.com/docs/non-interactive-mode)
documenta el sandbox para permitir cambios en el workspace. Este comando se
proporciona como guia; no se lanzo otro agente durante la auditoria.
Tras revisar el diff, ejecutar los cuatro niveles en orden. Ante un requisito nuevo,
actualizar primero RF/Gherkin y conservar la justificacion; ante un defecto de negocio,
corregir el producto con su regresion. Un locator nuevo no justifica borrar una
validacion de stock. No hay promesa de autoreparacion infalible ni de cero flakiness.

# 9. PIPELINE CI/CD (QUALITY GATES)

El workflow esta en `.github/workflows/inventory-quality.yml` de la raiz. Tiene
cuatro jobs dependientes: unit -> integration -> system -> uat, permisos de lectura,
tiempos limite, cobertura minima 80 %, contenedor efimero y artefactos de evidencia.
No publica a Postman, no despliega y no necesita secretos para estas cuentas de QA.

**Estado local actualizado: gate de hallazgos aprobado.** QA-INV-01..03 fueron
corregidos y cuentan con regresiones. El gate permanece para impedir
confundir cobertura alta con aprobacion de release. Despues de corregir cada
hallazgo, su regresion debe pasar y el reproductor debe dejar de detectarlo; no
eliminar el gate para volver verde el pipeline.

Para bloquear realmente un merge, la configuracion del repositorio debe exigir el
checks `Inventory / Unit`, `Inventory / Integration`, `Inventory / System` e
`Inventory / UAT`. Exigir solo el ultimo no basta si los anteriores fallan y el
ultimo queda omitido por su dependencia. El YAML por si solo
no modifica la proteccion de ramas. No se hizo esa modificacion remota ni se
observo una ejecucion en GitHub Actions. La [documentacion de GitHub](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
describe los eventos que inician workflows.

Archivo: `../.github/workflows/inventory-quality.yml`

```yaml
name: Inventory quality

on:
  pull_request:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: inventory-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

defaults:
  run:
    working-directory: puntoventa_total

jobs:
  unit:
    name: Inventory / Unit
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.14.7'
          cache: pip
          cache-dependency-path: puntoventa_total/requirements/*.txt
      - run: python -m pip install -r requirements/qa-inventory.txt
      - name: Nivel 1 y cobertura de inventario
        run: >-
          python -m pytest tests/unit/inventory -q
          --cov=src.modules.inventory.domain --cov=src.modules.inventory.application
          --cov-fail-under=80 --cov-report=xml:reports/inventory-unit-coverage.xml
          --junitxml=reports/inventory-unit.xml
      - name: Bloquear riesgos de dominio reproducidos por la auditoria
        run: python -m scripts.qa_inventory_findings > reports/inventory-findings.json
      - name: Regresiones de descuentos del POS
        run: python -m pytest tests/unit/domain/test_venta_reglas.py -q --junitxml=reports/sales-regressions.xml
      - uses: actions/upload-artifact@v5
        if: always()
        with:
          name: inventory-unit
          path: puntoventa_total/reports/

  integration:
    name: Inventory / Integration
    needs: unit
    runs-on: ubuntu-24.04
    timeout-minutes: 25
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.14.7'
          cache: pip
          cache-dependency-path: puntoventa_total/requirements/*.txt
      - run: sudo apt-get update && sudo apt-get install -y pkg-config default-libmysqlclient-dev build-essential
      - run: python -m pip install -r requirements/qa-inventory-mysql.txt
      - name: Nivel 2 en MySQL Testcontainers con dos escritores
        run: >-
          python scripts/qa_inventory_mysql.py
          tests/integration/test_inventario_requisitos.py
          tests/integration/test_inventario_mysql.py
          --junitxml=reports/inventory-integration.xml
      - uses: actions/upload-artifact@v5
        if: always()
        with:
          name: inventory-integration
          path: puntoventa_total/reports/

  system:
    name: Inventory / System
    needs: integration
    runs-on: ubuntu-24.04
    timeout-minutes: 20
    env:
      QA_REQUIRE_BROWSER: '1'
      INVENTORY_P95_MAX_MS: '2000'
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.14.7'
          cache: pip
          cache-dependency-path: puntoventa_total/requirements/*.txt
      - run: python -m pip install -r requirements/qa-inventory.txt
      - run: python -m playwright install --with-deps chromium
      - name: Nivel 3 UI, seguridad y carga HTTP
        run: >-
          python -m pytest tests/system/test_inventario_playwright.py
          tests/system/test_e2e_pos_playwright.py
          tests/system/test_inventario_seguridad_carga.py -q -s
          --junitxml=reports/inventory-system.xml
      - uses: actions/upload-artifact@v5
        if: always()
        with:
          name: inventory-system
          path: puntoventa_total/reports/

  uat:
    name: Inventory / UAT
    needs: system
    runs-on: ubuntu-24.04
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: '3.14.7'
          cache: pip
          cache-dependency-path: puntoventa_total/requirements/*.txt
      - run: python -m pip install -r requirements/qa-inventory.txt
      - name: Nivel 4 criterios de negocio automatizados
        run: python -m pytest tests/uat/test_inventario_bdd.py -q --junitxml=reports/inventory-uat.xml
      - uses: actions/upload-artifact@v5
        if: always()
        with:
          name: inventory-uat
          path: puntoventa_total/reports/
```

La suite local y CI deben preservar los codigos de error. No usar continue-on-error
ni suprimir el fallo de cobertura, Docker ausente, navegador ausente o el gate de
riesgos. Para produccion falta verificar tambien versiones soportadas, fijacion de
acciones por SHA y de imagen por digest conforme a la politica de la organizacion,
despliegue completo, SMTP y worker/broker reales.

# 10. MATRIZ DE TRAZABILIDAD DE PRUEBAS DEL MÓDULO

| ID Caso | Funcionalidad / Método del Módulo | Nivel | Tipo | Resultado Esperado | Comando de Ejecucion |
| :--- | :--- | :--- | :--- | :--- | :--- |
| INV-U01 | Existencia, conservacion de cantidades | Unit | Positivo / Borde | No negativo y entradas menos salidas | python -m pytest tests/unit/inventory -k propiedad -q |
| INV-U02 | Cantidades cero/negativas y reservas | Unit | Negativo | StockException sin cambios | python -m pytest tests/unit/inventory -k cantidades -q |
| INV-U03 | PoliticaStock PEPS | Unit | Borde | Vencimiento cercano primero, excluye vencidos | python -m pytest tests/unit/inventory -k peps -q |
| INV-U04 | Alertas dias 0/30/31 | Unit | Borde | Incluye 0 y 30, excluye 31 y vencidos | python -m pytest tests/unit/inventory -k limites -q |
| INV-I16 | RF-016 Crear/editar producto | Int | Positivo / Negativo | Todos los campos persisten; duplicados no actualizan parcialmente | python -m pytest tests/integration/test_inventario_requisitos.py -k rf016 -q |
| INV-I17 | RF-017 Pago y rollback | Int | Positivo / Negativo | Parcial no descuenta; total si; segunda linea fallida revierte | python -m pytest tests/integration/test_inventario_requisitos.py -k rf017 -q |
| INV-I18 | RF-018 Notificar minimo | Int | Borde | Solo tras commit y disponible < minimo individual | python -m pytest tests/integration/test_inventario_requisitos.py -k rf018 -q |
| INV-I19 | RF-019 Vencimientos | Int | Borde | Excluye agotados y 31 dias | python -m pytest tests/integration/test_inventario_requisitos.py -k rf019 -q |
| INV-I20 | RF-020 Recepcion | Int | Positivo / Negativo | Lote, existencia y entrada juntos | python -m pytest tests/integration/test_inventario_requisitos.py -k rf020 -q |
| INV-I21 | RF-021 Merma | Int | Positivo / Negativo | Motivo valido y lote del producto; sin perdida si falla | python -m pytest tests/integration/test_inventario_requisitos.py -k rf021 -q |
| INV-I22 | RF-022 Kardex | Int | Borde | 52 movimientos, paginas 50/2, filtros correctos | python -m pytest tests/integration/test_inventario_requisitos.py -k rf022 -q |
| INV-I23 | RF-023 Rotacion | Int | Borde | Solo ventas pagadas en ventana de 60 dias excluyen producto | python -m pytest tests/integration/test_inventario_requisitos.py -k rf023 -q |
| INV-I24 | RF-024 Margen | Int | Positivo / Borde | Orden por margen; costo cero y producto sin ventas | python -m pytest tests/integration/test_inventario_requisitos.py -k rf024 -q |
| INV-IC1 | Dos salidas concurrentes | Int MySQL | Negativo | Una acepta y otra rechaza; queda 1 unidad | python scripts/qa_inventory_mysql.py tests/integration/test_inventario_mysql.py -k descontar |
| INV-IC2 | Dos reservas concurrentes | Int MySQL | Negativo | Una reserva; disponible 1 | python scripts/qa_inventory_mysql.py tests/integration/test_inventario_mysql.py -k reservar |
| INV-IC3 | Doble liberacion concurrente | Int MySQL | Borde | Ambas peticiones terminan sin consumir la otra reserva | python scripts/qa_inventory_mysql_native.py --basedir RUTA_MYSQL |
| INV-IC4 | Doble confirmacion concurrente | Int MySQL | Negativo | Una confirma, otra rechaza; una sola SALIDA_PEDIDO y otra reserva intacta | python scripts/qa_inventory_mysql_native.py --basedir RUTA_MYSQL |
| INV-IC5 | Primeras recepciones concurrentes | Int MySQL | Borde | Una existencia, dos lotes y movimientos; stock acumulado 7 | python scripts/qa_inventory_mysql_native.py --basedir RUTA_MYSQL |
| INV-S01 | Almacenero y RF-016/018/019/020/021/022/023/024 | Sys | Positivo | Flujo completo de almacen por UI | python -m pytest tests/system/test_inventario_playwright.py -q |
| INV-S02 | RF-017 Cobro y PDF | Sys | Positivo | Venta pagada y stock descontado; PDF valido | python -m pytest tests/system/test_e2e_pos_playwright.py -q |
| INV-S03 | CSRF, XSS y frame headers | Sys | Negativo | POST sin token 403; HTML escapado; DENY | python -m pytest tests/system/test_inventario_seguridad_carga.py -k csrf -q |
| INV-P01 | Carga GET autenticada | Sys | Positivo | 20 respuestas validas, 4 usuarios y p95 <= 2000 ms | python -m pytest tests/system/test_inventario_seguridad_carga.py -k carga_http -q -s |
| INV-A01..06 | Recepcion, merma, rechazo, alertas y reportes | UAT | Positivo / Negativo / Borde | Seis escenarios de negocio satisfechos | python -m pytest tests/uat/test_inventario_bdd.py -q |
| QA-INV-01..03 | Riesgos reproducidos del dominio | Gate de auditoria | Negativo | Debe terminar con error mientras existan | python -m scripts.qa_inventory_findings |

## Evidencia observada de esta ejecución

| Comprobacion | Resultado observado |
|---|---|
| Regresion completa, Python 3.14.7 / Django 6.1.2 / Windows | 300 aprobadas sobre MySQL 8.4.3/InnoDB; 0 fallos, 0 omisiones, 0 xfail; exit 0 |
| Nivel 1 | 106 aprobadas; 95.95 % de lineas; gate >=80 % aprobado |
| Nivel 2 local | 48 casos RF/reservas y 5 casos de concurrencia sobre MySQL real aprobados |
| Nivel 3 | UI de inventario y POS, CSRF, escape HTML y cabecera aprobados |
| Carga HTTP | 20 muestras; 4 usuarios; 0 errores; p95 131.26 ms frente a 2000 ms |
| Nivel 4 | 6 escenarios BDD aprobados; firma de negocio pendiente |
| Gate de auditoria | Exit 0; los tres hallazgos ya no se reproducen |
| Docker / Testcontainers / MySQL | MySQL 8.4.3 nativo efimero aprobado; Docker/Testcontainers no ejecutado |
| Django system check | Sin errores |
| GitHub Actions / instalacion limpia | No ejecutados; el perfil QA fija versiones observadas localmente |

Artefactos: reports/inventory-regression.xml, inventory-unit-coverage.xml/json, inventory-load.json, inventory-findings.json y browser/*.zip.
La ejecucion completa no omitio pruebas. RN-07 de ventas se corrigio con un tope al saldo restante; su antigua prueba xfail y cinco regresiones adicionales ahora pasan.

# EVALUACIÓN FINAL DEL MÓDULO AUDITADO

Valoraciones de ingenieria, no metricas de una certificacion externa:

| Dimension | Puntuacion | Fundamento |
|---|---|---|
| Testabilidad del Codigo Actual | 8/10 | Puertos/UoW inyectables; quedan reloj y configuracion global |
| Cobertura Unitaria Alcanzable | 9/10 | 95,95 % de lineas medido en dominio/aplicacion; falta mutacion |
| Aislamiento de Dependencias | 8/10 | Sin ORM/red en unitarias; infraestructura real en otros niveles |
| Preparacion para CI/CD | 6/10 | Workflow y gates escritos; MySQL real aprobado; workflow remoto pendiente de publicacion/ejecucion |
| Resiliencia ante Fallos (Edge Cases) | 8/10 | Rollback, fronteras, reservas repetidas, zonas horarias y cantidades no enteras probadas |

# ESTADO DE CALIDAD (QUALITY READINESS)

| Estado | Evaluacion honesta |
|---|---|
| Unit Test Ready | ✅ Listo: 106 pruebas ejecutadas; hallazgos corregidos con regresiones |
| Integration Ready | ✅ Listo para MySQL nativo efimero: 53 pruebas de integracion aprobadas; ruta Testcontainers no ejecutada |
| System / E2E Ready | ✅ Listo en entorno local controlado; despliegue y carga productiva pendientes |
| UAT / Business Ready | ❌ No listo para aprobacion final: BDD automatizado aprobado; falta firma de negocio en inventory_uat_approval.md |

No se declara Enterprise Ready, cero flakiness ni aprobacion al 100 %. La entrega
es un plan ejecutable con pruebas y evidencias. Los tres defectos fueron corregidos;
MySQL nativo y los cuatro niveles automatizados estan aprobados. CI remoto y la firma de negocio se informan por separado.


Actualizacion de correcciones: QA-INV-01 (liberacion idempotente), QA-INV-02
(fecha aware/naive y normalizacion ORM), QA-INV-03 (stock entero estricto, sin bool)
estan corregidos. Regresiones adicionales: `tests/unit/inventory/test_regresiones_auditoria.py`
(53 casos) y `test_reserva_orm_aware_y_liberacion_idempotente` en integracion.
El acta de revision humana esta en `inventory_uat_approval.md`.
