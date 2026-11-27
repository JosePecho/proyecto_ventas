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

**Archivo: `tests/unit/application/test_reportes_administracion.py`**

```python
"""Contratos puros RF-044/045/047, sin ORM ni servicios."""
from datetime import date
from unittest.mock import Mock

import pytest

from src.modules.reporting.application.use_cases.reporte_utilidad import ReporteUtilidad
from src.modules.reporting.application.use_cases.reporte_ventas_diarias import ReporteVentasDiarias
from src.modules.reporting.domain.repositories.reporte_repository import ReporteRepository
from src.modules.reporting.domain.value_objects.utilidad_historica import agrupar_utilidad
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.modules.auditing.domain.entities.registro_auditoria import RegistroAuditoria
from src.modules.auditing.domain.repositories.auditoria_repository import AuditoriaRepository
from src.modules.auditing.application.dto.auditoria_dto import FiltroAuditoriaDTO
from src.modules.auditing.application.use_cases.consultar_auditoria import ConsultarAuditoria
from src.modules.auditing.application.use_cases.registrar_auditoria import RegistrarAuditoria
from src.modules.auditing.application.use_cases.rastrear_transaccion import RastrearTransaccion
from src.modules.reporting.application.use_cases.reporte_ventas_por_fecha import ReporteVentasPorFecha
from src.modules.reporting.application.use_cases.reporte_productos_mas_vendidos import ReporteProductosMasVendidos
from src.shared.application.exceptions.application_exception import NotFoundException
from src.modules.identity.domain.entities.usuario import Usuario
from src.modules.identity.domain.enums.rol_usuario import RolUsuario
from src.modules.catalog.domain.entities.categoria import Categoria

pytestmark = pytest.mark.unit


def fila(ingresos, costo, producto="pan"):
    return {"venta_id": producto, "producto_id": producto, "producto_nombre": producto,
            "cantidad": 1, "importe": ingresos, "total_venta": ingresos, "costo_unitario": costo}


@pytest.mark.parametrize("ingresos,costo,esperado", [
    (10, 6, 40.0), (10, 15, -50.0), (32, 31, 3.13),
    (0, 2, None), (10, None, None),
])
def test_margen_por_producto_es_utilidad_sobre_ingresos(ingresos, costo, esperado):
    resultado = agrupar_utilidad([fila(ingresos, costo)])[0]
    assert resultado["margen_pct"] == esperado


def test_margen_total_pondera_ingresos_en_lugar_de_promediar_porcentajes():
    repo = Mock(spec=ReporteRepository)
    repo.utilidad_por_producto.return_value = agrupar_utilidad([fila(10, 5), fila(90, 89, "torta")])
    reporte = ReporteUtilidad(repo).ejecutar(date(2026, 10, 1), date(2026, 10, 17))
    assert (reporte.ingresos_totales, reporte.costos_totales, reporte.utilidad_total) == (100, 94, 6)
    assert reporte.margen_pct == 6
    assert not reporte.estimado


def test_margen_total_y_producto_redondean_el_mismo_empate_decimal():
    repo = Mock(spec=ReporteRepository)
    repo.utilidad_por_producto.return_value = agrupar_utilidad([fila(32, 31)])
    reporte = ReporteUtilidad(repo).ejecutar(date(2026, 10, 17), date(2026, 10, 17))
    assert reporte.margen_pct == reporte.por_producto[0]["margen_pct"] == 3.13


def test_reporte_sin_ventas_es_cero_y_no_divide_por_cero():
    repo = Mock(spec=ReporteRepository)
    repo.utilidad_por_producto.return_value = []
    reporte = ReporteUtilidad(repo).ejecutar(date(2026, 10, 17), date(2026, 10, 17))
    assert reporte.ingresos_totales == reporte.costos_totales == reporte.utilidad_total == 0
    assert reporte.margen_pct == 0


@pytest.mark.parametrize("desde,hasta", [
    (date(2026, 10, 20), date(2026, 10, 19)), (date(2025, 1, 1), date(2026, 10, 17)),
])
def test_rango_invalido_no_consulta_repositorio(desde, hasta):
    repo = Mock(spec=ReporteRepository)
    with pytest.raises(ValidationException):
        ReporteUtilidad(repo).ejecutar(desde, hasta)
    repo.utilidad_por_producto.assert_not_called()


def test_reporte_diario_conserva_tickets_y_metodos_de_pago():
    repo = Mock(spec=ReporteRepository)
    dia = date(2026, 10, 17)
    repo.ventas_por_dia.return_value = [{"fecha": dia.isoformat(), "total": 40, "cantidad": 2}]
    repo.totales_por_metodo_pago.return_value = {"EFECTIVO": 10, "TARJETA": 30}
    reporte = ReporteVentasDiarias(repo).ejecutar(dia)
    assert (reporte["total"], reporte["tickets"], reporte["metodos_pago"]) == (
        40, 2, {"EFECTIVO": 10, "TARJETA": 30},
    )
    repo.ventas_por_dia.assert_called_once_with(dia, dia)


@pytest.mark.parametrize("accion", ["CREAR", "ACTUALIZAR", "ELIMINAR"])
def test_acciones_transversales_pueden_consultarse_como_dominio(accion):
    registro = RegistroAuditoria.crear(accion, "CategoriaModel", "categoria-1", "actor-1")
    assert (registro.accion, registro.usuario_id, registro.entidad_id) == (accion, "actor-1", "categoria-1")


def test_accion_arbitraria_sigue_rechazada():
    with pytest.raises(ValidationException):
        RegistroAuditoria.crear("ACCION_INVENTADA", "CategoriaModel", "categoria-1")


def test_ventas_por_rango_acumulan_tickets_total_e_igv():
    repo = Mock(spec=ReporteRepository)
    repo.ventas_por_dia.return_value = [
        {"fecha": "2026-10-16", "total": 10, "cantidad": 1, "igv": 1.8},
        {"fecha": "2026-10-17", "total": 30, "cantidad": 2, "igv": 5.4},
    ]
    reporte = ReporteVentasPorFecha(repo).ejecutar(date(2026, 10, 16), date(2026, 10, 17))
    assert (reporte.cantidad_tickets, reporte.total_ventas, reporte.total_igv) == (3, 40, 7.2)


def test_ranking_preserva_orden_y_limite_del_repositorio():
    repo = Mock(spec=ReporteRepository)
    repo.productos_mas_vendidos.return_value = [{"producto_id": "torta", "unidades": 5}]
    desde, hasta = date(2026, 10, 1), date(2026, 10, 17)
    assert ReporteProductosMasVendidos(repo).ejecutar(desde, hasta, 1) == [{"producto_id": "torta", "unidades": 5}]
    repo.productos_mas_vendidos.assert_called_once_with(desde, hasta, 1)


def test_auditoria_convierte_fechas_y_pagina_sin_alterar_el_actor():
    repo = Mock(spec=AuditoriaRepository)
    eventos = [RegistroAuditoria.crear("CREAR", "CategoriaModel", str(i), "actor") for i in range(3)]
    repo.consultar.return_value = eventos
    pagina = ConsultarAuditoria(repo).ejecutar(
        FiltroAuditoriaDTO(usuario_id="actor", desde="2026-10-01", hasta="2026-10-17"), pagina=2, por_pagina=2,
    )
    assert pagina.total == 3 and len(pagina.items) == 1
    assert pagina.items[0].entidad_id == "2" and pagina.items[0].usuario_id == "actor"
    assert repo.consultar.call_args.kwargs["desde"] == date(2026, 10, 1)
    assert repo.consultar.call_args.kwargs["hasta"] == date(2026, 10, 17)


def test_registrar_auditoria_conserva_actor_y_entidad():
    repo = Mock(spec=AuditoriaRepository)
    identificador = RegistrarAuditoria(repo).ejecutar("CREAR", "CategoriaModel", "cat-1", "actor")
    evento = repo.guardar.call_args.args[0]
    assert identificador == str(evento.id)
    assert (evento.usuario_id, evento.entidad_id) == ("actor", "cat-1")


def test_traza_conserva_primera_y_ultima_accion():
    repo = Mock(spec=AuditoriaRepository)
    repo.trazas_de_entidad.return_value = [
        RegistroAuditoria.crear("ACTUALIZAR", "CategoriaModel", "cat-1"),
        RegistroAuditoria.crear("CREAR", "CategoriaModel", "cat-1"),
    ]
    traza = RastrearTransaccion(repo).ejecutar("CategoriaModel", "cat-1")
    assert (traza["cantidad"], traza["primera_accion"], traza["ultima_accion"]) == (2, "CREAR", "ACTUALIZAR")


def test_traza_inexistente_se_informa():
    repo = Mock(spec=AuditoriaRepository)
    repo.trazas_de_entidad.return_value = []
    with pytest.raises(NotFoundException):
        RastrearTransaccion(repo).ejecutar("CategoriaModel", "inexistente")


@pytest.mark.parametrize("rol", list(RolUsuario))
def test_usuario_desactivado_no_puede_autenticarse_con_ningun_rol(rol):
    usuario = Usuario(username="usuario_qa", nombre_completo="Usuario QA", rol=rol)
    assert usuario.puede_autenticarse()
    usuario.desactivar()
    assert not usuario.puede_autenticarse()


def test_categoria_rechaza_nombre_vacio_al_editar_y_conserva_el_anterior():
    categoria = Categoria(nombre="Panes")
    with pytest.raises(ValidationException):
        categoria.renombrar("")
    assert categoria.nombre == "Panes"
```

