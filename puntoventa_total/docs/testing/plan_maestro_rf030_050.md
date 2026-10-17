# 1. DIAGNÓSTICO ARQUITECTÓNICO Y DE TESTABILIDAD DEL MÓDULO

## 1.1 Lenguaje, Runtime y Framework detectado

Alcance: RF-030..050, módulos 3.4 Pedidos en Línea, 3.5 Clientes Frecuentes/Promociones y 3.6 Reportes/Administración.
Python, Django, monolito modular con dominio/aplicación/infraestructura/presentación. Se revisó el código antes de seleccionar herramientas.
Perfil declarado: Python 3.11.16, Django 5.0.6, Celery 5.4.0. Perfil QA: Python 3.14.7, Django 6.1.2, Celery 5.6.3.
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

## 1.3 Deuda Técnica o Problemas de Testabilidad

Se corrigieron carrito sin dueño, seguimiento ajeno, checkout sin hora/datos, cancelación durante preparación,
reservas que vencían antes del recojo, historial propio inaccesible, descuento de frecuencia desconectado,
errores de fechas en promociones/reportes, falta de combo y edición web, costo histórico recalculado con catálogo actual,
pérdida del descuento global al cargar la venta, ausencia de auditoría transversal y sesiones de usuarios desactivados.

Políticas conservadas o explicitadas:

- Fidelización existente: recurrente hasta 7 días = 10%; OCASIONAL = 5%; requiere una promoción de fidelización vigente.
  El código clasifica como OCASIONAL también intervalos superiores a 30 días: no se introduce un corte no confirmado.
  No hubo confirmación de otra política. Dos compras del mismo día cuentan como recurrentes; una sola no proporciona frecuencia.
- Combo: productos/cantidades definidos por el administrador y precio final del paquete. Solo paquetes completos.
  Beneficio global = mejor opción entre combo/fidelización, descontando lo aplicado a líneas para evitar acumulación accidental.
- Promoción: Borrador → Activa → Vencida / Cancelada. PROGRAMADA se conserva internamente como borrador con calendario;
  FINALIZADA se muestra Vencida. El fin es exclusivo: en ese instante ya no aplica.
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
| Performance | k6 2.3.0 | CLI k6 | Cobro <100 ms p95; reportes/pedidos <500 ms p95 | Windows: `rtk proxy python scripts/qa_download_tools.py k6` |
| UAT | pytest-bdd 9.0.0 | CLI pytest | Doce escenarios de negocio entre los tres módulos | requirements/testing.txt |
| Servicios | Celery 5.4.0, redis 5.0.4 | Redis y SMTP | Worker, recuperación de avisos y entrega SMTP | requirements/testing.txt; Redis portable: `rtk proxy python scripts/qa_download_tools.py redis` |