**Archivo: `scripts/qa_reportes_unit_gate.py`**

```python
"""Cobertura de núcleo RF-044..050, incluyendo archivos no importados por los tests."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from coverage import Coverage

ROOT = Path(__file__).resolve().parents[1]
ARCHIVOS = [
    "reporting/domain/value_objects/rango_fechas.py",
    "reporting/domain/value_objects/utilidad_historica.py",
    "reporting/application/use_cases/reporte_ventas_diarias.py",
    "reporting/application/use_cases/reporte_ventas_por_fecha.py",
    "reporting/application/use_cases/reporte_productos_mas_vendidos.py",
    "reporting/application/use_cases/reporte_utilidad.py",
    "auditing/domain/entities/registro_auditoria.py",
    "auditing/application/use_cases/consultar_auditoria.py",
    "auditing/application/use_cases/registrar_auditoria.py",
    "auditing/application/use_cases/rastrear_transaccion.py",
    "identity/domain/entities/usuario.py",
    "catalog/domain/entities/categoria.py",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", default="reports/rf044-050-unit.xml")
    parser.add_argument("--data-file", default=".coverage")
    args = parser.parse_args()
    reporte = ET.parse(ROOT / args.junit).getroot()
    casos = list(reporte.iter("testcase"))
    if not casos or any(not c.get("classname", "").startswith("tests.unit.") or
                        any(c.find(tag) is not None for tag in ("failure", "error", "skipped")) for c in casos):
        raise SystemExit("El gate requiere un JUnit unitario aprobado, sin omisiones")
    coverage = Coverage(data_file=str(ROOT / args.data_file))
    coverage.load()
    if not coverage.get_data().measured_files():
        raise SystemExit("No hay datos de cobertura")
    filas = []
    for ruta in ARCHIVOS:
        _, lineas, _, faltantes, _ = coverage.analysis2(str(ROOT / "src/modules" / ruta))
        filas.append({"archivo": ruta, "lineas": len(lineas), "cubiertas": len(lineas) - len(faltantes),
                      "faltantes": faltantes})
    total = sum(f["lineas"] for f in filas)
    cubiertas = sum(f["cubiertas"] for f in filas)
    porcentaje = 100 * cubiertas / total if total else 0
    resultado = {"scope": "12 archivos de núcleo de reportes/auditoría y entidades de usuario/categoría",
                 "unit_tests": len(casos), "covered": cubiertas, "statements": total,
                 "percent": round(porcentaje, 2), "minimum": 80, "passed": porcentaje >= 80, "files": filas}
    (ROOT / "reports/rf044-050-unit-gate.json").write_text(json.dumps(resultado, indent=2), encoding="utf-8")
    print(f"Nucleo RF-044..050: {cubiertas}/{total} lineas = {porcentaje:.2f}% (minimo 80%)")
    return 0 if porcentaje >= 80 else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

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

**Archivo: `tests/integration/test_reportes_administracion.py`**

```python
"""RF-044/047/050 por HTTP y persistencia real; MySQL en el gate."""
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone

from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
from src.modules.customers.models import ClienteModel
from src.modules.sales.infrastructure.persistence.django_models.pago_model import PagoModel
from tests.integration.test_rf038_050 import compra, staff

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


def datos_utilidad(total=10, costo=6):
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente reportes RF047")
    venta = compra(cliente, total=total, costo=costo)
    venta.detalles.update(producto_nombre="Pan RF047")
    return venta


def test_dashboard_del_dia_excluye_ayer_y_anuladas_y_desglosa_pagos(client):
    staff(client)
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Cliente día")
    compra(cliente, total=10)
    tarjeta = compra(cliente, total=30)
    PagoModel.objects.filter(venta=tarjeta).update(metodo="TARJETA")
    compra(cliente, total=777, dias=1)
    compra(cliente, total=999, estado="ANULADA")
    respuesta = client.get(reverse("reporting:dashboard"))
    assert respuesta.status_code == 200
    assert respuesta.context["ventas_hoy"]["total"] == 40
    assert respuesta.context["ventas_hoy"]["tickets"] == 2
    assert respuesta.context["ventas_hoy"]["metodos_pago"] == {"EFECTIVO": 10, "TARJETA": 30}


@pytest.mark.parametrize("total,costo,margen", [(10, 6, 40), (32, 31, 3.13)])
def test_utilidad_muestra_margen_por_producto_y_total(client, total, costo, margen):
    staff(client)
    datos_utilidad(total, costo)
    respuesta = client.get(reverse("reporting:utilidad"))
    assert respuesta.status_code == 200
    reporte = respuesta.context["reporte"]
    assert reporte.por_producto[0]["margen_pct"] == margen
    assert reporte.margen_pct == margen
    assert reporte.utilidad_total == total - costo
    porcentaje = f"{margen:.2f}%"
    assert porcentaje.encode() in respuesta.content or porcentaje.replace(".", ",").encode() in respuesta.content