[Instalación oficial de Docker Desktop en Windows](https://docs.docker.com/desktop/setup/install/windows-install/).
Con el instalador descargado, PowerShell: `Start-Process '.\Docker Desktop Installer.exe' -Wait -ArgumentList 'install'`.
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
    |   |-- integration/{test_pedidos_online,test_pedidos_online_mysql,test_rf038_050}.py
    |   |-- integration/{test_smtp_real,test_redis_celery_real}.py
    |   |-- system/{test_pedidos_online_playwright,test_rf038_050_playwright}.py
    |   |-- system/{test_k6_pos_real,test_pedidos_online_k6,test_rf038_050_k6}.py
    |   |-- performance/{k6_cobro,k6_pedidos,k6_reportes}.js
    |   `-- uat/
    |       |-- features/{pedidos_online,clientes_promociones_admin}.feature
    |       `-- {test_pedidos_online_bdd,test_clientes_promociones_admin_bdd}.py
    |-- scripts/{qa_inventory_mysql,qa_inventory_mysql_native,qa_redis_native}.py
    |-- scripts/qa_build_rf030_050_report.py
    |-- docs/testing/plan_maestro_rf030_050.md
    `-- reports/  (JUnit, cobertura, traces, k6; ignorado por Git)
```

# 4. NIVEL 1: PRUEBAS UNITARIAS (UNIT TESTING)

## 4.1 Qué se evalúa en este módulo

Estados, cantidades, hora de recojo, frecuencia, combos completos/incompletos, vencimiento exacto,
reconfirmación sin nueva reserva y propiedad de conservación de centavos al distribuir descuentos.

## 4.2 Aplicativos y Librerías a usar

pytest, unittest.mock e Hypothesis. Las propiedades monetarias no usan BD, navegador ni red.

## 4.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
rtk proxy .venv-rf030-050/Scripts/python.exe -m pytest tests/unit -q -p no:cacheprovider --cov=src --cov-fail-under=0 --cov-report=json:reports/audit_unit_coverage.json --junitxml=reports/rf-unit.xml
rtk proxy .venv-rf030-050/Scripts/python.exe scripts/qa_unit_gate.py
```

El gate mide dominio y aplicación a partir de pruebas unitarias, mínimo 80%; no confunde cobertura integrada con unitaria.

## 4.4 Código Completo del Test Unitario

**Archivo: `tests/unit/domain/test_pedidos_online.py`**

```python
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate
from src.modules.orders.domain.entities.pedido import Pedido
from src.modules.orders.domain.enums.estado_pedido import EstadoPedido
from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException
from src.modules.orders.application.use_cases.confirmar_pedido import ConfirmarPedido
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("estado", list(EstadoPedido))
def test_cancelacion_solo_borrador_o_pendiente(estado):
    pedido = PedidoAggregate(Pedido(cliente_nombre="Ana", estado=estado))
    if estado in (EstadoPedido.BORRADOR, EstadoPedido.CONFIRMADO):
        pedido.cancelar()
        assert pedido.pedido.estado == EstadoPedido.CANCELADO
    else:
        with pytest.raises(PedidoException):
            pedido.cancelar()
        assert pedido.pedido.estado == estado


@pytest.mark.parametrize("cantidad", [0, -1, True, 1.5])
def test_cantidad_invalida_no_modifica_linea_existente(cantidad):
    pedido = PedidoAggregate(Pedido(cliente_nombre="Ana"))
    pedido.agregar_producto("p1", "Pan", 3, Monto(Decimal("2")))
    with pytest.raises(PedidoException):
        pedido.agregar_producto("p1", "Pan", cantidad, Monto(Decimal("2")))
    assert pedido.lineas[0].cantidad == 3


@pytest.mark.parametrize("segundos", [1, 59])
def test_franja_rechaza_segundos(segundos):
    hora = (datetime.now(timezone.utc) + timedelta(days=1)).replace(minute=30, second=segundos, microsecond=0)
    with pytest.raises(PedidoException):
        Pedido(cliente_nombre="Ana").asignar_hora_recojo(hora)


def test_reconfirmacion_no_reserva_stock_otra_vez():
    pedido = PedidoAggregate(Pedido(cliente_nombre="Ana"))
    pedido.agregar_producto("p1", "Pan", 2, Monto(Decimal("2")))
    pedido.confirmar()
    repo, inventario = Mock(), Mock()
    repo.buscar_por_id.return_value = pedido
    with pytest.raises(PedidoException):
        ConfirmarPedido(repo, inventario).ejecutar(str(pedido.pedido.id))
    inventario.reservar.assert_not_called()


def test_pedido_confirmado_no_admite_cambios():
    pedido = PedidoAggregate(Pedido(cliente_nombre="Ana"))
    pedido.agregar_producto("p1", "Pan", 2, Monto(Decimal("2")))
    pedido.confirmar()
    with pytest.raises(PedidoException):
        pedido.agregar_producto("p1", "Pan", 1, Monto(Decimal("2")))


def test_beat_conserva_recuperacion_de_emails_pendientes():
    from config.celery import app
    assert app.conf.beat_schedule["pedidos-listos-pendientes"]["task"] == "src.modules.orders.tasks.reintentar_notificaciones"
    assert "verificar-stock-minimo-diario" in app.conf.beat_schedule
```

**Archivo: `tests/unit/application/test_confirmar_pedido.py`**

```python
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.modules.orders.application.use_cases.confirmar_pedido import ConfirmarPedido
from src.modules.orders.domain.aggregates.pedido_aggregate import PedidoAggregate
from src.modules.orders.domain.entities.pedido import Pedido
from src.modules.orders.domain.enums.estado_pedido import EstadoPedido
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def _pedido() -> PedidoAggregate:
    agregado = PedidoAggregate(pedido=Pedido(numero="P1", cliente_nombre="Ana"))
    agregado.agregar_producto("p1", "Pizza", 1, Monto(Decimal("40.00")))
    return agregado


def test_confirmar_reserva_stock_y_cambia_estado():
    repo, inventario = MagicMock(), MagicMock()
    repo.buscar_por_id.return_value = _pedido()
    inventario.reservar.return_value = "reserva-1"

    # el repositorio fake debe devolver el agregado al guardar
    repo.guardar.side_effect = lambda agregado: agregado

    resultado = ConfirmarPedido(repo, inventario).ejecutar("p1-id")

    assert resultado.estado == EstadoPedido.CONFIRMADO.value
    inventario.reservar.assert_called_once()


def test_pedido_vacio_no_se_confirma():
    from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException

    repo, inventario = MagicMock(), MagicMock()
    repo.buscar_por_id.return_value = PedidoAggregate(pedido=Pedido(numero="P2", cliente_nombre="Ana"))

    with pytest.raises(PedidoException):
        ConfirmarPedido(repo, inventario).ejecutar("p2-id")
```

**Archivo: `tests/unit/domain/test_clientes_promociones_reportes.py`**

```python
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from hypothesis import given, settings, strategies as st

from src.modules.customers.domain.services.frecuencia_compra import FrecuenciaCompra
from src.modules.promotions.domain.entities.promocion import Promocion
from src.modules.promotions.domain.value_objects.descuento import Descuento
from src.modules.sales.domain.entities.detalle_venta import DetalleVenta
from src.modules.reporting.domain.value_objects.utilidad_historica import agrupar_utilidad
from src.shared.domain.value_objects.monto import Monto
from src.shared.domain.exceptions.domain_exception import DomainException

pytestmark = pytest.mark.unit


def test_compras_del_mismo_dia_son_recurrentes():
    ahora = datetime.now(timezone.utc)
    dias = FrecuenciaCompra.dias_entre_compras([ahora, ahora])
    assert FrecuenciaCompra.clasificar(dias) == "FRECUENTE"
    assert FrecuenciaCompra.clasificar(FrecuenciaCompra.dias_entre_compras([ahora])) == "SIN_DATOS"


@pytest.mark.parametrize("dias,esperado", [(7, "FRECUENTE"), (7.01, "OCASIONAL"), (30, "OCASIONAL")])
def test_fronteras_fidelizacion(dias, esperado):
    assert FrecuenciaCompra.clasificar(dias) == esperado


def test_combo_requiere_todos_los_productos_y_precio_congelado():
    a, b = str(uuid4()), str(uuid4())
    promo = Promocion(nombre="Combo desayuno", tipo="COMBO", estado="ACTIVA",
        descuento=Descuento(Decimal("12"), "COMBO"),
        componentes=[{"producto_id": a, "cantidad": 1}, {"producto_id": b, "cantidad": 1}])
    pan = DetalleVenta(producto_id=a, producto_nombre="Pan", cantidad=3, precio_unitario=Monto(10))
    jugo = DetalleVenta(producto_id=b, producto_nombre="Jugo", cantidad=2, precio_unitario=Monto(5))
    assert promo.descuento_combo([pan, jugo]).valor == Decimal("6")
    assert promo.descuento_combo([pan]).valor == 0


@pytest.mark.parametrize("componentes", [[], [{"producto_id": "no-uuid", "cantidad": 1}], ["malformado"]])
def test_combo_invalido_no_se_construye(componentes):
    with pytest.raises(DomainException):
        Promocion(nombre="Combo", tipo="COMBO", componentes=componentes)


def test_promocion_no_vigente_en_instante_final():
    fin = datetime.now(timezone.utc)
    promo = Promocion(nombre="10%", estado="ACTIVA", vigencia_hasta=fin)
    assert not promo.esta_vigente(fin)


@given(st.integers(min_value=1, max_value=10000), st.integers(min_value=0, max_value=100), st.integers(min_value=2, max_value=20))
@settings(derandomize=True, deadline=None)
def test_utilidad_conserva_total_de_venta_al_distribuir_centavos(centavos, descuento, cantidad):
    base = Decimal(centavos) / 100
    total = (base * (100 - descuento) / 100).quantize(Decimal("0.01"))
    lineas = [{"venta_id": "v1", "producto_id": str(i), "producto_nombre": f"Pan {i}",
               "cantidad": 1, "importe": base / cantidad, "total_venta": total, "costo_unitario": Decimal("0.1")}
              for i in range(cantidad)]
    filas = agrupar_utilidad(lineas)
    assert sum(Decimal(str(f["ingresos"])) for f in filas) == total
    assert all(f["ingresos"] >= 0 for f in filas)


def test_utilidad_antigua_declara_costo_desconocido():
    filas = agrupar_utilidad([{"venta_id": "v", "producto_id": "pan", "producto_nombre": "Pan",
        "cantidad": 1, "importe": 10, "total_venta": 10, "costo_unitario": None}])
    assert filas[0]["estimado"] is True
```

**Archivo: `tests/unit/application/test_beneficios_venta.py`**

```python
from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.modules.sales.application.use_cases.preparar_beneficios import PrepararBeneficiosVenta
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.entities.pago import Pago
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


def venta():
    agregado = VentaAggregate(Venta(numero_ticket="T-BENEFICIO", cajero_id="cajero"))
    agregado.agregar_producto("pan", "Pan", 2, Monto(10))
    agregado.calcular_totales()
    return agregado


def test_beneficio_se_aplica_antes_del_pago_sin_compuesto():
    agregado, puerto = venta(), Mock()
    puerto.descuento_venta.return_value = Monto(2)
    caso = PrepararBeneficiosVenta(Mock(), puerto)
    caso.aplicar(agregado)
    caso.aplicar(agregado)
    assert agregado.descuento_venta_pct == Decimal("10")
    assert agregado.venta.total == 18


def test_pago_iniciado_congela_el_beneficio():
    agregado, puerto = venta(), Mock()
    agregado.registrar_pago(Pago.efectivo(str(agregado.venta.id), Monto(1)))
    PrepararBeneficiosVenta(Mock(), puerto).aplicar(agregado)
    puerto.descuento_venta.assert_not_called()
    assert agregado.venta.total == 20


def test_beneficio_superior_al_subtotal_es_rechazado():
    agregado, puerto = venta(), Mock()
    puerto.descuento_venta.return_value = Monto(21)
    with pytest.raises(ValidationException):
        PrepararBeneficiosVenta(Mock(), puerto).aplicar(agregado)
    assert agregado.venta.total == 20
```

# 5. NIVEL 2: PRUEBAS DE INTEGRACIÓN (INTEGRATION TESTING)

## 5.1 Qué se evalúa en este módulo

Registro/login, stock, persistencia, pagos, historial, fidelización automática, promociones, rangos,
utilidad estable, edición, permisos, revocación de sesión y rollback si la auditoría falla.
Dos escritores compiten por confirmar/cancelar el mismo pedido. La suite completa también enfrenta inventario y secuencias.

## 5.2 Aplicativos y Librerías a usar

MySQL 8.4.3/InnoDB efímero en Testcontainers; Redis para worker real; SMTP de prueba por socket.
Los tests con locmem demuestran selección de destinatario y flujo, no envío a un proveedor externo.
SQLite solo sirve para iteración: no demuestra SELECT FOR UPDATE ni carreras de InnoDB.

## 5.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
rtk proxy docker version
rtk proxy .venv-rf030-050/Scripts/python.exe scripts/qa_inventory_mysql.py tests/integration --junitxml=reports/rf-integration.xml
```

Para incluir Redis en ese comando, definir QA_REDIS_URL con una instancia exclusiva de QA. CI ya la proporciona.
Alternativa nativa **aislada**, disponible en este equipo sin Docker; no conecta a la BD del negocio:

```powershell
rtk proxy .venv/Scripts/python.exe scripts/qa_inventory_mysql_native.py --basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --target tests/integration/test_rf038_050.py --target tests/integration/test_pedidos_online.py --target tests/integration/test_pedidos_online_mysql.py --report-prefix rf-integration
```

## 5.4 Código Completo del Test de Integración

**Archivo: `tests/integration/test_pedidos_online.py`**

```python
"""RF-030..037: HTTP, ORM, stock y correo reales (MySQL en el gate)."""
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core import mail
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel
from src.modules.inventory.infrastructure.persistence.django_models.lote_model import LoteModel
from src.modules.inventory.infrastructure.persistence.django_models.reserva_model import ReservaModel
from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
from src.modules.orders.infrastructure.tasks.enviar_notificacion_pedido import run

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
PASSWORD = "Panaderia!Segura#725"


def registrar(client, email="ana@example.com", dni="12345678"):
    return client.post(reverse("customers:registro"), {
        "nombre": "Ana Cliente", "dni": dni, "email": email, "telefono": "987654321",
        "password": PASSWORD, "password_confirmacion": PASSWORD,
    })


def iniciar(client, email="ana@example.com", password=PASSWORD):
    return client.post(reverse("identity:login"), {"username": email, "password": password})


def producto():
    p = ProductoModel.objects.create(id=uuid.uuid4(), nombre="Pan de recojo", codigo_barras="7751234567890",
                                     costo=Decimal("1"), precio_venta=Decimal("2"), estado="ACTIVO")
    ExistenciaModel.objects.create(id=uuid.uuid4(), producto_id=p.id, cantidad=10, reservada=0)
    LoteModel.objects.create(id=uuid.uuid4(), producto_id=p.id, numero_lote="PEDIDOS-1", cantidad_inicial=10,
                             cantidad_restante=10, fecha_recepcion=date.today())
    return p


def carrito(client):
    assert registrar(client).status_code == 302
    assert iniciar(client).status_code == 302
    p = producto()
    assert client.post(reverse("orders:agregar", args=[p.id]), {"cantidad": 2}).status_code == 302
    return PedidoModel.objects.get(), p


def confirmar(client):
    hora = (timezone.localtime() + timedelta(days=1)).replace(minute=30, second=0, microsecond=0)
    return client.post(reverse("orders:checkout"), {
        "cliente_nombre": "Ana Recojo", "cliente_dni": "12345678", "cliente_telefono": "987654321",
        "hora_recojo": hora.strftime("%Y-%m-%dT%H:%M"), "modalidad": "RECOJO", "observaciones": "Sin bolsa",
    })


def test_registro_publico_login_email_y_password_hash(client):
    assert registrar(client, "ANA@EXAMPLE.COM").status_code == 302
    usuario = UsuarioModel.objects.get()
    assert usuario.rol == "CLIENTE"
    assert usuario.email == "ana@example.com"
    assert usuario.password_hash != PASSWORD
    assert ClienteModel.objects.get().usuario_id == usuario.id
    assert iniciar(client, "ANA@example.com").status_code == 302
    assert client.session["usuario_id"] == str(usuario.id)


@pytest.mark.parametrize("cambio", [
    {"dni": "abc"}, {"email": "invalido"}, {"telefono": ""}, {"telefono": "abcdefghi"},
    {"password": "123", "password_confirmacion": "123"}, {"password_confirmacion": "otra"},
])
def test_registro_invalido_no_crea_cuentas(client, cambio):
    datos = {"nombre": "Ana", "dni": "12345678", "email": "ana@example.com", "telefono": "987654321",
             "password": PASSWORD, "password_confirmacion": PASSWORD}
    datos.update(cambio)
    respuesta = client.post(reverse("customers:registro"), datos)
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    assert UsuarioModel.objects.count() == ClienteModel.objects.count() == 0


def test_email_duplicado_y_dni_duplicado_no_dejan_cuentas_huerfanas(client):
    registrar(client)
    assert registrar(client, "ANA@EXAMPLE.COM", "87654321").status_code == 200
    assert registrar(client, "otra@example.com").status_code == 200
    assert UsuarioModel.objects.count() == ClienteModel.objects.count() == 1


def test_login_incorrecto_no_crea_sesion(client):
    registrar(client)
    assert iniciar(client, password="incorrecta").status_code == 200
    assert "usuario_id" not in client.session
    assert UsuarioModel.objects.get().intentos_fallidos == 1


def test_carrito_confirmacion_datos_recojo_y_cancelacion_libera_stock(client):
    pedido, p = carrito(client)
    assert pedido.cliente_id == UsuarioModel.objects.get().id
    assert client.get(reverse("orders:carrito")).context["total"] == 4
    assert confirmar(client).status_code == 302
    pedido.refresh_from_db()
    assert pedido.estado == "CONFIRMADO"
    assert pedido.cliente_nombre == "Ana Recojo"
    assert pedido.cliente_email == "ana@example.com"
    assert pedido.hora_recojo is not None
    assert pedido.observaciones == "Sin bolsa"
    assert "pedido_web" not in client.session
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 2
    assert ReservaModel.objects.get().permanente
    respuesta = client.get(reverse("orders:detalle", args=[pedido.id]))
    assert b"Pendiente" in respuesta.content
    assert client.post(reverse("orders:cancelar", args=[pedido.id])).status_code == 302
    pedido.refresh_from_db()
    assert pedido.estado == "CANCELADO"
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 0


@pytest.mark.parametrize("estado", ["EN_PREPARACION", "LISTO", "ENTREGADO", "CANCELADO"])
def test_cancelacion_tardia_no_modifica_stock(client, estado):
    pedido, p = carrito(client)
    confirmar(client)
    PedidoModel.objects.filter(pk=pedido.id).update(estado=estado)
    client.post(reverse("orders:cancelar", args=[pedido.id]))
    pedido.refresh_from_db()
    assert pedido.estado == estado
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 2


def test_aislamiento_cliente_y_permisos_cocina(client):
    pedido, _ = carrito(client)
    otro = Client()
    registrar(otro, "otro@example.com", "87654321")
    iniciar(otro, "otro@example.com")
    for ruta in ("detalle", "cancelar"):
        assert otro.post(reverse(f"orders:{ruta}", args=[pedido.id])).status_code == 404
    assert otro.get(reverse("orders:seguimiento"), {"numero": pedido.numero}).status_code == 404
    session = otro.session
    session["pedido_web"] = str(pedido.id)
    session.save()
    assert otro.get(reverse("orders:checkout")).status_code == 404
    assert otro.get(reverse("orders:carrito")).status_code == 404
    respuesta = otro.post(reverse("orders:cambiar_estado", args=[pedido.id]), {"estado": "LISTO"})
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("catalog:catalogo")
    pedido.refresh_from_db()
    assert pedido.estado == "BORRADOR"


def test_preparar_listo_notifica_una_vez_y_entrega_descuenta_stock(client, django_capture_on_commit_callbacks):
    pedido, p = carrito(client)
    confirmar(client)
    session = client.session
    session["rol"] = "CAJERO"
    session.save()
    for estado in ("EN_PREPARACION", "LISTO"):
        with django_capture_on_commit_callbacks(execute=True):
            assert client.post(reverse("orders:cambiar_estado", args=[pedido.id]), {"estado": estado}).status_code == 302
    pedido.refresh_from_db()
    assert pedido.estado == "LISTO"
    assert pedido.notificado_listo
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["ana@example.com"]
    assert pedido.numero in mail.outbox[0].subject
    assert run(str(pedido.id)) is True
    assert len(mail.outbox) == 1
    client.post(reverse("orders:cambiar_estado", args=[pedido.id]), {"estado": "ENTREGADO"})
    pedido.refresh_from_db()
    assert pedido.estado == "ENTREGADO"
    stock = ExistenciaModel.objects.get(producto_id=p.id)
    assert (stock.cantidad, stock.reservada) == (8, 0)
    assert LoteModel.objects.get(producto_id=p.id).cantidad_restante == 8


@pytest.mark.parametrize("hora", ["", "2000-01-01T10:00", "2099-01-01T10:15", "2099-01-01T10:30:01"])
def test_checkout_rechaza_hora_invalida_sin_reservar(client, hora):
    pedido, p = carrito(client)
    respuesta = client.post(reverse("orders:checkout"), {"cliente_nombre": "Ana", "modalidad": "RECOJO", "hora_recojo": hora})
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    pedido.refresh_from_db()
    assert pedido.estado == "BORRADOR"
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 0


def test_cantidad_acumulada_no_supera_disponible(client):
    pedido, p = carrito(client)
    client.post(reverse("orders:agregar", args=[p.id]), {"cantidad": 9})
    assert pedido.detalles.get().cantidad == 2
    client.post(reverse("orders:agregar", args=[p.id]), {"cantidad": -1})
    assert pedido.detalles.get().cantidad == 2


def test_confirmacion_revierte_todas_las_reservas_si_una_linea_se_agota(client):
    pedido, p = carrito(client)
    segundo = ProductoModel.objects.create(id=uuid.uuid4(), nombre="Otro pan", codigo_barras="7751234567891",
                                           costo=1, precio_venta=2, estado="ACTIVO")
    stock = ExistenciaModel.objects.create(id=uuid.uuid4(), producto_id=segundo.id, cantidad=5)
    client.post(reverse("orders:agregar", args=[segundo.id]), {"cantidad": 2})
    stock.cantidad = 0
    stock.save()
    assert confirmar(client).status_code == 200
    pedido.refresh_from_db()
    assert pedido.estado == "BORRADOR"
    assert pedido.hora_recojo is None
    assert ReservaModel.objects.count() == 0
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 0


def test_entrega_antes_de_listo_no_consume_stock(client):
    pedido, p = carrito(client)
    confirmar(client)
    sesion = client.session
    sesion["rol"] = "CAJERO"
    sesion.save()
    client.post(reverse("orders:cambiar_estado", args=[pedido.id]), {"estado": "ENTREGADO"})
    pedido.refresh_from_db()
    assert pedido.estado == "CONFIRMADO"
    stock = ExistenciaModel.objects.get(producto_id=p.id)
    assert (stock.cantidad, stock.reservada) == (10, 2)


def test_reserva_confirmada_no_expira_antes_del_recojo(client):
    from src.modules.inventory.infrastructure.factories import construir_reserva_repository
    pedido, _ = carrito(client)
    confirmar(client)
    ReservaModel.objects.update(expira_en=timezone.now() - timedelta(days=1))
    repo = construir_reserva_repository()
    assert repo.buscar_por_id(ReservaModel.objects.get().id).activa
    assert repo.listar_activas_expiradas() == []


def test_producto_sin_stock_se_confirma_sin_reserva(client):
    pedido, p = carrito(client)
    # Un servicio no requiere existencia física.
    servicio = ProductoModel.objects.create(id=uuid.uuid4(), nombre="Personalización", codigo_barras="7751234567892",
                                            costo=1, precio_venta=2, estado="ACTIVO", requiere_stock=False)
    client.post(reverse("orders:agregar", args=[servicio.id]), {"cantidad": 1})
    assert confirmar(client).status_code == 302
    assert pedido.detalles.get(producto_id=servicio.id).requiere_stock is False
    assert ReservaModel.objects.count() == 1
    assert ReservaModel.objects.get().producto_id == p.id


def test_cambios_requieren_post_y_csrf(client):
    pedido, _ = carrito(client)
    assert client.get(reverse("orders:cancelar", args=[pedido.id])).status_code == 405
    seguro = Client(enforce_csrf_checks=True)
    seguro.cookies = client.cookies
    assert seguro.post(reverse("orders:cancelar", args=[pedido.id])).status_code == 403
    pedido.refresh_from_db()
    assert pedido.estado == "BORRADOR"


def test_email_no_enviado_queda_pendiente_y_se_recupera(client, monkeypatch):
    from src.modules.orders.infrastructure.notifications.email_notifier import EmailNotifier
    pedido, _ = carrito(client)
    confirmar(client)
    PedidoModel.objects.filter(pk=pedido.id).update(estado="LISTO")
    with monkeypatch.context() as contexto:
        contexto.setattr(EmailNotifier, "_enviar", lambda *args: False)
        assert run(str(pedido.id)) is False
    pedido.refresh_from_db()
    assert not pedido.notificado_listo
    assert run(str(pedido.id)) is True
    pedido.refresh_from_db()
    assert pedido.notificado_listo
    assert mail.outbox[-1].to == ["ana@example.com"]
```

**Archivo: `tests/integration/test_pedidos_online_mysql.py`**

```python
"""Dos solicitudes simultáneas al mismo pedido: InnoDB sin dobles reservas."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import connection, close_old_connections, connections, transaction

from tests.integration.test_pedidos_online import carrito
from src.modules.orders.application.use_cases.confirmar_pedido import ConfirmarPedido
from src.modules.orders.application.use_cases.cancelar_pedido import CancelarPedido
from src.modules.orders.domain.exceptions.pedido_exceptions import PedidoException
from src.modules.orders.infrastructure.factories import construir_inventario_port, construir_pedido_repository
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel
from src.modules.inventory.infrastructure.persistence.django_models.reserva_model import ReservaModel

pytestmark = [pytest.mark.integration, pytest.mark.django_db(transaction=True),
              pytest.mark.skipif(connection.vendor != "mysql", reason="Requiere MySQL/InnoDB real")]


@pytest.mark.parametrize("accion", ["confirmar", "cancelar"])
def test_dos_escritores_sobre_un_pedido(client, accion):
    pedido, producto = carrito(client)
    if accion == "cancelar":
        ConfirmarPedido(construir_pedido_repository(), construir_inventario_port(), uow=transaction.atomic()).ejecutar(str(pedido.id))
    barrera = Barrier(2, timeout=10)

    def ejecutar():
        close_old_connections()
        try:
            barrera.wait()
            caso = ConfirmarPedido if accion == "confirmar" else CancelarPedido
            caso(construir_pedido_repository(), construir_inventario_port(), uow=transaction.atomic()).ejecutar(str(pedido.id))
            return "aceptado"
        except PedidoException:
            return "rechazado"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(ejecutar) for _ in range(2)]
        assert sorted(f.result(timeout=25) for f in futuros) == ["aceptado", "rechazado"]
    pedido.refresh_from_db()
    assert pedido.estado == ("CONFIRMADO" if accion == "confirmar" else "CANCELADO")
    stock = ExistenciaModel.objects.get(producto_id=producto.id)
    assert stock.cantidad == 10
    assert stock.reservada == (2 if accion == "confirmar" else 0)
    assert ReservaModel.objects.filter(referencia=f"PEDIDO:{pedido.numero}").count() == 1
```

**Archivo: `tests/integration/test_rf038_050.py`**

```python
import json
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.infrastructure.factories import construir_repositorio, construir_hasher
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.promotions.infrastructure.persistence.django_models.promocion_model import PromocionModel
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.modules.sales.infrastructure.persistence.django_models.detalle_venta_model import DetalleVentaModel
from src.modules.sales.infrastructure.persistence.django_models.pago_model import PagoModel
from src.modules.catalog.infrastructure.persistence.django_models.categoria_model import CategoriaModel
from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
from src.modules.reporting.infrastructure.factories import construir_reporte_repository
from src.modules.promotions.infrastructure.tasks.actualizar_estado_promociones import run as actualizar_promos
from tests.integration.test_pedidos_online import producto

pytestmark = [pytest.mark.integration, pytest.mark.django_db]
PASSWORD = "Clave!Arquitectura#275"


def staff(client, rol="ADMINISTRADOR"):
    username = "qa_" + uuid4().hex[:12]
    usuario = CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(
        UsuarioInputDTO(username=username, password=PASSWORD, nombre_completo="Personal QA", rol=rol))
    client.force_login(User.objects.create_user(username=username))
    session = client.session
    session["rol"], session["usuario_id"] = rol, usuario.id
    session.save()
    return usuario


def compra(cliente, total=10, dias=0, estado="PAGADA", producto_id=None, costo=3):
    p = producto_id or uuid4()
    venta = VentaModel.objects.create(id=uuid4(), numero_ticket="T" + uuid4().hex[:15], cajero_id=uuid4(),
        cliente_id=cliente.id, estado=estado, subtotal=total, total=total, moneda="PEN")
    VentaModel.objects.filter(pk=venta.id).update(fecha_creacion=timezone.now() - timedelta(days=dias))
    DetalleVentaModel.objects.create(id=uuid4(), venta=venta, producto_id=p, producto_nombre="Pan auditado",
        cantidad=1, precio_unitario=total, subtotal=total, total=total, costo_unitario=costo)
    PagoModel.objects.create(id=uuid4(), venta=venta, metodo="EFECTIVO", monto=total)
    return venta


def promo_payload(tipo="PORCENTAJE", **extra):
    datos = {"nombre": "Promo QA", "tipo": tipo, "descuento_valor": "10", "accion": "crear"}
    datos.update(extra)
    return datos


def test_rf038_cajero_registra_dni_telefono_sin_asociarse_como_dueno(client):
    staff(client, "CAJERO")
    respuesta = client.post(reverse("customers:registro"), {"nombre": "Cliente frecuente", "dni": "12345678", "telefono": "987654321"})
    assert respuesta.status_code == 302
    cliente = ClienteModel.objects.get()
    assert cliente.usuario_id is None
    assert cliente.dni == "12345678"
    assert cliente.telefono == "987654321"
    assert AuditoriaModel.objects.filter(entidad="ClienteModel", entidad_id=str(cliente.id), accion="CREAR").exists()


def test_rf039_y_rf043_historial_propio_suma_solo_pagadas(client):
    usuario = staff(client, "CLIENTE")
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Ana", usuario_id=usuario.id)
    compra(cliente, total=10, dias=2)
    compra(cliente, total=20)
    compra(cliente, total=999, estado="ANULADA")
    respuesta = client.get(reverse("customers:historial", args=[cliente.id]))
    assert respuesta.status_code == 200
    assert respuesta.context["historial"]["cantidad"] == 2
    assert respuesta.context["historial"]["total_gastado"] == 30
    assert respuesta.context["frecuencia"]["clasificacion"] == "FRECUENTE"
    otro = ClienteModel.objects.create(id=uuid4(), nombre="Ajeno", usuario_id=uuid4())
    assert client.get(reverse("customers:historial", args=[otro.id])).status_code == 403


@pytest.mark.parametrize("tipo", ["PORCENTAJE", "NX1", "COMBO"])
def test_rf041_admin_crea_tipos_reales_y_edita(client, tipo):
    staff(client)
    p = producto()
    extra = {"producto_id": str(p.id)} if tipo == "NX1" else {}
    if tipo == "NX1":
        extra["descuento_valor"] = "0"
    if tipo == "COMBO":
        from src.modules.catalog.models import ProductoModel
        segundo = ProductoModel.objects.create(id=uuid4(), nombre="Jugo", codigo_barras="7751234567891", costo=1, precio_venta=5, estado="ACTIVO")
        extra["componentes"] = json.dumps([{"producto_id": str(p.id), "cantidad": 1}, {"producto_id": str(segundo.id), "cantidad": 1}])
    respuesta = client.post(reverse("promotions:crear"), promo_payload(tipo, **extra))
    assert respuesta.status_code == 302
    promocion = PromocionModel.objects.get()
    assert promocion.tipo == tipo
    assert client.get(reverse("promotions:editar", args=[promocion.id])).status_code == 200
    respuesta = client.post(reverse("promotions:editar", args=[promocion.id]), promo_payload(tipo, nombre="Editada", **extra))
    assert respuesta.status_code == 302
    promocion.refresh_from_db()
    assert promocion.nombre == "Editada"


@pytest.mark.parametrize("extra", [{"descuento_valor": "150"}, {"vigencia_desde": "mal"}, {"vigencia_hasta": "2099-01-01T10:00"}])
def test_rf041_042_entrada_invalida_se_muestra_sin_500(client, extra):
    staff(client)
    respuesta = client.post(reverse("promotions:crear"), promo_payload(**extra))
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    assert PromocionModel.objects.count() == 0


def test_rf042_programada_ya_vencida_no_se_activa_temporalmente(client):
    staff(client)
    ahora = timezone.localtime()
    datos = promo_payload(vigencia_desde=(ahora + timedelta(days=1)).isoformat(), vigencia_hasta=(ahora + timedelta(days=2)).isoformat())
    assert client.post(reverse("promotions:crear"), datos).status_code == 302
    promocion = PromocionModel.objects.get()
    assert promocion.estado == "PROGRAMADA"
    PromocionModel.objects.filter(pk=promocion.id).update(vigencia_desde=ahora - timedelta(days=2), vigencia_hasta=ahora - timedelta(days=1))
    resultado = actualizar_promos()
    assert resultado == {"activadas": 0, "finalizadas": 1}
    promocion.refresh_from_db()
    assert promocion.estado == "FINALIZADA"
    assert client.get(reverse("promotions:activas"), HTTP_ACCEPT="application/json").json() == {"promociones": []}


@pytest.mark.parametrize("vista", ["ventas", "utilidad", "productos"])
@pytest.mark.parametrize("datos", [{"desde": "mal"}, {"desde": "2026-05-02", "hasta": "2026-05-01"}])
def test_rf045_filtros_invalidos_retornan_400(client, vista, datos):
    staff(client)
    assert client.get(reverse(f"reporting:{vista}"), datos).status_code == 400


def test_rf044_047_reportes_excluyen_anuladas_y_conservan_costo_historico(client):
    staff(client)
    p = producto()
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Ana")
    compra(cliente, total=20, producto_id=p.id, costo=3)
    compra(cliente, total=999, estado="ANULADA", producto_id=p.id)
    p.costo = 100
    p.save()
    hoy = timezone.localdate()
    repo = construir_reporte_repository()
    assert repo.ventas_por_dia(hoy, hoy)[0]["total"] == 20
    assert repo.totales_por_metodo_pago(hoy, hoy) == {"EFECTIVO": 20.0}
    assert repo.productos_mas_vendidos(hoy, hoy)[0]["unidades"] == 1
    utilidad = repo.utilidad_por_producto(hoy, hoy)[0]
    assert utilidad["costo"] == 3
    assert utilidad["utilidad"] == 17
    for vista in ("dashboard", "ventas", "utilidad", "productos"):
        assert client.get(reverse(f"reporting:{vista}")).status_code == 200


def test_rf048_crear_editar_desactivar_y_revocar_sesion(client):
    staff(client)
    payload = {"username": "nuevo_qa", "nombre_completo": "Cajero QA", "password": PASSWORD, "rol": "CAJERO"}
    assert client.post(reverse("identity:usuario_nuevo"), payload).status_code == 302
    nuevo = construir_repositorio().buscar_por_username("nuevo_qa")
    assert client.post(reverse("identity:usuario_nuevo"), dict(payload, username="NUEVO_QA")).status_code == 200
    datos_auditados = json.dumps(list(AuditoriaModel.objects.filter(entidad="UsuarioModel").values("detalle")))
    assert PASSWORD not in datos_auditados
    assert nuevo.password_hash not in datos_auditados
    otro = Client()
    assert otro.post(reverse("identity:login"), {"username": "nuevo_qa", "password": PASSWORD}).status_code == 302
    assert client.post(reverse("identity:usuario_editar", args=[nuevo.id]), dict(payload, nombre_completo="Nombre editado", rol="GERENTE")).status_code == 302
    assert construir_repositorio().buscar_por_id(nuevo.id).nombre_completo == "Nombre editado"
    assert otro.get(reverse("catalog:catalogo")).status_code == 302
    assert "usuario_id" not in otro.session
    assert otro.post(reverse("identity:login"), {"username": "nuevo_qa", "password": PASSWORD}).status_code == 302
    assert otro.session["rol"] == "GERENTE"
    assert client.post(reverse("identity:usuario_desactivar", args=[nuevo.id])).status_code == 302
    assert not construir_repositorio().buscar_por_id(nuevo.id).activo
    assert otro.get(reverse("catalog:catalogo")).status_code == 302
    assert "usuario_id" not in otro.session


def test_rf049_050_categoria_edicion_auditable_y_sin_secretos(client):
    usuario = staff(client)
    assert client.post(reverse("catalog:categorias"), {"nombre": "Panadería"}).status_code == 302
    categoria = CategoriaModel.objects.get(nombre="Panadería")
    assert client.post(reverse("catalog:categoria_editar", args=[categoria.id]), {"nombre": "Panes", "descripcion": "Frescos"}).status_code == 302
    categoria.refresh_from_db()
    assert categoria.nombre == "Panes"
    registros = AuditoriaModel.objects.filter(entidad="CategoriaModel", entidad_id=str(categoria.id))
    assert set(registros.values_list("accion", flat=True)) == {"CREAR", "ACTUALIZAR"}
    assert all(str(r.usuario_id) == usuario.id and r.fecha for r in registros)
    assert PASSWORD not in json.dumps(list(registros.values("detalle")))


@pytest.mark.parametrize("rol", ["CLIENTE", "CAJERO", "ALMACENERO"])
def test_no_administradores_no_mutan_usuarios_ni_reportes(client, rol):
    staff(client, rol)
    assert client.get(reverse("identity:usuarios")).status_code == 302
    assert client.get(reverse("reporting:ventas")).status_code == 302
    assert client.post(reverse("promotions:crear"), promo_payload()).status_code == 302
    assert PromocionModel.objects.count() == 0


def test_rf040_descuento_automatico_se_persiste_y_cobra_con_stock_real(client):
    from django.db import transaction
    from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
    from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
    from src.modules.sales.application.use_cases.agregar_producto import AgregarProducto
    from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
    from src.modules.sales.domain.entities.venta import Venta
    from src.modules.sales.infrastructure.factories import construir_venta_repository, construir_inventario_port, construir_auditoria_port, construir_promociones_port
    from src.modules.catalog.infrastructure.factories import construir_producto_repository
    usuario = staff(client, "CAJERO")
    p = producto()
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Recurrente", dni="12345678")
    compra(cliente, dias=2)
    compra(cliente, dias=1)
    PromocionModel.objects.create(id=uuid4(), nombre="Fidelización", tipo="PORCENTAJE", estado="ACTIVA",
        descuento_valor=10, aplica_clientes_frecuentes=True)
    repo = construir_venta_repository()
    venta = VentaAggregate(Venta(numero_ticket="T-FRECUENCIA", cajero_id=usuario.id))
    repo.guardar(venta)
    AgregarProducto(repo, construir_inventario_port(), construir_promociones_port()).ejecutar(
        str(venta.venta.id), construir_producto_repository().buscar_por_id(p.id), 2)
    assert client.post(reverse("sales:asignar_cliente", args=[venta.venta.id]), {"dni": cliente.dni}).status_code == 302
    recuperada = repo.buscar_por_id(venta.venta.id)
    assert recuperada.venta.total == 3.6
    assert recuperada.descuento_venta_pct == 10
    resultado = ProcesarPago(repo, construir_inventario_port(), construir_auditoria_port(),
        uow=transaction.atomic(), promociones=construir_promociones_port()).ejecutar(
            ProcesarPagoDTO(venta_id=str(venta.venta.id), metodo="EFECTIVO", monto=Decimal("3.60"), monto_entregado=Decimal("3.60")))
    assert resultado["estado"] == "PAGADA"
    hoy = timezone.localdate()
    utilidad = construir_reporte_repository().utilidad_por_producto(hoy, hoy)
    fila = next(f for f in utilidad if f["producto_id"] == str(p.id))
    assert fila["ingresos"] == 3.6
    assert fila["costo"] == 2
    assert fila["utilidad"] == 1.6


def test_rf050_fallo_de_auditoria_revierte_mutacion(client, monkeypatch):
    from django.db import DatabaseError
    staff(client)
    def fallo(*args, **kwargs):
        raise DatabaseError("Auditoría indisponible")
    monkeypatch.setattr(AuditoriaModel.objects, "create", fallo)
    client.raise_request_exception = False
    respuesta = client.post(reverse("catalog:categorias"), {"nombre": "No debe persistir"})
    assert respuesta.status_code == 500
    assert not CategoriaModel.objects.filter(nombre="No debe persistir").exists()


@pytest.mark.parametrize("telefono", ["abc", "123", "9" * 16])
def test_rf038_telefono_invalido_no_produce_500(client, telefono):
    staff(client, "CAJERO")
    respuesta = client.post(reverse("customers:registro"), {"nombre": "Cliente", "dni": "12345678", "telefono": telefono})
    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors
    assert ClienteModel.objects.count() == 0


def test_migracion_preserva_descuento_global_y_no_inventa_costos():
    from importlib import import_module
    from django.apps import apps
    from src.modules.sales.infrastructure.factories import construir_venta_repository
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Venta histórica")
    historica = compra(cliente, total=20, costo=None, estado="BORRADOR")
    VentaModel.objects.filter(pk=historica.id).update(subtotal=20, descuento=2, total=18)
    import_module("src.modules.sales.migrations.0004_preservar_descuentos_existentes").preservar(apps, None)
    agregado = construir_venta_repository().buscar_por_id(historica.id)
    agregado.calcular_totales()
    assert agregado.venta.total == 18
    assert agregado.descuento_venta_pct == 10
    assert agregado.lineas[0].costo_unitario is None
```

**Archivo: `tests/integration/test_smtp_real.py`**

```python
"""Entrega SMTP por socket real hacia un servidor local de pruebas."""
import django
from email.parser import BytesParser
from socketserver import StreamRequestHandler, ThreadingTCPServer
from threading import Thread

import pytest

from src.modules.orders.infrastructure.notifications.email_notifier import EmailNotifier

pytestmark = pytest.mark.integration


class SMTPHandler(StreamRequestHandler):
    def handle(self):
        self.wfile.write(b"220 localhost QA SMTP\r\n")
        recipients = []
        while line := self.rfile.readline():
            command = line.split(b" ", 1)[0].strip().upper()
            if command == b"QUIT":
                self.wfile.write(b"221 Bye\r\n")
                return
            if command == b"RCPT":
                recipients.append(line.decode().strip())
            if command == b"DATA":
                self.wfile.write(b"354 End with dot\r\n")
                data = []
                while (part := self.rfile.readline()) not in (b".\r\n", b""):
                    data.append(part[1:] if part.startswith(b"..") else part)
                self.server.messages.append((recipients[:], b"".join(data)))
            self.wfile.write(b"250 OK\r\n")


@pytest.mark.django_db
@pytest.mark.parametrize("via", ["notificador", "tarea"])
def test_email_pedido_se_entrega_por_smtp_al_cliente(settings, via):
    with ThreadingTCPServer(("127.0.0.1", 0), SMTPHandler) as server:
        server.messages = []
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            if django.VERSION >= (6, 1):
                settings.MAILERS = {"default": {"BACKEND": "django.core.mail.backends.smtp.EmailBackend",
                    "OPTIONS": {"host": host, "port": port, "timeout": 5, "username": "", "password": ""}}}
            else:
                settings.EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
                settings.EMAIL_HOST = host
                settings.EMAIL_PORT = port
                settings.EMAIL_HOST_USER = ""
                settings.EMAIL_HOST_PASSWORD = ""
                settings.EMAIL_USE_TLS = False
                settings.EMAIL_USE_SSL = False
                settings.EMAIL_TIMEOUT = 5
            if via == "notificador":
                assert EmailNotifier().notificar_pedido_listo("Ana", "ana@example.test", "P-SMTP-QA")
            else:
                from uuid import uuid4
                from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
                from src.modules.orders.infrastructure.tasks.enviar_notificacion_pedido import run
                pedido = PedidoModel.objects.create(id=uuid4(), numero="P-SMTP-QA", cliente_nombre="Ana",
                                                     cliente_email="ana@example.test", estado="LISTO")
                assert run(str(pedido.id)) is True
                pedido.refresh_from_db()
                assert pedido.notificado_listo
                assert run(str(pedido.id)) is True
            assert len(server.messages) == 1
            recipients, raw = server.messages[0]
            assert [r.lower() for r in recipients] == ["rcpt to:<ana@example.test>"]
            message = BytesParser().parsebytes(raw)
            assert message["To"] == "ana@example.test"
            assert "P-SMTP-QA" in message["Subject"]
        finally:
            server.shutdown()
            thread.join(timeout=5)
```

**Archivo: `tests/integration/test_redis_celery_real.py`**

```python
"""Redis y worker real. CI proporciona un servicio exclusivo para este job."""
import os
from uuid import uuid4

import pytest
from django.conf import settings
from celery import Celery
from celery.contrib.testing.worker import start_worker
from django.core.cache.backends.redis import RedisCache
from redis import Redis

pytestmark = [pytest.mark.integration, pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.environ.get("QA_REDIS_URL"), reason="Requiere QA_REDIS_URL de un Redis exclusivo de QA"
)]


def test_cache_redis_y_tarea_en_worker_real(monkeypatch):
    url = os.environ["QA_REDIS_URL"]
    # Celery prioriza estas variables sobre broker= y sobre app.conf.
    # .env local puede apuntar a localhost:6379; nunca usar ese broker en QA.
    monkeypatch.setenv("CELERY_BROKER_URL", url)
    monkeypatch.setenv("CELERY_RESULT_BACKEND", url)
    namespace = "qa-" + uuid4().hex
    redis = Redis.from_url(url, socket_connect_timeout=5, socket_timeout=5)
    cache = RedisCache(url, {"KEY_PREFIX": namespace, "TIMEOUT": 30, "OPTIONS": {}})
    app = Celery(namespace, broker=url, backend=url)
    app.conf.update(task_always_eager=False, task_default_queue=namespace,
                    imports=settings.CELERY_IMPORTS,
                    broker_transport_options={"global_keyprefix": namespace + ":"},
                    result_backend_transport_options={"global_keyprefix": namespace + ":"})

    @app.task(name=namespace + ".confirmar")
    def confirmar(referencia):
        return {"referencia": referencia, "estado": "procesado"}

    resultado = None
    try:
        assert redis.ping()
        cache.set("estado", "pendiente")
        assert cache.get("estado") == "pendiente"
        with start_worker(app, pool="solo", perform_ping_check=False, shutdown_timeout=10):
            assert "src.modules.orders.tasks.enviar_notificacion_pedido.run" in app.tasks
            assert "src.modules.promotions.tasks.actualizar_estado_promociones.run" in app.tasks
            resultado = confirmar.delay("PEDIDO-QA")
            assert resultado.get(timeout=10) == {"referencia": "PEDIDO-QA", "estado": "procesado"}
            negocio = app.send_task("src.modules.inventory.tasks.verificar_stock_minimo.run", queue=namespace)
            assert negocio.get(timeout=10) == 0
            negocio.forget()
            from django.core import mail
            from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
            pedido = PedidoModel.objects.create(id=uuid4(), numero="P-WORKER-QA", cliente_nombre="Ana",
                                                 cliente_email="ana@example.test", estado="LISTO")
            aviso = app.send_task("src.modules.orders.tasks.enviar_notificacion_pedido.run",
                                  args=[str(pedido.id)], queue=namespace)
            assert aviso.get(timeout=10) is True
            aviso.forget()
            pedido.refresh_from_db()
            assert pedido.notificado_listo
            assert mail.outbox[-1].to == ["ana@example.test"]
            assert "P-WORKER-QA" in mail.outbox[-1].subject
    finally:
        if resultado is not None:
            resultado.forget()
        cache.delete("estado")
        cache.close()
        app.close()
        redis.close()
```

# 6. NIVEL 3: PRUEBAS DE SISTEMA (SYSTEM / E2E & PERFORMANCE)

## 6.1 Qué se evalúa en este módulo

Registro → login → carrito → recojo → confirmación/cancelación con Chromium y CSRF.
Administración: categoría, promoción de porcentaje, combo mediante selectores, reportes e historial propio.
k6 verifica dos sesiones de clientes y dos roles, además de seis cobros reales y coherencia del stock.
Son smoke tests de concurrencia, no certificación de capacidad máxima de producción.

## 6.2 Aplicativos y Librerías a usar

Playwright/Chromium, k6 2.3.0, MySQL. Linux ejecuta carga contra Gunicorn del proyecto; Windows contra servidor HTTP de QA.
Se bloquean CDN externos en el navegador; se esperan elementos/navegación, sin sleeps para sincronizar UI.

## 6.3 Guía Paso a Paso de Configuración y Ejecución

```powershell
rtk proxy .venv-rf030-050/Scripts/python.exe -m playwright install chromium
rtk proxy .venv-rf030-050/Scripts/python.exe scripts/qa_download_tools.py k6
$env:QA_REQUIRE_BROWSER = '1'
$env:QA_K6_BINARY = 'C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/k6/v2.3.0/k6-v2.3.0-windows-amd64/k6.exe'
rtk proxy .venv-rf030-050/Scripts/python.exe scripts/qa_inventory_mysql.py tests/system --junitxml=reports/rf-system.xml
```

Usar la ruta que devuelve el descargador en otra máquina. No ejecutar dos cargas al mismo tiempo.
Presupuestos conservados: cobro p95 <100 ms, búsqueda <200 ms, HTTP/reportes/pedidos <500 ms; checks=100%, error inesperado=0.

## 6.4 Código Completo del Test de Sistema (E2E) + Script rápido de Carga/Performance

**Archivo: `tests/system/test_pedidos_online_playwright.py`**

```python
"""RF-030..036 a través de Chromium y servidor Django reales, con CSRF."""
from datetime import timedelta

import pytest
from django.utils import timezone

from tests.system.test_e2e_pos_playwright import navegador  # noqa: F401
from tests.integration.test_pedidos_online import PASSWORD, producto
from src.modules.orders.infrastructure.persistence.django_models.pedido_model import PedidoModel
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel

pytestmark = [pytest.mark.system, pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def test_cliente_se_registra_compra_y_cancela(navegador, live_server):
    p = producto()
    page = navegador.new_page()
    page.goto(live_server.url + "/clientes/registro/")
    for campo, valor in {
        "nombre": "Ana Navegador", "dni": "12345678", "email": "navegador@example.com",
        "telefono": "987654321", "password": PASSWORD, "password_confirmacion": PASSWORD,
    }.items():
        page.locator(f'[name="{campo}"]').fill(valor)
    page.get_by_role("button", name="Registrar", exact=True).click()
    page.wait_for_url("**/login/")
    page.locator('[name="username"]').fill("navegador@example.com")
    page.locator('[name="password"]').fill(PASSWORD)
    page.get_by_role("button", name="Ingresar", exact=True).click()
    page.wait_for_url("**/catalogo/")
    page.get_by_role("button", name="Agregar al carrito", exact=True).click()
    page.wait_for_url("**/pedidos/carrito/")
    assert page.get_by_text("Pan de recojo", exact=True).is_visible()
    page.goto(live_server.url + "/pedidos/checkout/")
    hora = (timezone.localtime() + timedelta(days=1)).replace(minute=30, second=0, microsecond=0)
    page.locator('[name="hora_recojo"]').fill(hora.strftime("%Y-%m-%dT%H:%M"))
    page.get_by_role("button", name="Confirmar pedido", exact=True).click()
    page.wait_for_url("**/pedidos/confirmacion/**")
    assert page.get_by_text("Pendiente", exact=True).is_visible()
    pedido = PedidoModel.objects.get()
    assert pedido.hora_recojo == hora
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 1
    page.get_by_role("button", name="Cancelar pedido", exact=True).click()
    page.wait_for_url("**/pedidos/pedido/**")
    assert page.get_by_text("Cancelado", exact=True).is_visible()
    pedido.refresh_from_db()
    assert pedido.estado == "CANCELADO"
    assert ExistenciaModel.objects.get(producto_id=p.id).reservada == 0
```

**Archivo: `tests/system/test_rf038_050_playwright.py`**

```python
import pytest

from tests.system.test_e2e_pos_playwright import navegador  # noqa: F401
from tests.integration.test_rf038_050 import PASSWORD, compra
from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.infrastructure.factories import construir_repositorio, construir_hasher
from src.modules.catalog.infrastructure.persistence.django_models.categoria_model import CategoriaModel
from src.modules.promotions.infrastructure.persistence.django_models.promocion_model import PromocionModel
from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from uuid import uuid4

pytestmark = [pytest.mark.system, pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


def login(page, live_server, username):
    page.goto(live_server.url + "/login/")
    page.locator('[name="username"]').fill(username)
    page.locator('[name="password"]').fill(PASSWORD)
    page.get_by_role("button", name="Ingresar", exact=True).click()
    page.wait_for_url("**/catalogo/")


def test_admin_gestiona_categoria_promocion_y_consulta_reportes(navegador, live_server):
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(UsuarioInputDTO(
        username="admin_navegador", password=PASSWORD, nombre_completo="Admin navegador", rol="ADMINISTRADOR"))
    page = navegador.new_page()
    login(page, live_server, "admin_navegador")
    page.goto(live_server.url + "/catalogo/categorias/")
    page.locator('[name="nombre"]').fill("Categoría navegador")
    page.get_by_role("button", name="Guardar categoría", exact=True).click()
    page.wait_for_url("**/catalogo/categorias/")
    categoria = CategoriaModel.objects.get(nombre="Categoría navegador")
    assert AuditoriaModel.objects.filter(entidad_id=str(categoria.id), accion="CREAR").exists()
    page.goto(live_server.url + "/promociones/crear/")
    page.locator('[name="nombre"]').fill("Porcentaje navegador")
    page.locator('[name="tipo"]').select_option("PORCENTAJE")
    page.locator('[name="descuento_valor"]').fill("10")
    page.get_by_role("button", name="Crear promocion", exact=True).click()
    page.wait_for_url("**/promociones/gestion/")
    page.get_by_role("button", name="Activar", exact=True).click()
    page.wait_for_url("**/promociones/gestion/")
    assert PromocionModel.objects.get(nombre="Porcentaje navegador").estado == "ACTIVA"
    assert page.get_by_text("Activa", exact=True).is_visible()
    page.goto(live_server.url + "/reportes/ventas/")
    assert page.get_by_role("heading", name="Métodos de pago", exact=True).is_visible()
    page.goto(live_server.url + "/reportes/productos/")
    assert page.get_by_role("heading", name="Productos más vendidos", exact=True).is_visible()


def test_cliente_consulta_su_historial_web(navegador, live_server):
    usuario = CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(UsuarioInputDTO(
        username="cliente_historial", email="historial@example.test", password=PASSWORD,
        nombre_completo="Cliente historial", rol="CLIENTE"))
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente historial", usuario_id=usuario.id)
    venta = compra(cliente, total=37)
    page = navegador.new_page()
    login(page, live_server, "historial@example.test")
    page.goto(live_server.url + f"/clientes/historial/{cliente.id}/")
    assert page.get_by_role("heading", name="Historial de compras").is_visible()
    assert page.get_by_text(venta.numero_ticket, exact=True).is_visible()
    response = page.goto(live_server.url + "/reportes/ventas/")
    assert response.status == 200
    page.wait_for_url("**/catalogo/")
    assert "Reporte de ventas" not in page.title()


def test_admin_crea_combo_desde_selectores_de_productos(navegador, live_server):
    from tests.integration.test_pedidos_online import producto
    from src.modules.catalog.models import ProductoModel
    primero = producto()
    segundo = ProductoModel.objects.create(id=uuid4(), nombre="Jugo combo", codigo_barras="7751234567891",
                                           costo=1, precio_venta=5, estado="ACTIVO")
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(UsuarioInputDTO(
        username="admin_combo", password=PASSWORD, nombre_completo="Admin combo", rol="ADMINISTRADOR"))
    page = navegador.new_page()
    login(page, live_server, "admin_combo")
    page.goto(live_server.url + "/promociones/crear/")
    page.locator('[name="nombre"]').fill("Desayuno navegador")
    page.locator('[name="tipo"]').select_option("COMBO")
    page.locator('[name="descuento_valor"]').fill("6")
    page.get_by_label("Producto del combo", exact=True).nth(0).select_option(str(primero.id))
    page.get_by_label("Producto del combo", exact=True).nth(1).select_option(str(segundo.id))
    page.get_by_role("button", name="Crear promocion", exact=True).click()
    page.wait_for_url("**/promociones/gestion/")
    promo = PromocionModel.objects.get(nombre="Desayuno navegador")
    assert promo.tipo == "COMBO"
    assert promo.componentes == [{"producto_id": str(primero.id), "cantidad": 1}, {"producto_id": str(segundo.id), "cantidad": 1}]


def test_cajero_cobra_con_descuento_automatico_por_frecuencia(navegador, live_server):
    from decimal import Decimal
    from tests.integration.test_pedidos_online import producto
    from src.modules.sales.models import VentaModel
    from src.modules.inventory.models import ExistenciaModel
    p = producto()
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente recurrente", dni="12345678")
    compra(cliente, total=10, dias=2)
    compra(cliente, total=10, dias=1)
    PromocionModel.objects.create(id=uuid4(), nombre="Fidelidad navegador", tipo="PORCENTAJE", estado="ACTIVA",
        descuento_valor=10, aplica_clientes_frecuentes=True)
    CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(UsuarioInputDTO(
        username="cajero_frecuencia", password=PASSWORD, nombre_completo="Cajero frecuencia", rol="CAJERO"))
    page = navegador.new_page()
    login(page, live_server, "cajero_frecuencia")
    page.goto(live_server.url + "/caja/apertura/")
    page.locator('[name="monto_apertura"]').fill("100")
    page.get_by_role("button", name="Abrir caja").click()
    page.wait_for_url("**/pos/")
    actual = VentaModel.objects.get(estado="BORRADOR")
    page.locator('#buscador-pos').fill(p.codigo_barras)
    with page.expect_response(lambda r: '/agregar/' in r.url) as agregado:
        page.locator('#buscador-pos').press('Enter')
    assert agregado.value.status == 200
    page.locator('[name="dni"]').fill(cliente.dni)
    page.get_by_role("button", name="Asociar cliente y calcular beneficio").click()
    page.wait_for_url("**/pago/")
    assert Decimal(page.locator('[name="monto"]').input_value()) == Decimal("1.80")
    page.locator('[name="metodo"]').select_option("EFECTIVO")
    page.locator('[name="monto_entregado"]').fill("2")
    with page.expect_response(lambda r: r.url.endswith(f'/pos/venta/{actual.id}/ticket/')) as ticket:
        page.get_by_role("button", name="Confirmar cobro").click()
    assert ticket.value.status == 200
    actual.refresh_from_db()
    assert actual.estado == "PAGADA"
    assert actual.total == Decimal("1.80")
    assert actual.cliente_id == cliente.id
    assert ExistenciaModel.objects.get(producto_id=p.id).cantidad == 9
```

**Archivo: `tests/system/test_rf038_050_k6.py`**

```python
import json
import os
from pathlib import Path
import subprocess
from uuid import uuid4

import pytest
from django.conf import settings
from django.test import Client

from tests.system.test_k6_pos_real import pos_http_server  # noqa: F401
from tests.integration.test_rf038_050 import staff, compra
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel

pytestmark = [pytest.mark.system, pytest.mark.performance, pytest.mark.django_db(transaction=True),
              pytest.mark.skipif(not os.environ.get("QA_K6_BINARY"), reason="Requiere QA_K6_BINARY")]


def test_reportes_carga_dos_roles_sin_filtrar_datos(client, pos_http_server):
    staff(client)
    otro = Client()
    staff(otro, "CLIENTE")
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente carga")
    compra(cliente, total=37)
    sesiones = [{"admin": admin, "cookie": settings.SESSION_COOKIE_NAME + "=" + c.cookies[settings.SESSION_COOKIE_NAME].value}
                for c, admin in ((client, True), (otro, False))]
    root = Path(__file__).resolve().parents[2]
    summary = root / "reports/k6-reportes-summary.json"
    summary.parent.mkdir(exist_ok=True)
    result = subprocess.run([os.environ["QA_K6_BINARY"], "run", "--summary-export", str(summary),
        "tests/performance/k6_reportes.js"], cwd=root, capture_output=True, text=True, timeout=60,
        env=dict(os.environ, BASE_URL=pos_http_server, QA_REPORTES_SESIONES=json.dumps(sesiones), K6_NO_USAGE_REPORT="true"))
    (root / "reports/k6-reportes-output.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(summary.read_text())["metrics"]["checks"]["value"] == 1
    assert VentaModel.objects.filter(estado="PAGADA", total=37).count() == 1
```

**Archivo: `tests/performance/k6_cobro.js`**

```javascript
// Solo QA. Crear un cajero por VU: PMV_USERNAME_PREFIX1, PREFIX2, etc.
// Sembrar producto con stock >= VUS*ITERATIONS. No reutilizar usuarios productivos.
// k6 run -e BASE_URL=http://127.0.0.1:8000 -e PMV_USERNAME_PREFIX=qa_cajero_ \
//   -e PMV_PASSWORD=... -e PMV_CODIGO=7751234567890 tests/performance/k6_cobro.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const BASE = (__ENV.BASE_URL || '').replace(/\/$/, '');
const TIEMPO_COBRO = new Trend('tiempo_cobro_ms', true);
const TIEMPO_BUSQUEDA = new Trend('tiempo_busqueda_ms', true);
const ERRORES = new Rate('tasa_errores_negocio');
let sesionPreparada = false; // El runtime JS y el cookie jar son propios de cada VU.

export const options = {
  noCookiesReset: true,
  scenarios: {
    punto_de_venta: {
      executor: 'per-vu-iterations', vus: Number(__ENV.VUS || 2),
      iterations: Number(__ENV.ITERATIONS || 5), maxDuration: '2m',
    },
  },
  thresholds: {
    checks: ['rate==1'], http_req_failed: ['rate==0'], http_req_duration: ['p(95)<500'],
    tiempo_cobro_ms: ['p(95)<100'], tiempo_busqueda_ms: ['p(95)<200'],
    tasa_errores_negocio: ['rate==0'],
  },
};

function token() {
  const values = http.cookieJar().cookiesForURL(`${BASE}/`).csrftoken;
  if (!values || !values.length) throw new Error('No se recibio cookie CSRF');
  return values[0];
}

function post(path, data) {
  // Django rota el token al iniciar sesion: leer siempre la cookie actual del VU.
  const csrf = token();
  return http.post(`${BASE}${path}`, { ...data, csrfmiddlewaretoken: csrf }, {
    headers: { Referer: `${BASE}/`, 'X-CSRFToken': csrf }, redirects: 0,
  });
}

function exigir(response, nombre, assertion) {
  if (!check(response, { [nombre]: assertion })) throw new Error(nombre);
}

export default function () {
  let ok = false;
  try {
    if (!BASE || !__ENV.PMV_USERNAME_PREFIX || !__ENV.PMV_PASSWORD || !__ENV.PMV_CODIGO) {
      throw new Error('Defina BASE_URL, PMV_USERNAME_PREFIX, PMV_PASSWORD y PMV_CODIGO de QA');
    }
    if (!sesionPreparada) {
      http.cookieJar().clear(`${BASE}/`);
      const loginPage = http.get(`${BASE}/login/`, { redirects: 0 });
      exigir(loginPage, 'formulario login', (r) => r.status === 200);
      const login = post('/login/', {
        username: `${__ENV.PMV_USERNAME_PREFIX}${__VU}`, password: __ENV.PMV_PASSWORD,
      });
      exigir(login, 'login aceptado', (r) => r.status === 302 && r.headers.Location === '/catalogo/');
      const apertura = post('/caja/apertura/', { monto_apertura: '100.00' });
      exigir(apertura, 'caja abierta', (r) => r.status === 302 && r.headers.Location === '/pos/');
      sesionPreparada = true;
    }
    const pos = http.get(`${BASE}/pos/`, { redirects: 0 });
    exigir(pos, 'POS autenticado', (r) => r.status === 200 && r.body.includes('Ticket en curso:'));
    const match = pos.body.match(/Ticket en curso:\s*([0-9a-f-]{36})/);
    if (!match) throw new Error('El POS no contiene venta activa');
    const ventaId = match[1];
    const busqueda = http.get(`${BASE}/pos/buscar/?q=${encodeURIComponent(__ENV.PMV_CODIGO)}`, { redirects: 0 });
    TIEMPO_BUSQUEDA.add(busqueda.timings.duration);
    exigir(busqueda, 'busqueda correcta', (r) => r.status === 200);
    const productos = busqueda.json('resultados');
    if (!Array.isArray(productos) || productos.length !== 1) throw new Error('Producto QA no encontrado');
    const agregar = post(`/pos/venta/${ventaId}/agregar/${productos[0].id}/`, { cantidad: '1' });
    exigir(agregar, 'producto agregado', (r) => r.status === 200);
    const total = agregar.json('total');
    if (typeof total !== 'number' || !Number.isFinite(total) || total <= 0) throw new Error('Total invalido');
    const cobro = post(`/pos/venta/${ventaId}/pago/`, {
      metodo: 'EFECTIVO', monto: total.toFixed(2), monto_entregado: total.toFixed(2),
    });
    TIEMPO_COBRO.add(cobro.timings.duration);
    exigir(cobro, 'cobro redirige al ticket', (r) =>
      r.status === 302 && r.headers.Location === `/pos/venta/${ventaId}/ticket/`);
    const ticket = http.get(`${BASE}${cobro.headers.Location}`, { redirects: 0 });
    exigir(ticket, 'ticket PDF emitido', (r) =>
      r.status === 200 && r.headers['Content-Type'].includes('application/pdf') && r.body.startsWith('%PDF'));
    ok = true;
  } finally {
    ERRORES.add(ok ? 0 : 1);
    sleep(0.5);
  }
}
```

**Archivo: `tests/performance/k6_pedidos.js`**

```javascript
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: { clientes: { executor: 'per-vu-iterations', vus: 2, iterations: 5, maxDuration: '30s' } },
  thresholds: { checks: ['rate==1'], http_req_failed: ['rate==0'], http_req_duration: ['p(95)<500'] },
};

const clientes = JSON.parse(__ENV.QA_PEDIDOS_CLIENTES);
const expected = http.expectedStatuses(200, 404);

export default function () {
  const propio = clientes[__VU - 1];
  const otro = clientes[__VU % 2];
  const params = { headers: { Cookie: propio.cookie }, redirects: 0, responseCallback: expected };
  const detalle = http.get(__ENV.BASE_URL + propio.ruta, params);
  check(detalle, {
    'cliente ve su pedido Pendiente': r => r.status === 200 && r.body.includes(propio.numero) && r.body.includes('Pendiente'),
  });
  const ajeno = http.get(__ENV.BASE_URL + otro.ruta, params);
  check(ajeno, { 'pedido ajeno protegido': r => r.status === 404 && !r.body.includes(otro.numero) });
}
```

**Archivo: `tests/performance/k6_reportes.js`**

```javascript
import http from 'k6/http';
import { check } from 'k6';
export const options = {
  scenarios: { roles: { executor: 'per-vu-iterations', vus: 2, iterations: 3, maxDuration: '30s' } },
  thresholds: { checks: ['rate==1'], http_req_failed: ['rate==0'], http_req_duration: ['p(95)<500'] },
};
const sesiones = JSON.parse(__ENV.QA_REPORTES_SESIONES);
export default function () {
  const sesion = sesiones[__VU - 1];
  for (const ruta of ['/reportes/ventas/', '/reportes/utilidad/']) {
    const r = http.get(__ENV.BASE_URL + ruta, {headers: {Cookie: sesion.cookie}, redirects: 0,
      responseCallback: http.expectedStatuses(200, 302)});
    check(r, {'acceso y datos según rol': r => sesion.admin ? r.status === 200 && r.body.includes('37') :
      r.status === 302 && r.headers.Location.endsWith('/catalogo/') && !r.body.includes('Total gastado')});
  }
}
```

# 7. NIVEL 4: PRUEBAS DE ACEPTACIÓN (UAT / BDD)

## 7.1 Escenarios de Negocio en Formato Gherkin

Los módulos tienen cuatro escenarios de pedidos, cinco comerciales y tres administrativos, doce en total.

**Archivo: `tests/uat/features/pedidos_online.feature`**

```gherkin
Feature: Pedidos web con recojo en tienda RF-030 a RF-037
  Scenario: Confirmar un pedido con hora de recojo
    Given una cliente web autenticada con dos panes en su carrito
    When confirma el pedido para recojo mañana en una franja válida
    Then el pedido queda Pendiente con dos unidades reservadas

  Scenario: Cancelar mientras está pendiente
    Given una cliente web autenticada con dos panes en su carrito
    When confirma el pedido para recojo mañana en una franja válida
    And solicita cancelar su pedido
    Then el pedido queda Cancelado y el stock queda disponible

  Scenario: La preparación impide cancelar
    Given una cliente web autenticada con dos panes en su carrito
    When confirma el pedido para recojo mañana en una franja válida
    And la tienda inicia la preparación
    And solicita cancelar su pedido
    Then el pedido sigue En preparación y conserva su reserva

  Scenario: Avisar cuando está listo
    Given una cliente web autenticada con dos panes en su carrito
    When confirma el pedido para recojo mañana en una franja válida
    And la tienda inicia la preparación
    And la tienda marca el pedido Listo
    Then la cliente recibe un email con su número de pedido
```

**Archivo: `tests/uat/features/clientes_promociones_admin.feature`**

```gherkin
Feature: Clientes frecuentes, promociones y administración RF-038 a RF-050
  Scenario: Calcular beneficio automático al asociar una cliente recurrente
    Given un carrito de dos soles para una cliente recurrente con fidelización vigente
    When el cajero asocia el DNI de esa cliente a la venta
    Then el importe a cobrar baja automáticamente a un sol con ochenta céntimos

  Scenario: Registrar al cliente frecuente en caja
    Given un cajero autenticado
    When registra el DNI y teléfono del cliente
    Then el cliente frecuente queda registrado sin pertenecer al cajero

  Scenario: Consultar historial propio
    Given una cliente con dos compras pagadas y una anulada
    When consulta su historial web
    Then ve dos compras por un total de treinta soles

  Scenario: Aplicar una promoción 2x1
    Given un administrador con un producto de dos soles
    When crea y activa una promoción 2x1
    Then dos unidades reciben dos soles de descuento

  Scenario: Vencer una promoción cuyo periodo terminó
    Given una promoción programada cuyo periodo ya terminó
    When se actualiza la vigencia de promociones
    Then queda Vencida y no aparece entre las promociones públicas

  Scenario: Reportar solo ventas pagadas
    Given un administrador y ventas pagadas y anuladas
    When consulta el reporte de ventas
    Then ve una transacción pagada y su método de pago

  Scenario: Auditar cambios de categorías
    Given un administrador autenticado
    When crea una categoría de productos
    Then la auditoría identifica al administrador y la categoría creada

  Scenario: Proteger la administración
    Given un cajero autenticado
    When intenta crear una promoción
    Then el sistema deniega la operación y no crea promociones
```

## 7.2 Automatización del UAT (Step Definitions) o Checklist de Validación Manual para el Product Owner / Cliente

**Archivo: `tests/uat/test_pedidos_online_bdd.py`**

```python
import pytest
from django.core import mail
from django.urls import reverse
from pytest_bdd import given, when, then, scenarios

from tests.integration.test_pedidos_online import carrito, confirmar
from src.modules.inventory.infrastructure.persistence.django_models.existencia_model import ExistenciaModel

pytestmark = [pytest.mark.uat, pytest.mark.django_db]
scenarios("features/pedidos_online.feature")


@given("una cliente web autenticada con dos panes en su carrito", target_fixture="contexto")
def cliente(client):
    pedido, producto = carrito(client)
    return {"pedido": pedido, "producto": producto}


@when("confirma el pedido para recojo mañana en una franja válida")
def confirma(client):
    assert confirmar(client).status_code == 302


@when("solicita cancelar su pedido")
def cancela(client, contexto):
    assert client.post(reverse("orders:cancelar", args=[contexto["pedido"].id])).status_code == 302


def estado_tienda(client, contexto, estado):
    sesion = client.session
    sesion["rol"] = "CAJERO"
    sesion.save()
    assert client.post(reverse("orders:cambiar_estado", args=[contexto["pedido"].id]), {"estado": estado}).status_code == 302
    sesion = client.session
    sesion["rol"] = "CLIENTE"
    sesion.save()


@when("la tienda inicia la preparación")
def prepara(client, contexto):
    estado_tienda(client, contexto, "EN_PREPARACION")


@when("la tienda marca el pedido Listo")
def listo(client, contexto, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        estado_tienda(client, contexto, "LISTO")


def comprobar(contexto, estado, reservada):
    pedido = contexto["pedido"]
    pedido.refresh_from_db()
    assert pedido.estado == estado
    assert ExistenciaModel.objects.get(producto_id=contexto["producto"].id).reservada == reservada


@then("el pedido queda Pendiente con dos unidades reservadas")
def pendiente(contexto):
    comprobar(contexto, "CONFIRMADO", 2)
    assert contexto["pedido"].hora_recojo is not None


@then("el pedido queda Cancelado y el stock queda disponible")
def cancelado(contexto):
    comprobar(contexto, "CANCELADO", 0)


@then("el pedido sigue En preparación y conserva su reserva")
def preparando(contexto):
    comprobar(contexto, "EN_PREPARACION", 2)


@then("la cliente recibe un email con su número de pedido")
def notificada(contexto):
    comprobar(contexto, "LISTO", 2)
    assert contexto["pedido"].notificado_listo
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["ana@example.com"]
    assert contexto["pedido"].numero in mail.outbox[0].subject
```

**Archivo: `tests/uat/test_clientes_promociones_admin_bdd.py`**

```python
from datetime import timedelta
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_bdd import given, when, then, scenarios

from tests.integration.test_rf038_050 import staff, compra, promo_payload
from tests.integration.test_pedidos_online import producto
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.catalog.infrastructure.persistence.django_models.categoria_model import CategoriaModel
from src.modules.promotions.infrastructure.persistence.django_models.promocion_model import PromocionModel
from src.modules.promotions.infrastructure.factories import construir_promocion_repository
from src.modules.promotions.application.use_cases.calcular_descuento import CalcularDescuento
from src.modules.promotions.infrastructure.tasks.actualizar_estado_promociones import run
from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
from src.shared.domain.value_objects.monto import Monto

pytestmark = [pytest.mark.uat, pytest.mark.django_db]
scenarios("features/clientes_promociones_admin.feature")


@pytest.fixture
def contexto():
    return {}


@given("un cajero autenticado")
def cajero(client, contexto):
    contexto["usuario"] = staff(client, "CAJERO")


@given("un administrador autenticado")
def administrador(client, contexto):
    contexto["usuario"] = staff(client)


@when("registra el DNI y teléfono del cliente")
def registra(client):
    assert client.post(reverse("customers:registro"), {"nombre": "Cliente UAT", "dni": "12345678", "telefono": "987654321"}).status_code == 302


@then("el cliente frecuente queda registrado sin pertenecer al cajero")
def registrado():
    cliente = ClienteModel.objects.get(dni="12345678")
    assert cliente.telefono == "987654321"
    assert cliente.usuario_id is None


@given("una cliente con dos compras pagadas y una anulada")
def cliente(client, contexto):
    usuario = staff(client, "CLIENTE")
    contexto["cliente"] = ClienteModel.objects.create(id=uuid4(), nombre="Cliente UAT", usuario_id=usuario.id)
    compra(contexto["cliente"], total=10, dias=1)
    compra(contexto["cliente"], total=20)
    compra(contexto["cliente"], total=999, estado="ANULADA")


@when("consulta su historial web")
def consulta(client, contexto):
    contexto["respuesta"] = client.get(reverse("customers:historial", args=[contexto["cliente"].id]))


@then("ve dos compras por un total de treinta soles")
def historial(contexto):
    assert contexto["respuesta"].status_code == 200
    assert contexto["respuesta"].context["historial"]["total_gastado"] == 30
    assert contexto["respuesta"].context["historial"]["cantidad"] == 2


@given("un administrador con un producto de dos soles")
def admin_producto(client, contexto):
    administrador(client, contexto)
    contexto["producto"] = producto()


@when("crea y activa una promoción 2x1")
def crea_2x1(client, contexto):
    assert client.post(reverse("promotions:crear"), promo_payload("NX1", producto_id=str(contexto["producto"].id), descuento_valor="0")).status_code == 302
    promocion = PromocionModel.objects.get()
    assert client.post(reverse("promotions:promociones"), {"accion": "activar", "promocion_id": str(promocion.id)}).status_code == 302


@then("dos unidades reciben dos soles de descuento")
def descuento(contexto):
    assert CalcularDescuento(construir_promocion_repository()).por_producto(str(contexto["producto"].id), Monto(4), 2).valor == 2


@given("una promoción programada cuyo periodo ya terminó")
def vencida():
    ahora = timezone.now()
    PromocionModel.objects.create(id=uuid4(), nombre="UAT vencida", tipo="PORCENTAJE", estado="PROGRAMADA", descuento_valor=10,
        vigencia_desde=ahora - timedelta(days=2), vigencia_hasta=ahora - timedelta(days=1))


@when("se actualiza la vigencia de promociones")
def actualiza():
    run()


@then("queda Vencida y no aparece entre las promociones públicas")
def no_publica(client):
    assert PromocionModel.objects.get().estado == "FINALIZADA"
    assert client.get(reverse("promotions:activas"), HTTP_ACCEPT="application/json").json()["promociones"] == []


@given("un administrador y ventas pagadas y anuladas")
def ventas(client, contexto):
    administrador(client, contexto)
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente reportes")
    compra(cliente, total=37)
    compra(cliente, total=999, estado="ANULADA")


@when("consulta el reporte de ventas")
def reporte(client, contexto):
    contexto["respuesta"] = client.get(reverse("reporting:ventas"))


@then("ve una transacción pagada y su método de pago")
def reporte_correcto(contexto):
    respuesta = contexto["respuesta"]
    assert respuesta.status_code == 200
    assert respuesta.context["reporte"].total_ventas == 37
    assert respuesta.context["reporte"].cantidad_tickets == 1
    assert respuesta.context["metodos"] == {"EFECTIVO": 37}


@when("crea una categoría de productos")
def categoria(client):
    assert client.post(reverse("catalog:categorias"), {"nombre": "Categoría UAT"}).status_code == 302


@then("la auditoría identifica al administrador y la categoría creada")
def audita(contexto):
    categoria = CategoriaModel.objects.get(nombre="Categoría UAT")
    assert AuditoriaModel.objects.filter(entidad="CategoriaModel", entidad_id=str(categoria.id), usuario_id=contexto["usuario"].id, accion="CREAR").exists()


@when("intenta crear una promoción")
def intenta(client, contexto):
    contexto["respuesta"] = client.post(reverse("promotions:crear"), promo_payload())


@then("el sistema deniega la operación y no crea promociones")
def deniega(contexto):
    assert contexto["respuesta"].status_code == 302
    assert contexto["respuesta"].url == reverse("catalog:catalogo")
    assert PromocionModel.objects.count() == 0


@given("un carrito de dos soles para una cliente recurrente con fidelización vigente")
def carrito_recurrente(client, contexto):
    from src.modules.sales.domain.entities.venta import Venta
    from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
    from src.modules.sales.infrastructure.factories import construir_venta_repository
    cajero(client, contexto)
    p = producto()
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Recurrente UAT", dni="12345678")
    compra(cliente, total=10, dias=2)
    compra(cliente, total=10, dias=1)
    PromocionModel.objects.create(id=uuid4(), nombre="Fidelidad UAT", tipo="PORCENTAJE", estado="ACTIVA",
        descuento_valor=10, aplica_clientes_frecuentes=True)
    agregado = VentaAggregate(Venta(numero_ticket="T-UAT-FRECUENCIA", cajero_id=contexto["usuario"].id))
    agregado.agregar_producto(str(p.id), p.nombre, 1, Monto(2))
    agregado.calcular_totales()
    construir_venta_repository().guardar(agregado)
    contexto["cliente"], contexto["venta_id"] = cliente, str(agregado.venta.id)


@when("el cajero asocia el DNI de esa cliente a la venta")
def asocia(client, contexto):
    assert client.post(reverse("sales:asignar_cliente", args=[contexto["venta_id"]]), {"dni": contexto["cliente"].dni}).status_code == 302


@then("el importe a cobrar baja automáticamente a un sol con ochenta céntimos")
def beneficio_automatico(contexto):
    from src.modules.sales.infrastructure.factories import construir_venta_repository
    venta = construir_venta_repository().buscar_por_id(contexto["venta_id"])
    assert venta.venta.total == 1.8
    assert venta.descuento_venta_pct == 10
```

## 7.3 Guía Paso a Paso para ejecutar y aprobar el UAT

```powershell
rtk proxy .venv-rf030-050/Scripts/python.exe -m pytest tests/uat -q -p no:cacheprovider --junitxml=reports/rf-uat.xml
```

El Product Owner valida reglas/supuestos, nombres de estados, totales y permisos con cuentas de QA y registra versión,
fecha, resultado y aprobación. Su firma no se sustituye con un pytest verde. No se envían mensajes a clientes reales.

# 8. GUÍA DE AI SKILLS, MCP Y AUTOMATIZACIÓN AGÉNTICA (CONTEXTO 2026-2027)

## 8.1 Configuración de Skill / Rule para el Agente de Código

Regla lista para Cursor, aplicada al trabajar sobre los archivos coincidentes; no implica que el IDE ejecute tests sin una tarea del usuario.

**Archivo: `../.cursor/rules/rf030-050-testing.mdc`**

```markdown
---
description: Pruebas y contratos RF-030 a RF-050 en los cuatro niveles
globs: puntoventa_total/src/modules/{orders,customers,promotions,reporting,identity,catalog,auditing,sales}/**/*.py,puntoventa_total/tests/**/*rf038_050*,puntoventa_total/tests/**/*clientes_promociones*
alwaysApply: false
---

Lee puntoventa_total/docs/testing/plan_maestro_rf030_050.md y pedidos_online.md.

- Mantén RF-030..RF-050 y documenta los supuestos de negocio no confirmados.
- Pedidos: propietario = Usuario.id; solo Pendiente admite cancelación del cliente; franjas futuras de 30 minutos.
- Historial/frecuencia: cliente = Customers.Cliente.id en las ventas. Excluir anuladas y borradores.
- Registro por cajero no asigna la cuenta del cajero al cliente registrado.
- Conserva la política existente de fidelización hasta que el negocio indique otra; no inventes tasas.
- El código existente clasifica como OCASIONAL también intervalos superiores a 30 días; no inventar un corte sin confirmación.
- 2x1 es paquete de dos unidades, una gratuita; combo requiere productos distintos y precio final por paquete completo.
- Las promociones caducan en el instante final; una programada ya vencida nunca se activa transitoriamente.
- Aplica el beneficio automáticamente antes del primer pago. No sumes beneficios incompatibles ni alteres pagos iniciados.
- La utilidad usa el costo congelado al agregar la línea y distribuye el descuento global conservando centavos.
- No inventes costos históricos; marca como parcial el reporte que contiene costos desconocidos.
- Auditoría: agregado, actor y fecha dentro de la transacción; movimientos de inventario conservan su propio libro.
- No incluyas passwords, tokens, teléfonos, DNI ni cuerpos de request en la auditoría técnica.
- Revoca la sesión de una cuenta inactiva y los permisos anteriores cuando cambia de rol.
- Reproduce fallos antes de editar expectativas; conserva los umbrales de cobertura y rendimiento existentes.
- Ejecuta Unit, MySQL real (incluidas carreras), navegador/carga y UAT. No llames integración MySQL a SQLite.
- Usa rtk para shell. No ejecutes dos suites de carga al mismo tiempo.
- Guarda JUnit, cobertura, resúmenes k6 y traces sin cookies/credenciales.
- Una ejecución verde no garantiza ausencia absoluta de flakiness ni sustituye aceptación del Product Owner.
```

## 8.2 Servidores MCP (Model Context Protocol) recomendados

Playwright MCP es opcional para inspeccionar la UI local y reproducir un fallo; los tests versionados mantienen el criterio verificable:
[documentación oficial](https://playwright.dev/python/docs/getting-started-mcp).
El stack usa MySQL: no hace falta instalar un MCP de PostgreSQL/SQLite ajeno a su persistencia.
Para inspección de datos se prefieren consultas limitadas sobre la instancia efímera; un MCP no debe recibir la BD del negocio.
GitHub MCP solo resulta necesario si se desea inspeccionar checks/artifacts remotos; pytest no depende de él.
Las anotaciones read-only no sustituyen permisos del servidor:
[referencia oficial MCP](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/).
No se instalaron ni publicaron conexiones externas durante esta auditoría.

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
[Sintaxis oficial de Claude Code](https://docs.anthropic.com/en/docs/claude-code/cli-usage).

# 9. PIPELINE CI/CD (QUALITY GATES)

El workflow de la **raíz Git** descubre estos tests nuevos sin listas manuales. Cada perfil ejecuta los pasos en orden:
Unit → gate unitario → MySQL → Sistema/Carga → UAT → cobertura global. Chromium/k6/Redis forman parte del job.
La ejecución completa rechaza skips/xfails y cobertura inferior a 80%; los presupuestos k6 también bloquean.
Un YAML verde no bloquea por sí mismo el merge: se requieren checks obligatorios en la protección de main,
con nombres `quality (production-declared)` y `quality (qa)`; esa protección ya estaba configurada en este repositorio.
Esta ampliación se entrega localmente, sin afirmar un nuevo check remoto ejecutado.
[Semántica oficial del workflow](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

**Archivo: `../.github/workflows/full-quality.yml`**

```yaml
name: Full quality audit
on:
  pull_request:
  push:
    branches: [main, 'qa/**']
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
    services:
      redis:
        image: redis:7-alpine
        ports: ['6379:6379']
        options: >-
          --health-cmd="redis-cli ping" --health-interval=5s
          --health-timeout=3s --health-retries=10
    strategy:
      fail-fast: false
      matrix:
        include:
          - python: '3.11'
            requirements: requirements/testing.txt
            profile: production-declared
          - python: '3.14.7'
            requirements: requirements/qa-inventory-mysql.txt
            profile: qa
    name: quality (${{ matrix.profile }})
    runs-on: ubuntu-24.04
    timeout-minutes: 30
    env:
      DJANGO_SETTINGS_MODULE: config.settings.testing
      QA_REQUIRE_BROWSER: '1'
      QA_REDIS_URL: redis://127.0.0.1:6379/15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
          cache: pip
          cache-dependency-path: puntoventa_total/requirements/*.txt
      - name: System dependencies
        run: sudo apt-get update && sudo apt-get install -y pkg-config default-libmysqlclient-dev build-essential
      - name: Python dependencies
        run: python -m pip install -r ${{ matrix.requirements }}
      - name: Django checks
        run: python manage.py check --settings=config.settings.testing
      - name: Migration consistency
        run: python manage.py makemigrations --check --dry-run --settings=config.settings.testing
      - name: '1 - Unit'
        run: python -m pytest tests/unit -q --cov=src --cov-fail-under=0 --cov-report=json:reports/audit_unit_coverage.json --junitxml=reports/full-unit.xml
      - name: Unit domain and application coverage gate
        run: python scripts/qa_unit_gate.py
      - name: '2 - Integration on disposable MySQL'
        run: python scripts/qa_inventory_mysql.py tests/integration --runxfail --junitxml=reports/full-integration.xml
      - name: Install Chromium
        run: python -m playwright install --with-deps chromium
      - uses: grafana/setup-k6-action@v1
        with:
          k6-version: '2.3.0'
      - name: Locate k6
        run: echo "QA_K6_BINARY=$(command -v k6)" >> "$GITHUB_ENV"
      - name: '3 - System and performance budgets'
        run: python scripts/qa_inventory_mysql.py tests/system tests/e2e tests/functional tests/performance --junitxml=reports/full-system.xml
      - name: '4 - Acceptance'
        run: python -m pytest tests/uat -q --junitxml=reports/full-uat.xml
      - name: Global coverage gate (all levels)
        env:
          QA_REQUIRE_ALL_TESTS: '1'
        run: python scripts/qa_inventory_mysql.py tests --runxfail --cov=src --cov-fail-under=80 --cov-report=xml:reports/full-coverage.xml --junitxml=reports/full-suite.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: full-quality-evidence-${{ matrix.profile }}
          path: puntoventa_total/reports/
```

# 10. MATRIZ DE TRAZABILIDAD DE PRUEBAS DEL MÓDULO

U = `rtk proxy python -m pytest tests/unit -q`.
I = `rtk proxy python scripts/qa_inventory_mysql.py tests/integration`.
S = `rtk proxy python scripts/qa_inventory_mysql.py tests/system` (Chromium/k6 disponibles).
A = `rtk proxy python -m pytest tests/uat -q`.
Los nombres de tests en la tabla son nodos verificables en los archivos incluidos arriba.

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
| RF-042 | programar / actualizar_estado_promociones | Unit/Int/UAT | Positivo/Borde | Rango válido; vencida no se activa ni se publica | U / I / A |
| RF-043 | historial_compras_view | Int/Sys/UAT | Positivo/Negativo | Cliente consulta el propio, no el ajeno | I / S / A |
| RF-044 | ReporteVentasDiarias / ventas_reporte_view | Int/Sys/UAT | Positivo | Total, tickets y métodos de pago | I / S / A |
| RF-045 | RangoReporteForm / ReporteVentasPorFecha | Int/Sys | Positivo/Negativo | Filtra fechas; inválido da 400 y no 500 | I / S |
| RF-046 | productos_reporte_view | Int/Sys | Positivo | Ranking por cantidad o monto neto | I / S |
| RF-047 | agrupar_utilidad / ReporteUtilidad | Unit/Int/Sys | Positivo/Borde | Costo congelado, descuento repartido y centavos conservados | U / I / S |
| RF-048 | crear/editar/desactivar_usuario | Int | Positivo/Negativo | Roles, edición, baja y revocación de sesión | I |
| RF-049 | categoria_view | Int/Sys/UAT | Positivo/Negativo | Creación y edición con permisos | I / S / A |
| RF-050 | RequestAuditMiddleware / auditoría de venta | Int/Sys/UAT | Positivo/Negativo | Actor, agregado y fecha; fallo de auditoría revierte | I / S / A |

# EVALUACIÓN FINAL DEL MÓDULO AUDITADO

Escala cualitativa, no porcentaje medido ni certificación ISO:

- Testabilidad del Código Actual: **8/10**. Dominio aislable; algunos adaptadores construyen repositorios concretos.
- Cobertura Unitaria Alcanzable: **9/10**. Propiedades y reglas puras automatizadas; cobertura real se informa debajo.
- Aislamiento de Dependencias: **8/10**. Puertos en unitarias; BD/worker/SMTP reales para evidencia integrada.
- Preparación para CI/CD: **9/10**. Dos perfiles, cuatro niveles, artifacts y gates; falta nuevo CI remoto de esta ampliación.
- Resiliencia ante Fallos (Edge Cases): **8/10**. Rollback, carreras, permisos y avisos fallidos; límites SMTP e históricos explicitados.

# ESTADO DE CALIDAD (QUALITY READINESS)

Los estados definitivos dependen de las evidencias finales de esta ejecución, que aparecen a continuación.
La aceptación formal del negocio y la configuración del SMTP productivo no se sustituyen por tests locales.
No se promete ausencia absoluta de flakiness ni 100% de cobertura de código.

| Perfil | Pruebas | Fallos / errores / omitidas | Cobertura global |
|---|---|---|---|

| production | 490/490 | 0 / 0 / 0 | 88.57% |

| qa | 490/490 | 0 / 0 / 0 | 88.34% |

| Perfil | Unit | Integration | System/E2E/Functional/Performance | UAT |
|---|---|---|---|---|

| production | 252 | 175 | 36 | 27 |

| qa | 252 | 175 | 36 | 27 |

| Perfil | Cobro p95 (100 ms) | Pedidos HTTP p95 (500 ms) | Reportes HTTP p95 (500 ms) |
|---|---|---|---|

| production | 71.83 ms | 30.09 ms | 38.85 ms |

| qa | 62.35 ms | 26.1 ms | 21.43 ms |

Unit Test Ready → ✅ Listo. Integration Ready → ✅ Listo (MySQL nativo efímero). System/E2E Ready → ✅ Listo. UAT/Business Ready → automatización ✅ lista, aprobación PO pendiente.

Reproducir suite completa local con infraestructura aislada instalada en este equipo:

```powershell
rtk proxy .venv-production/Scripts/python.exe scripts/qa_redis_native.py --binary C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/redis/8.10.2/Redis-8.10.2-Windows-x64-cygwin/redis-server.exe --mysql-basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --k6-binary C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/k6/v2.3.0/k6-v2.3.0-windows-amd64/k6.exe --coverage --report-prefix rf030-050-production
rtk proxy python scripts/qa_rf030_050_evidence.py --capture production
rtk proxy .venv/Scripts/python.exe scripts/qa_redis_native.py --binary C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/redis/8.10.2/Redis-8.10.2-Windows-x64-cygwin/redis-server.exe --mysql-basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --k6-binary C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/k6/v2.3.0/k6-v2.3.0-windows-amd64/k6.exe --coverage --report-prefix rf030-050-qa
rtk proxy python scripts/qa_rf030_050_evidence.py --capture qa
rtk proxy python scripts/qa_rf030_050_evidence.py
rtk proxy python scripts/qa_build_rf030_050_report.py
```

Ejecutar los perfiles secuencialmente. El wrapper exige cero skips/xfails en la suite completa.
Evidencias: reports/rf030-050-*.xml, *-coverage.json, resúmenes k6 y browser/*.zip.
Son servicios nativos efímeros; no se etiquetan como Testcontainers ejecutado en esta máquina.
El workflow utiliza contenedores y está listo para validar el mismo código cuando se publique una PR.

Activación en el entorno del negocio: revisar las nuevas migraciones sales/0003..0004 y promotions/0002, además de
las migraciones de Pedidos si aún no se aplicaron; ejecutar `rtk proxy python manage.py migrate` en ese entorno,
configurar SMTP con .env.example y reiniciar web/worker/Beat. No se migró ni modificó la base del negocio en esta auditoría.