@pytest.mark.parametrize("consulta", [
    {"pagina": "abc"}, {"pagina": "0"}, {"pagina": "-1"}, {"pagina": "1.5"},
    {"desde": "mal"}, {"hasta": "2026-02-30"},
    {"desde": "2026-10-20", "hasta": "2026-10-19"}, {"usuario_id": "no-uuid"},
])
def test_auditoria_rechaza_filtros_invalidos_sin_500(client, consulta):
    staff(client)
    client.raise_request_exception = False
    respuesta = client.get(reverse("auditing:registros"), consulta)
    assert respuesta.status_code == 400
    assert respuesta.context["form"].errors


def test_auditoria_filtra_actor_accion_y_fecha_sin_exponer_secretos(client):
    admin = staff(client)
    secreto = "NoRegistrar#DatoPrivado456"
    assert client.post(reverse("catalog:categorias"), {
        "nombre": "Categoría auditable RF050", "password": secreto, "dni": "12345678",
    }).status_code == 302
    registro = AuditoriaModel.objects.get(entidad="CategoriaModel", accion="CREAR")
    AuditoriaModel.objects.create(id=uuid4(), accion="CREAR", entidad="CategoriaModel", entidad_id=str(uuid4()),
                                 usuario_id=uuid4(), detalle={"campos": ["nombre"]})
    hoy = timezone.localdate().isoformat()
    respuesta = client.get(reverse("auditing:registros"), {"usuario_id": admin.id, "accion": "CREAR",
                          "entidad": "CategoriaModel", "desde": hoy, "hasta": hoy})
    assert respuesta.status_code == 200
    filas = respuesta.context["pagina_dto"].items
    assert len(filas) == 1
    assert filas[0].id == str(registro.id)
    assert str(filas[0].usuario_id) == admin.id
    assert filas[0].fecha
    assert secreto not in respuesta.content.decode()
    assert "12345678" not in str(filas[0].detalle)


@pytest.mark.parametrize("rol", ["CLIENTE", "CAJERO", "ALMACENERO", "GERENTE"])
def test_auditoria_solo_es_visible_para_administrador(client, rol):
    staff(client, rol)
    respuesta = client.get(reverse("auditing:registros"))
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("catalog:catalogo")
```

**Archivo: `tests/integration/test_rf030_050_contratos.py`**

```python
"""RF-045/046/048: fronteras del día local, rankings y último administrador."""
from datetime import datetime, timezone as utc
from decimal import Decimal
from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone

from src.modules.customers.models import ClienteModel
from src.modules.identity.infrastructure.factories import construir_repositorio
from src.modules.sales.models import VentaModel
from tests.integration.test_rf038_050 import compra, staff

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@timezone.override("America/Lima")
def test_reporte_incluye_dia_local_completo_y_excluye_dias_adyacentes(client):
    staff(client)
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Fronteras Lima")
    for instante, total, estado in [
        (datetime(2026, 10, 17, 4, 59, 59, 999999, tzinfo=utc.utc), 100, "PAGADA"),
        (datetime(2026, 10, 17, 5, tzinfo=utc.utc), 20, "PAGADA"),
        (datetime(2026, 10, 18, 4, 59, 59, 999999, tzinfo=utc.utc), 30, "PAGADA"),
        (datetime(2026, 10, 18, 5, tzinfo=utc.utc), 200, "PAGADA"),
        (datetime(2026, 10, 17, 12, tzinfo=utc.utc), 999, "ANULADA"),
    ]:
        venta = compra(cliente, total=total, estado=estado)
        VentaModel.objects.filter(pk=venta.id).update(fecha_creacion=instante)
    respuesta = client.get(reverse("reporting:ventas"), {"desde": "2026-10-17", "hasta": "2026-10-17"})
    assert respuesta.status_code == 200
    assert respuesta.context["reporte"].cantidad_tickets == 2
    assert respuesta.context["reporte"].total_ventas == 50
    assert respuesta.context["metodos"] == {"EFECTIVO": 50}


def sembrar_ranking():
    cliente = ClienteModel.objects.create(id=uuid4(), nombre="Ranking contrato")
    barato, caro = uuid4(), uuid4()
    mas_unidades = compra(cliente, total=10, producto_id=barato)
    mas_unidades.detalles.update(cantidad=5, precio_unitario=Decimal("2"))
    compra(cliente, total=30, producto_id=caro)
    compra(cliente, total=999, producto_id=barato, estado="ANULADA")
    return barato, caro


@pytest.mark.parametrize("orden", ["cantidad", "monto"])
def test_ranking_cambia_segun_criterio_sin_incluir_anuladas(client, orden):
    staff(client)
    barato, caro = sembrar_ranking()
    hoy = timezone.localdate().isoformat()
    respuesta = client.get(reverse("reporting:productos"), {"desde": hoy, "hasta": hoy, "orden": orden})
    assert respuesta.status_code == 200
    filas = respuesta.context["productos"]
    assert [f["producto_id"] for f in filas] == [str(p) for p in (
        (barato, caro) if orden == "cantidad" else (caro, barato)
    )]
    assert sum(f["unidades"] for f in filas) == 6
    assert sum(Decimal(str(f["ingresos"])) for f in filas) == Decimal("40")


@pytest.mark.parametrize("accion", ["desactivar", "quitar_rol"])
def test_ultimo_administrador_conserva_acceso(client, accion):
    administrador = staff(client)
    if accion == "desactivar":
        respuesta = client.post(reverse("identity:usuario_desactivar", args=[administrador.id]))
    else:
        respuesta = client.post(reverse("identity:usuario_editar", args=[administrador.id]), {
            "nombre_completo": "Administrador protegido", "email": "", "rol": "CAJERO", "password": "",
        })
    assert respuesta.status_code in (200, 302)
    actual = construir_repositorio().buscar_por_id(administrador.id)
    assert actual.activo
    assert actual.rol.value == "ADMINISTRADOR"
    assert client.get(reverse("identity:usuarios")).status_code == 200
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

**Archivo: `tests/system/test_reportes_administracion_playwright.py`**

```python
"""RF-047..050: pantalla real de utilidad, usuarios y auditoría con Chromium."""
import re

import pytest
from django.urls import reverse
from playwright.sync_api import expect

from src.modules.catalog.models import CategoriaModel
from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
from tests.integration.test_reportes_administracion import datos_utilidad
from tests.integration.test_rf038_050 import PASSWORD
from tests.system.test_e2e_pos_playwright import navegador  # noqa: F401
from tests.system.test_rf038_050_playwright import login

pytestmark = [pytest.mark.system, pytest.mark.e2e, pytest.mark.django_db(transaction=True)]


@pytest.fixture
def admin_page(navegador, live_server):
    admin = CrearUsuario(construir_repositorio(), construir_hasher()).ejecutar(UsuarioInputDTO(
        username="admin_reportes_ui", password=PASSWORD, nombre_completo="Administrador reportes", rol="ADMINISTRADOR",
    ))
    page = navegador.new_page()
    login(page, live_server, admin.username)
    return page, admin


def test_utilidad_por_producto_visible_con_margen(admin_page, live_server):
    datos_utilidad()
    page, _ = admin_page
    page.goto(live_server.url + reverse("reporting:utilidad"))
    fila = page.get_by_role("row").filter(has_text="Pan RF047")
    expect(fila).to_contain_text(re.compile(r"40[.,]00%"))
    expect(page.get_by_role("columnheader", name="Margen", exact=True)).to_be_visible()


def test_categoria_creada_editada_y_auditada_con_actor(admin_page, live_server):
    page, admin = admin_page
    page.goto(live_server.url + reverse("catalog:categorias"))
    page.locator('[name="nombre"]').fill("Categoría RF049 navegador")
    page.get_by_role("button", name="Guardar categoría", exact=True).click()
    expect(page.get_by_text("Categoría RF049 navegador", exact=False)).to_be_visible()
    categoria = CategoriaModel.objects.get(nombre="Categoría RF049 navegador")
    page.goto(live_server.url + reverse("catalog:categoria_editar", args=[categoria.id]))
    page.locator('[name="nombre"]').fill("Categoría RF049 editada")
    page.get_by_role("button", name="Guardar categoría", exact=True).click()
    page.goto(live_server.url + reverse("auditing:registros") + f"?entidad=CategoriaModel&entidad_id={categoria.id}")
    expect(page.get_by_role("cell", name="CREAR", exact=True)).to_be_visible()
    expect(page.get_by_role("cell", name="ACTUALIZAR", exact=True)).to_be_visible()
    expect(page.get_by_role("cell", name=admin.id, exact=True)).to_have_count(2)


def test_admin_crea_edita_y_desactiva_usuario_por_ui(admin_page, live_server):
    page, _ = admin_page
    page.goto(live_server.url + reverse("identity:usuario_nuevo"))
    for campo, valor in {"username": "cajero_rf048_ui", "nombre_completo": "Cajero inicial",
                         "email": "cajero-rf048@example.test", "password": PASSWORD}.items():
        page.locator(f'[name="{campo}"]').fill(valor)
    page.locator('[name="rol"]').select_option("CAJERO")
    page.get_by_role("button", name="Crear", exact=True).click()
    fila = page.get_by_role("row").filter(has_text="cajero_rf048_ui")
    expect(fila).to_contain_text("CAJERO")
    fila.get_by_role("link", name="Editar", exact=True).click()
    page.locator('[name="nombre_completo"]').fill("Gerente actualizado")
    page.locator('[name="rol"]').select_option("GERENTE")
    page.get_by_role("button", name="Guardar usuario", exact=True).click()
    fila = page.get_by_role("row").filter(has_text="cajero_rf048_ui")
    expect(fila).to_contain_text("Gerente actualizado")
    expect(fila).to_contain_text("GERENTE")
    fila.get_by_role("button", name="Desactivar", exact=True).click()
    expect(page.get_by_role("row").filter(has_text="cajero_rf048_ui")).to_contain_text("INACTIVO")
    assert not construir_repositorio().buscar_por_username("cajero_rf048_ui").activo
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

**Archivo: `tests/uat/features/reportes_administracion.feature`**

```gherkin
Feature: Reportes y administración RF-044 a RF-050
  Scenario: Consultar utilidad y margen histórico por producto
    Given un administrador con una venta de diez soles y costo histórico de seis
    When consulta el reporte de utilidad
    Then ve cuatro soles de utilidad y cuarenta por ciento de margen por producto y total

  Scenario: Rastrear creación y edición de una categoría
    Given un administrador que crea y edita una categoría
    When consulta la auditoría de esa categoría
    Then identifica ambas acciones con su actor y fecha

  Scenario: Revocar el acceso de un usuario desactivado
    Given un administrador y un cajero con sesión iniciada
    When el administrador desactiva al cajero
    Then la cuenta queda inactiva y su sesión pierde el acceso
```

**Archivo: `tests/uat/features/reportes_administracion_contratos.feature`**

```gherkin
Feature: Criterios de aceptación de reportes y usuarios RF-045 RF-046 RF-048
  Scenario: Separar ranking por volumen y por importe
    Given un administrador con cinco unidades de diez soles y una de treinta soles
    When consulta el ranking por cantidad y por monto
    Then el orden cambia y las ventas anuladas no cuentan

  Scenario: Rechazar un rango de fechas invertido
    Given un administrador de reportes autenticado
    When pide ventas desde el veinte hasta el diecinueve de octubre
    Then recibe un error de validación sin generar un reporte engañoso

  Scenario: Conservar al último administrador
    Given un único administrador activo
    When intenta desactivar su propia cuenta
    Then conserva su rol y el acceso a la gestión de usuarios
```

## 7.2 Automatización del UAT (Step Definitions) o Checklist de Validación Manual para el Product Owner / Cliente

**Archivo: `tests/uat/test_reportes_administracion_bdd.py`**

```python
import pytest
from django.test import Client
from django.urls import reverse
from pytest_bdd import given, scenarios, then, when

from src.modules.catalog.models import CategoriaModel
from src.modules.identity.infrastructure.factories import construir_repositorio
from tests.integration.test_reportes_administracion import datos_utilidad
from tests.integration.test_rf038_050 import PASSWORD, staff

pytestmark = [pytest.mark.uat, pytest.mark.django_db]
scenarios("features/reportes_administracion.feature")


@pytest.fixture
def contexto():
    return {}


@given("un administrador con una venta de diez soles y costo histórico de seis")
def venta(client):
    staff(client)
    datos_utilidad()


@when("consulta el reporte de utilidad")
def utilidad(client, contexto):
    contexto["respuesta"] = client.get(reverse("reporting:utilidad"))


@then("ve cuatro soles de utilidad y cuarenta por ciento de margen por producto y total")
def margen(contexto):
    assert contexto["respuesta"].status_code == 200
    reporte = contexto["respuesta"].context["reporte"]
    assert reporte.utilidad_total == reporte.por_producto[0]["utilidad"] == 4
    assert reporte.margen_pct == reporte.por_producto[0]["margen_pct"] == 40


@given("un administrador que crea y edita una categoría")
def categoria(client, contexto):
    contexto["admin"] = staff(client)
    assert client.post(reverse("catalog:categorias"), {"nombre": "Categoría UAT RF049"}).status_code == 302
    categoria = CategoriaModel.objects.get(nombre="Categoría UAT RF049")
    contexto["categoria"] = categoria
    assert client.post(reverse("catalog:categoria_editar", args=[categoria.id]), {
        "nombre": "Categoría UAT editada", "descripcion": "Prueba de trazabilidad",
    }).status_code == 302


@when("consulta la auditoría de esa categoría")
def consultar_auditoria(client, contexto):
    contexto["respuesta"] = client.get(reverse("auditing:registros"), {
        "entidad": "CategoriaModel", "entidad_id": str(contexto["categoria"].id),
    })


@then("identifica ambas acciones con su actor y fecha")
def trazabilidad(contexto):
    respuesta = contexto["respuesta"]
    assert respuesta.status_code == 200
    eventos = respuesta.context["pagina_dto"].items
    assert {e.accion for e in eventos} == {"CREAR", "ACTUALIZAR"}
    assert all(str(e.usuario_id) == contexto["admin"].id and e.fecha for e in eventos)


@given("un administrador y un cajero con sesión iniciada")
def usuario(client, contexto):
    staff(client)
    assert client.post(reverse("identity:usuario_nuevo"), {
        "username": "cajero_uat_rf048", "nombre_completo": "Cajero UAT", "rol": "CAJERO", "password": PASSWORD,
    }).status_code == 302
    contexto["usuario"] = construir_repositorio().buscar_por_username("cajero_uat_rf048")
    contexto["cajero"] = Client()
    assert contexto["cajero"].post(reverse("identity:login"), {
        "username": "cajero_uat_rf048", "password": PASSWORD,
    }).status_code == 302


@when("el administrador desactiva al cajero")
def desactivar(client, contexto):
    assert client.post(reverse("identity:usuario_desactivar", args=[contexto["usuario"].id])).status_code == 302


@then("la cuenta queda inactiva y su sesión pierde el acceso")
def sin_acceso(contexto):
    assert not construir_repositorio().buscar_por_id(contexto["usuario"].id).activo
    respuesta = contexto["cajero"].get(reverse("catalog:catalogo"))
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("identity:login")
    assert "usuario_id" not in contexto["cajero"].session
```

**Archivo: `tests/uat/test_reportes_administracion_contratos_bdd.py`**

```python
"""Aceptación ejecutable adicional para RF-045/046/048."""
import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_bdd import given, scenarios, then, when

from src.modules.identity.infrastructure.factories import construir_repositorio
from tests.integration.test_rf030_050_contratos import sembrar_ranking
from tests.integration.test_rf038_050 import staff

pytestmark = [pytest.mark.uat, pytest.mark.django_db]
scenarios("features/reportes_administracion_contratos.feature")


@pytest.fixture
def contexto():
    return {}


@given("un administrador de reportes autenticado")
@given("un único administrador activo")
def administrador(client, contexto):
    contexto["administrador"] = staff(client)


@given("un administrador con cinco unidades de diez soles y una de treinta soles")
def ranking(client, contexto):
    administrador(client, contexto)
    contexto["barato"], contexto["caro"] = sembrar_ranking()


@when("consulta el ranking por cantidad y por monto")
def consultar_ranking(client, contexto):
    hoy = timezone.localdate().isoformat()
    contexto["rankings"] = {
        orden: client.get(reverse("reporting:productos"), {"desde": hoy, "hasta": hoy, "orden": orden})
        for orden in ("cantidad", "monto")
    }


@then("el orden cambia y las ventas anuladas no cuentan")
def ranking_correcto(contexto):
    for orden, esperado in (("cantidad", contexto["barato"]), ("monto", contexto["caro"])):
        respuesta = contexto["rankings"][orden]
        assert respuesta.status_code == 200
        filas = respuesta.context["productos"]
        assert filas[0]["producto_id"] == str(esperado)
        assert sum(f["unidades"] for f in filas) == 6
        assert sum(f["ingresos"] for f in filas) == 40


@when("pide ventas desde el veinte hasta el diecinueve de octubre")
def rango_invertido(client, contexto):
    contexto["respuesta"] = client.get(reverse("reporting:ventas"), {
        "desde": "2026-10-20", "hasta": "2026-10-19",
    })


@then("recibe un error de validación sin generar un reporte engañoso")
def rango_rechazado(contexto):
    respuesta = contexto["respuesta"]
    assert respuesta.status_code == 400
    assert respuesta.context["form"].errors
    assert "reporte" not in respuesta.context


@when("intenta desactivar su propia cuenta")
def desactivar(client, contexto):
    contexto["respuesta"] = client.post(reverse("identity:usuario_desactivar", args=[contexto["administrador"].id]))


@then("conserva su rol y el acceso a la gestión de usuarios")
def administrador_protegido(client, contexto):
    actual = construir_repositorio().buscar_por_id(contexto["administrador"].id)
    assert contexto["respuesta"].status_code == 302
    assert actual.activo
    assert actual.rol.value == "ADMINISTRADOR"
    assert client.get(reverse("identity:usuarios")).status_code == 200
```

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

**Archivo: `../.cursor/rules/reporting-admin-testing.mdc`**

```markdown
---
description: Contratos y pruebas del módulo 3.6 RF-044 a RF-050
globs: puntoventa_total/src/modules/reporting/**/*.py,puntoventa_total/src/modules/auditing/**/*.py,puntoventa_total/templates/dashboard/*.html,puntoventa_total/templates/auditing/*.html,puntoventa_total/tests/**/*reportes_administracion*
alwaysApply: false
---

Lee puntoventa_total/docs/requirements/reportes_admin_rf044_rf050.md y
puntoventa_total/docs/testing/plan_maestro_rf044_050.md antes de modificar estos contratos.

- Prueba dominio/aplicación con pytest y mocks de puertos; prohíbe ORM en Unit.
- Ventas y utilidad solo incluyen PAGADA. Conserva fechas locales de America/Lima y costos históricos.
- Margen sobre ventas = utilidad/ingresos*100, no recargo sobre costo. Redondea HALF_UP a dos decimales.
- Si faltan costos o ingresos del producto son cero, el margen de la fila no está disponible.
- No sumes porcentajes de productos para calcular el margen global: pondera sus ingresos/costos.
- Reportes permiten ADMINISTRADOR/GERENTE; usuarios y auditoría exigen ADMINISTRADOR.
- Mantén al último administrador y revoca sesiones ante cambio de rol o desactivación.
- Auditoría debe aceptar CREAR/ACTUALIZAR/ELIMINAR emitidos por el middleware y rechazar acciones arbitrarias.
- Valida fechas, UUID de actor y página de auditoría; entrada inválida devuelve 400. No captures secretos del request.
- Reproduce el fallo antes de cambiar expectativas y prueba actor, acción y fecha después de una mutación real.
- Ejecuta Unit, MySQL efímero, Chromium/k6 y UAT; conserva JUnit, cobertura y traces privados.
- Ejecuta scripts/qa_reportes_unit_gate.py después de la cobertura unitaria: incluye archivos no importados.
- No reduzcas umbrales, no omitas casos y no reintentes hasta conseguir verde. Documenta el diagnóstico.
- Usa rtk para shell. CI remoto, Testcontainers ejecutado y aceptación del PO requieren evidencia propia.
```

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
      QA_REQUIRE_ALL_TESTS: '1'
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
      - name: Reporting and auditing core unit coverage gate
        run: python scripts/qa_reportes_unit_gate.py --junit reports/full-unit.xml
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
        run: python scripts/qa_inventory_mysql.py tests/uat --junitxml=reports/full-uat.xml
      - name: Global coverage gate (all levels)
        env:
          QA_REQUIRE_ALL_TESTS: '1'
        run: python scripts/qa_inventory_mysql.py tests --runxfail --cov=src --cov-fail-under=80 --cov-report=xml:reports/full-coverage.xml --junitxml=reports/full-suite.xml
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: full-quality-evidence-${{ matrix.profile }}
          path: puntoventa_total/reports/
          retention-days: 7
```

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

Unit: 337 pruebas; cobertura del núcleo explícito: **87.85%**, 217/247 líneas; mínimo 80%.

| Perfil | Unit | Cobertura del núcleo | Integración | Sistema/carga | UAT | Fallos / errores / omitidas | Reportes HTTP p95 |
|---|---|---|---|---|---|---|---|

| qa | 337 | 87.76% | 48 | 4 | 6 | 0 / 0 / 0 | 40.06 ms |

| production | 337 | 87.85% | 48 | 4 | 6 | 0 / 0 / 0 | 43.17 ms |

Unit Test Ready → ✅ Listo. Integration Ready → ✅ Listo con MySQL nativo efímero. System/E2E Ready → ✅ Listo para los flujos y smoke de carga probados. UAT/Business Ready → ⚠ Aprobación formal del PO pendiente; automatización aprobada.

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
