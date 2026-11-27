# 1. ANÁLISIS DE CAJA BLANCA Y GRAFO DE FLUJO DE LA FUNCIÓN

## 1.1 Inventario de la Función Analizada

El bloque de código del enunciado estaba vacío. Se seleccionó un coordinador complejo y crítico del proyecto, sin afirmar que sea el máximo global de complejidad.

| Elemento | Valor |
|---|---|
| Proyecto ABP | PuntoVenta Total |
| Archivo | `src/modules/sales/application/use_cases/procesar_pago.py` |
| Método | `ProcesarPago.ejecutar(self, datos: ProcesarPagoDTO) -> dict` |
| Propósito | Registrar pagos, preparar promociones, distinguir saldo pendiente y cerrar ventas descontando stock y registrando auditoría |
| Lenguaje / framework | Python; Django en infraestructura |
| Ejecución verificada | Python 3.14.7; Pytest, pytest-cov y coverage.py |
| Alcance | Base estructural aislada; ampliación con agregado real, orden de efectos, fallos de colaboradores y rollback de BD con adaptadores reales |

## 1.2 Modelo del Grafo de Control

Modelo intraprocedimental con cortocircuitos descompuestos. Se usa una salida común para los retornos y el `raise` explícito. Las excepciones implícitas de constructores, puertos y contexto transaccional no se incorporan como decisiones; no es un CFG de excepciones completo. `with` por sí mismo no añade un predicado en esta convención.

| Nodo | Bloque / decisión |
|---|---|
| 1 | Entrada |
| 2 | Entrar en UoW y buscar agregado |
| 3 | ¿Agregado es None? |
| 4 | Importar y lanzar VentaNoEncontrada |
| 5 | verificar_modificable |
| 6 | ¿Hay puerto de promociones? |
| 7 | Importar, construir y aplicar PrepararBeneficiosVenta |
| 8 | Capturar total y preparar argumentos iniciales del pago |
| 9 | ¿monto_entregado is not None? |
| 10 | ¿metodo == EFECTIVO? |
| 11 | Construir Monto del vuelto |
| 12 | Usar vuelto None |
| 13 | Construir Pago y registrar_pago |
| 14 | ¿saldo_pendiente > 0? |
| 15 | Guardar y devolver PENDIENTE |
| 16 | Preparar referencia e iterador de líneas |
| 17 | ¿Existe siguiente línea? |
| 18 | ¿requiere_stock? |
| 19 | ¿cantidad > 0? |
| 20 | Descontar inventario |
| 21 | Cerrar, guardar y auditar venta |
| 22 | ¿pago.vuelto es verdadero? |
| 23 | Convertir vuelto a float |
| 24 | Usar 0.0 |
| 25 | Devolver venta pagada |
| 26 | Salida común |

```text
1→2→3
3 T→4→26; 3 F→5→6
6 T→7→8; 6 F→8
8→9; 9 T→10; 9 F→12
10 T→11→13; 10 F→12→13
13→14; 14 T→15→26; 14 F→16→17
17 T→18; 17 F→21→22
18 T→19; 18 F→17
19 T→20→17; 19 F→17
22 T→23→25; 22 F→24→25
25→26
```

# 2. CÁLCULO DE LA COMPLEJIDAD CICLOMÁTICA (FÓRMULA DE MCCABE)

| Estructura | Predicados |
|---|---:|
| if agregado is None | 1 |
| if promociones is not None | 1 |
| Expresión condicional del vuelto + and | 2 |
| if saldo_pendiente > 0 | 1 |
| for linea in agregado.lineas | 1 |
| if requiere_stock and cantidad > 0 | 2 |
| Expresión condicional al devolver vuelto | 1 |
| **P total** | **9** |

**V(G) = P + 1 = 10.** Comprobación: **E − N + 2C = 34 − 26 + 2×1 = 10**, donde C es el número de componentes conexas. No confundir P de predicados con P de componentes en otras notaciones.

La base estructural requiere **10 caminos independientes** para este CFG; no implica que 10 pruebas garanticen todos los valores o todas las secuencias de un bucle. La suite añade casos de regresión. El script construye vectores de frecuencia de aristas y verifica rango 10 mediante eliminación gaussiana racional.

# 3. DISEÑO DE LA MATRIZ DE CASOS DE PRUEBA (CAJA BLANCA)

Valores comunes: venta `venta-11`, total 10 PEN, método EFECTIVO, monto 10, sin promociones y entrega None salvo indicación. El saldo es la respuesta del agregado aislado.

| ID Caso | Camino / Rama Evaluada | Valores de Entrada | Condición Evaluada | Resultado Esperado |
|---|---|---|---|---|
| B01 | Venta ausente | repo devuelve None | 3 T | VentaNoEncontrada; ningún efecto de escritura |
| B02 | Parcial sin promoción | saldo=4.25 | 3 F, 6 F, 9 F, 14 T | PENDIENTE, saldo 4.25; guardar una vez |
| B03 | Parcial con promoción | saldo=4.25; puerto Mock | 6 T | aplicar(agregado) antes de terminar como parcial |
| B04 | Parcial con efectivo entregado | saldo=4.25; entrega=12 | 9 T, 10 T | Pago con vuelto Decimal('2.00') |
| B05 | Entrega indicada con tarjeta | saldo=4.25; TARJETA; entrega=12 | 9 T, 10 F | Pago sin vuelto |
| B06 | Completo sin iteraciones | saldo=0; líneas=[] | 14 F, 17 F, 22 F | PAGADA; no descontar; auditar una vez |
| B07 | Línea con stock | saldo=0; requiere_stock=True; cantidad=1 | 17 T, 18 T, 19 T | descontar(producto-11,1,VENTA:S11-001,cajero-11) |
| B08 | Línea sin stock | requiere_stock=False; cantidad=1 | 18 F | No descontar; sí cerrar y auditar |
| B09 | Cantidad cero defensiva | requiere_stock=True; cantidad=0 | 19 F | No descontar; sí cerrar en el agregado aislado |
| B10 | Completo con vuelto | saldo=0; líneas=[]; entrega=12 | 22 T | vuelto=2.0 |
| R01 | Varias iteraciones y vuelto cero | tres líneas de B07–B09; entrega=10 | mezcla de guardas | Un solo descuento; vuelto=0.0 |
| R02–R04 | Precisión monetaria | (monto,entrega)=(0.1,0.3),(8.5,10),(10,10) | Constructor Monto real | Decimal 0.20, 1.50, 0.00 |
| R05 | Efectivo insuficiente | monto=10; entrega=9 | Monto negativo | ValidationException; ninguna escritura |
| A01 | Contraejemplo de refactorización | monto=10; entrega=0 | is not None frente a truthiness | Original rechaza; propuesta insegura devuelve None |
| A02 | Contraejemplo de redondeo | 1.005 | Decimal HALF_UP frente a round(float) | 1.01 frente a 1.00 |
| E01–E02 | Venta ya cerrada | estados PAGADA y ANULADA | verificar_modificable | VentaNoModificable; sin pagos ni escrituras |
| E03–E08 | Excepciones de colaboradores | Fallo en buscar, promociones, inventario, cerrar, guardar o auditar | Salida excepcional del UoW | Misma excepción propagada; no ejecutar etapas posteriores |
| E09 | Orden observable | Dos productos; promociones presentes | Secuencia de llamadas | Promociones antes de pago; stock antes de cierre, guardado y auditoría |
| E10 | Agregado real y pagos sucesivos | Pagos 7 y 13; tercer intento 1 | Parcial, completo y venta cerrada | Dos pagos; un descuento por producto; rechazar tercero |
| E11 | Fallo de guardado parcial | Pago 7 y excepción al guardar | Retorno parcial interrumpido | Sin stock ni auditoría; excepción llega a __exit__ |
| E12 | Agregado real vacío | Sin productos; pago 20 | Invariante de registrar_pago | VentaException; sin escrituras |
| I01–I06 | Rollback de cobro completo | Fallo tras segundo descuento, guardar o auditar; dos tipos de UoW | Escrituras reales y excepción | Snapshot de siete tablas restaurado; reintento único exitoso |
| I07 | Pagos persistidos sucesivos | 7, 13 y tercer intento 1 | Recarga por repositorio entre pagos | Dos pagos; stock 19 por producto; una auditoría; rechazar tercero |
| I08–I09 | Rollback parcial | Guardar pago 7 y fallar; dos tipos de UoW | Escritura parcial real | Snapshot restaurado; reintento guarda un solo pago |

**Límite de factibilidad:** B06/B10 aíslan el bucle vacío, aunque el agregado real rechaza cobrar sin productos. B09 modifica un DetalleVenta construido correctamente para ejercitar una guarda defensiva: su constructor no admite cantidad cero. Son caminos del método aislado, no ventas válidas de extremo a extremo. No se afirma que los diez caminos sean factibles bajo todas las invariantes del agregado real.

Los recorridos completos de B01–B10 están en `reports/semana11-estructura.json`, clave `paths`; las aristas, en `edges_list`.

# 4. CÓDIGO COMPLETO DE LAS PRUEBAS EN EL FRAMEWORK xUnit

Archivos: `tests/unit/application/test_semana11_procesar_pago.py`, `tests/unit/application/test_semana11_fallos_cobro.py` y `tests/integration/test_semana11_rollback_cobro.py`. Desde `puntoventa_total`, en PowerShell:

```powershell
rtk proxy .venv/Scripts/python.exe -m pytest tests/unit/application/test_semana11_procesar_pago.py tests/unit/application/test_semana11_fallos_cobro.py tests/integration/test_semana11_rollback_cobro.py -q -p no:cacheprovider --cov=src.modules.sales.application.use_cases.procesar_pago --cov-branch --cov-fail-under=100 --cov-report=term-missing --cov-report=json:reports/semana11-cobertura.json --cov-report=html:reports/semana11-html --junitxml=reports/semana11-pruebas.xml
rtk proxy .venv/Scripts/python.exe scripts/qa_inventory_mysql_native.py --basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --target tests/integration/test_semana11_rollback_cobro.py --report-prefix semana11-rollback-mysql
rtk proxy .venv/Scripts/python.exe scripts/qa_semana11_caja_blanca.py
rtk proxy .venv/Scripts/python.exe -m ruff check scripts/qa_semana11_caja_blanca.py tests/unit/application/test_semana11_procesar_pago.py tests/unit/application/test_semana11_fallos_cobro.py tests/integration/test_semana11_rollback_cobro.py
```

Código completo ejecutado:

```python
"""Caja blanca del coordinador de cobro; puertos y agregado aislados con mocks."""
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.ports.auditoria_port import AuditoriaPort
from src.modules.sales.application.ports.inventario_port import InventarioPort
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.detalle_venta import DetalleVenta
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoEncontrada
from src.modules.sales.domain.repositories.venta_repository import VentaRepository
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


@pytest.fixture
def cobro():
    agregado = Mock(spec=VentaAggregate)
    agregado.venta = Venta(cajero_id="cajero-11", numero_ticket="S11-001")
    agregado.venta.total = 10.0
    agregado.lineas = []
    agregado.saldo_pendiente.return_value = Decimal("0")
    agregado.cerrar.side_effect = lambda: setattr(agregado.venta, "estado", EstadoVenta.PAGADA)
    repo, inventario, auditoria = Mock(spec=VentaRepository), Mock(spec=InventarioPort), Mock(spec=AuditoriaPort)
    repo.buscar_por_id.return_value = agregado
    return agregado, repo, inventario, auditoria


def datos(metodo="EFECTIVO", entregado=None, monto=10.0):
    return ProcesarPagoDTO("venta-11", metodo, monto, entregado, "operacion-11")


def linea(requiere_stock=True, cantidad=1):
    detalle = DetalleVenta(producto_id="producto-11", producto_nombre="Arroz", precio_unitario=Monto(10))
    detalle.requiere_stock = requiere_stock
    # Estado sintetico para comprobar la guarda defensiva; el constructor rechaza cero.
    detalle.cantidad = cantidad
    return detalle


def test_b01_venta_inexistente(cobro):
    agregado, repo, inventario, auditoria = cobro
    repo.buscar_por_id.return_value = None
    with pytest.raises(VentaNoEncontrada):
        ProcesarPago(repo, inventario, auditoria).ejecutar(datos())
    agregado.registrar_pago.assert_not_called()
    repo.guardar.assert_not_called()
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()


@pytest.mark.parametrize("promociones,metodo,entregado,vuelto", [
    (False, "EFECTIVO", None, None),  # B02
    (True, "EFECTIVO", None, None),   # B03
    (False, "EFECTIVO", 12.0, Decimal("2.00")),  # B04
    (False, "TARJETA", 12.0, None),  # B05: segundo operando del and falso
], ids=["B02", "B03", "B04", "B05"])
def test_pago_parcial(cobro, promociones, metodo, entregado, vuelto):
    agregado, repo, inventario, auditoria = cobro
    agregado.saldo_pendiente.return_value = Decimal("4.25")
    puerto_promociones = Mock() if promociones else None
    with patch("src.modules.sales.application.use_cases.preparar_beneficios.PrepararBeneficiosVenta") as preparar:
        resultado = ProcesarPago(repo, inventario, auditoria, promociones=puerto_promociones).ejecutar(
            datos(metodo, entregado)
        )
    assert resultado == {"estado": "PENDIENTE", "saldo": 4.25}
    pago = agregado.registrar_pago.call_args.args[0]
    assert (pago.vuelto.valor if pago.vuelto is not None else None) == vuelto
    assert pago.metodo.tipo == metodo
    assert pago.monto == Monto(10)
    if promociones:
        preparar.assert_called_once_with(repo, puerto_promociones)
        preparar.return_value.aplicar.assert_called_once_with(agregado)
    else:
        preparar.assert_not_called()
    repo.guardar.assert_called_once_with(agregado)
    agregado.cerrar.assert_not_called()
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()


@pytest.mark.parametrize("lineas,entregado,descuentos,vuelto", [
    ([], None, 0, 0.0),  # B06: agregado sintetico vacio, salida inmediata del bucle
    ([linea()], None, 1, 0.0),  # B07
    ([linea(False)], None, 0, 0.0),  # B08
    ([linea(cantidad=0)], None, 0, 0.0),  # B09: guarda defensiva
    ([], 12.0, 0, 2.0),  # B10
    ([linea(), linea(False), linea(cantidad=0)], 10.0, 1, 0.0),  # R01
], ids=["B06", "B07", "B08", "B09", "B10", "R01"])
def test_pago_completo(cobro, lineas, entregado, descuentos, vuelto):
    agregado, repo, inventario, auditoria = cobro
    agregado.lineas = lineas
    resultado = ProcesarPago(repo, inventario, auditoria).ejecutar(datos(entregado=entregado))
    assert resultado == {"estado": "PAGADA", "total": 10.0, "vuelto": vuelto, "numero_ticket": "S11-001"}
    assert inventario.descontar.call_count == descuentos
    if descuentos:
        inventario.descontar.assert_called_once_with("producto-11", 1, "VENTA:S11-001", "cajero-11")
    agregado.cerrar.assert_called_once_with()
    repo.guardar.assert_called_once_with(agregado)
    auditoria.registrar.assert_called_once_with(
        accion="VENTA_PAGADA", entidad="Venta", entidad_id=str(agregado.venta.id), usuario_id="cajero-11",
        detalle={"total": 10.0, "metodo": "EFECTIVO", "numero_ticket": "S11-001"},
    )


@pytest.mark.parametrize("monto,entregado,esperado", [
    (0.1, 0.3, "0.20"), (8.5, 10.0, "1.50"), (10.0, 10.0, "0.00"),
])
def test_regresion_redondeo_vuelto(cobro, monto, entregado, esperado):
    agregado, repo, inventario, auditoria = cobro
    resultado = ProcesarPago(repo, inventario, auditoria).ejecutar(datos(entregado=entregado, monto=monto))
    assert agregado.registrar_pago.call_args.args[0].vuelto.valor == Decimal(esperado)
    assert resultado["vuelto"] == float(esperado)


def test_efectivo_insuficiente_no_guarda(cobro):
    agregado, repo, inventario, auditoria = cobro
    with pytest.raises(ValidationException):
        ProcesarPago(repo, inventario, auditoria).ejecutar(datos(entregado=9.0))
    agregado.registrar_pago.assert_not_called()
    repo.guardar.assert_not_called()
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()


def vuelto_propuesto_ia(pago_datos, moneda):
    """Propuesta deliberadamente incorrecta; nunca se incorpora a produccion."""
    return (
        Monto(pago_datos.monto_entregado - pago_datos.monto, moneda)
        if pago_datos.monto_entregado and pago_datos.metodo == "EFECTIVO" else None
    )


def test_auditoria_rechaza_simplificacion_por_truthiness(cobro):
    _, repo, inventario, auditoria = cobro
    pago_datos = datos(entregado=0.0)
    assert vuelto_propuesto_ia(pago_datos, "PEN") is None
    with pytest.raises(ValidationException):
        ProcesarPago(repo, inventario, auditoria).ejecutar(pago_datos)
    repo.guardar.assert_not_called()


def test_auditoria_rechaza_redondeo_binario():
    assert Monto(Decimal("1.005")).valor == Decimal("1.01")
    assert Decimal(str(round(1.005, 2))) == Decimal("1.00")
```

Código completo de la ampliación de fallos, orden y agregado real:

```python
"""Rutas excepcionales, orden observable y pagos sucesivos del cobro."""
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.enums.estado_venta import EstadoVenta
from src.modules.sales.domain.exceptions.venta_exceptions import VentaException, VentaNoModificable
from src.shared.application.interfaces.unit_of_work import UnitOfWork
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


@pytest.fixture
def entorno():
    agregado = VentaAggregate(Venta(numero_ticket="S11-FALLOS", cajero_id="cajero"))
    agregado.agregar_producto("p1", "Arroz", 1, Monto(10))
    agregado.agregar_producto("p2", "Aceite", 1, Monto(10))
    agregado.calcular_totales()
    repo, inventario, auditoria = Mock(), Mock(), Mock()
    repo.buscar_por_id.return_value = agregado
    uow = MagicMock(spec=UnitOfWork)
    uow.__exit__.return_value = False
    return agregado, repo, inventario, auditoria, uow


def dto(monto=20):
    return ProcesarPagoDTO("venta", "EFECTIVO", monto, monto)


@pytest.mark.parametrize("estado", [EstadoVenta.PAGADA, EstadoVenta.ANULADA])
def test_venta_cerrada_no_admite_otro_pago(entorno, estado):
    agregado, repo, inventario, auditoria, uow = entorno
    agregado.venta.estado = estado
    with pytest.raises(VentaNoModificable) as error:
        ProcesarPago(repo, inventario, auditoria, uow).ejecutar(dto())
    assert agregado.pagos == []
    repo.guardar.assert_not_called()
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()
    assert uow.__exit__.call_args.args[:2] == (VentaNoModificable, error.value)


@pytest.mark.parametrize("etapa", ["buscar", "promociones", "inventario", "cerrar", "guardar", "auditar"])
def test_propaga_fallo_y_entrega_excepcion_al_uow(entorno, etapa):
    agregado, repo, inventario, auditoria, uow = entorno
    fallo = RuntimeError(f"Fallo controlado: {etapa}")
    with patch("src.modules.sales.application.use_cases.preparar_beneficios.PrepararBeneficiosVenta") as preparar:
        if etapa == "buscar":
            repo.buscar_por_id.side_effect = fallo
        elif etapa == "promociones":
            preparar.return_value.aplicar.side_effect = fallo
        elif etapa == "inventario":
            inventario.descontar.side_effect = [None, fallo]
        elif etapa == "cerrar":
            agregado.cerrar = Mock(side_effect=fallo)
        elif etapa == "guardar":
            repo.guardar.side_effect = fallo
        else:
            auditoria.registrar.side_effect = fallo
        with pytest.raises(RuntimeError) as error:
            ProcesarPago(repo, inventario, auditoria, uow, promociones=Mock()).ejecutar(dto())
    assert error.value is fallo
    uow.__enter__.assert_called_once_with()
    tipo, excepcion, traceback = uow.__exit__.call_args.args
    assert tipo is RuntimeError and excepcion is fallo and traceback is not None
    if etapa in ("buscar", "promociones"):
        assert agregado.pagos == []
        inventario.descontar.assert_not_called()
    if etapa in ("buscar", "promociones", "inventario", "cerrar"):
        repo.guardar.assert_not_called()
    if etapa != "auditar":
        auditoria.registrar.assert_not_called()
    if etapa == "inventario":
        assert agregado.venta.estado is EstadoVenta.BORRADOR
        assert inventario.descontar.call_count == 2


def test_orden_de_operaciones_exacto(entorno):
    agregado, repo, inventario, auditoria, uow = entorno
    eventos = []
    uow.__enter__.side_effect = lambda: eventos.append("entrar")
    uow.__exit__.side_effect = lambda *args: eventos.append("salir")
    repo.buscar_por_id.side_effect = lambda _: eventos.append("buscar") or agregado
    verificar, registrar, cerrar = agregado.venta.verificar_modificable, agregado.registrar_pago, agregado.cerrar
    agregado.venta.verificar_modificable = Mock(side_effect=lambda: (eventos.append("verificar"), verificar())[1])
    agregado.registrar_pago = Mock(side_effect=lambda pago: (eventos.append("pago"), registrar(pago))[1])
    agregado.cerrar = Mock(side_effect=lambda: (eventos.append("cerrar"), cerrar())[1])
    inventario.descontar.side_effect = lambda producto, *args: eventos.append(f"stock:{producto}")
    repo.guardar.side_effect = lambda _: eventos.append("guardar")
    auditoria.registrar.side_effect = lambda **kwargs: eventos.append("auditar")
    with patch("src.modules.sales.application.use_cases.preparar_beneficios.PrepararBeneficiosVenta") as preparar:
        preparar.return_value.aplicar.side_effect = lambda _: eventos.append("promociones")
        ProcesarPago(repo, inventario, auditoria, uow, promociones=Mock()).ejecutar(dto())
    assert eventos == ["entrar", "buscar", "verificar", "promociones", "pago", "stock:p1", "stock:p2",
                       "cerrar", "guardar", "auditar", "salir"]


def test_dos_pagos_reales_cierran_y_descuentan_una_sola_vez(entorno):
    agregado, repo, inventario, auditoria, uow = entorno
    caso = ProcesarPago(repo, inventario, auditoria, uow)
    assert caso.ejecutar(dto(7)) == {"estado": "PENDIENTE", "saldo": 13.0}
    assert agregado.venta.estado is EstadoVenta.BORRADOR
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()
    resultado = caso.ejecutar(dto(13))
    assert resultado["estado"] == "PAGADA"
    assert agregado.total_pagado() == Monto(20).valor
    assert agregado.saldo_pendiente() == 0
    assert len(agregado.pagos) == 2
    assert inventario.descontar.call_count == 2  # una llamada por cada producto
    auditoria.registrar.assert_called_once()
    assert repo.guardar.call_count == 2
    with pytest.raises(VentaNoModificable):
        caso.ejecutar(dto(1))
    assert len(agregado.pagos) == 2
    assert inventario.descontar.call_count == 2
    auditoria.registrar.assert_called_once()


def test_fallo_al_guardar_pago_parcial_no_toca_stock(entorno):
    _, repo, inventario, auditoria, uow = entorno
    fallo = RuntimeError("No se pudo guardar el pago parcial")
    repo.guardar.side_effect = fallo
    with pytest.raises(RuntimeError) as error:
        ProcesarPago(repo, inventario, auditoria, uow).ejecutar(dto(7))
    assert error.value is fallo
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()
    assert uow.__exit__.call_args.args[:2] == (RuntimeError, fallo)


def test_agregado_real_sin_productos_rechaza_el_pago(entorno):
    agregado, repo, inventario, auditoria, uow = entorno
    agregado.lineas.clear()
    with pytest.raises(VentaException, match="sin productos"):
        ProcesarPago(repo, inventario, auditoria, uow).ejecutar(dto())
    assert agregado.pagos == []
    repo.guardar.assert_not_called()
    inventario.descontar.assert_not_called()
    auditoria.registrar.assert_not_called()
```

Código completo de las pruebas transaccionales con base de datos:

```python
"""Rollback durable del cobro con repositorios y adaptadores reales."""
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import connection, transaction

from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
from src.modules.catalog.models import ProductoModel
from src.modules.inventory.models import ExistenciaModel, LoteModel, MovimientoModel
from src.modules.sales.application.dto.venta_input import ProcesarPagoDTO
from src.modules.sales.application.use_cases.procesar_pago import ProcesarPago
from src.modules.sales.domain.aggregates.venta_aggregate import VentaAggregate
from src.modules.sales.domain.entities.venta import Venta
from src.modules.sales.domain.exceptions.venta_exceptions import VentaNoModificable
from src.modules.sales.infrastructure.adapters.inventario_adapter import InventarioAdapter
from src.modules.sales.infrastructure.auditing.auditoria_adapter import AuditoriaAdapter
from src.modules.sales.infrastructure.persistence.django_models.detalle_venta_model import DetalleVentaModel
from src.modules.sales.infrastructure.persistence.django_models.pago_model import PagoModel
from src.modules.sales.infrastructure.persistence.django_models.venta_model import VentaModel
from src.modules.sales.infrastructure.persistence.repositories.django_venta_repository import (
    DjangoVentaRepository,
)
from src.shared.domain.value_objects.monto import Monto
from src.shared.infrastructure.database.mysql_unit_of_work import MySQLUnitOfWork

pytestmark = [pytest.mark.integration, pytest.mark.django_db(transaction=True)]


@pytest.fixture
def venta_persistida():
    agregado = VentaAggregate(Venta(numero_ticket=f"S11-{uuid4().hex[:12]}", cajero_id=str(uuid4())))
    for indice in range(2):
        producto = ProductoModel.objects.create(
            id=uuid4(), nombre=f"Producto S11 {indice}", codigo_barras=f"775{uuid4().int % 10**10:010d}",
            costo=Decimal("5"), precio_venta=Decimal("10"), estado="ACTIVO", requiere_stock=True,
        )
        ExistenciaModel.objects.create(id=uuid4(), producto_id=producto.id, cantidad=20, reservada=0)
        LoteModel.objects.create(
            id=uuid4(), producto_id=producto.id, numero_lote=f"S11-{indice}", cantidad_inicial=20,
            cantidad_restante=20, fecha_recepcion=date.today(),
        )
        agregado.agregar_producto(str(producto.id), producto.nombre, 1, Monto(10))
    agregado.calcular_totales()
    DjangoVentaRepository().guardar(agregado)
    assert not connection.in_atomic_block  # la semilla ya esta confirmada
    return str(agregado.venta.id)


def snapshot():
    modelos = (VentaModel, DetalleVentaModel, PagoModel, ExistenciaModel, LoteModel, MovimientoModel, AuditoriaModel)
    return {modelo._meta.label: list(modelo.objects.order_by("pk").values()) for modelo in modelos}


@pytest.mark.parametrize("tipo_uow", ["atomic", "mysql_uow"])
@pytest.mark.parametrize("etapa", ["inventario", "guardar", "auditar"])
def test_fallo_restaura_toda_la_bd_y_permite_reintentar(venta_persistida, tipo_uow, etapa):
    antes = snapshot()
    repo, inventario, auditoria = DjangoVentaRepository(), InventarioAdapter(), AuditoriaAdapter()
    uow = transaction.atomic() if tipo_uow == "atomic" else MySQLUnitOfWork()
    llamadas = []
    objeto, metodo = {
        "inventario": (inventario, "descontar"), "guardar": (repo, "guardar"), "auditar": (auditoria, "registrar"),
    }[etapa]
    original = getattr(objeto, metodo)
    fallo = RuntimeError(f"Fallo despues de escribir: {etapa}")

    def escribir_y_fallar(*args, **kwargs):
        resultado = original(*args, **kwargs)
        llamadas.append(1)
        # Fallar tras escribir el segundo producto prueba el rollback del bucle completo.
        if etapa != "inventario" or len(llamadas) == 2:
            assert snapshot() != antes
            raise fallo
        return resultado

    datos = ProcesarPagoDTO(venta_persistida, "EFECTIVO", 20, 20)
    with patch.object(objeto, metodo, side_effect=escribir_y_fallar), pytest.raises(RuntimeError) as error:
        ProcesarPago(repo, inventario, auditoria, uow).ejecutar(datos)
    assert error.value is fallo
    assert len(llamadas) == (2 if etapa == "inventario" else 1)
    assert not connection.in_atomic_block
    assert snapshot() == antes  # incluye pagos, estado, lotes, existencias, kardex y auditoria

    # Releer desde otra instancia evita validar solo el estado en memoria del intento fallido.
    resultado = ProcesarPago(
        DjangoVentaRepository(), InventarioAdapter(), AuditoriaAdapter(), transaction.atomic()
    ).ejecutar(datos)
    assert resultado["estado"] == "PAGADA"
    assert PagoModel.objects.filter(venta_id=venta_persistida).count() == 1
    assert list(ExistenciaModel.objects.values_list("cantidad", flat=True)) == [19, 19]
    assert MovimientoModel.objects.filter(tipo="SALIDA_VENTA").count() == 2
    assert AuditoriaModel.objects.filter(accion="VENTA_PAGADA").count() == 1


def test_dos_pagos_persistidos_sin_doble_descuento(venta_persistida):
    def cobrar(monto):
        return ProcesarPago(
            DjangoVentaRepository(), InventarioAdapter(), AuditoriaAdapter(), transaction.atomic()
        ).ejecutar(ProcesarPagoDTO(venta_persistida, "EFECTIVO", monto, monto))

    assert cobrar(7) == {"estado": "PENDIENTE", "saldo": 13.0}
    assert VentaModel.objects.get(pk=venta_persistida).estado == "BORRADOR"
    assert PagoModel.objects.filter(venta_id=venta_persistida).count() == 1
    assert list(ExistenciaModel.objects.values_list("cantidad", flat=True)) == [20, 20]
    assert not MovimientoModel.objects.exists()
    assert not AuditoriaModel.objects.exists()
    assert cobrar(13)["estado"] == "PAGADA"
    assert PagoModel.objects.filter(venta_id=venta_persistida).count() == 2
    assert list(ExistenciaModel.objects.values_list("cantidad", flat=True)) == [19, 19]
    assert MovimientoModel.objects.count() == 2
    assert AuditoriaModel.objects.filter(accion="VENTA_PAGADA").count() == 1
    antes_repeticion = snapshot()
    with pytest.raises(VentaNoModificable):
        cobrar(1)
    assert snapshot() == antes_repeticion


@pytest.mark.parametrize("tipo_uow", ["atomic", "mysql_uow"])
def test_rollback_de_pago_parcial_y_reintento(venta_persistida, tipo_uow):
    antes = snapshot()
    repo = DjangoVentaRepository()
    guardar_original = repo.guardar

    def guardar_y_fallar(agregado):
        guardar_original(agregado)
        assert PagoModel.objects.filter(venta_id=venta_persistida).count() == 1
        raise RuntimeError("Fallo despues de persistir pago parcial")

    uow = transaction.atomic() if tipo_uow == "atomic" else MySQLUnitOfWork()
    with patch.object(repo, "guardar", side_effect=guardar_y_fallar), pytest.raises(RuntimeError, match="pago parcial"):
        ProcesarPago(repo, InventarioAdapter(), AuditoriaAdapter(), uow).ejecutar(
            ProcesarPagoDTO(venta_persistida, "EFECTIVO", 7, 7)
        )
    assert not connection.in_atomic_block
    assert snapshot() == antes
    resultado = ProcesarPago(
        DjangoVentaRepository(), InventarioAdapter(), AuditoriaAdapter(), transaction.atomic()
    ).ejecutar(ProcesarPagoDTO(venta_persistida, "EFECTIVO", 7, 7))
    assert resultado == {"estado": "PENDIENTE", "saldo": 13.0}
    assert PagoModel.objects.filter(venta_id=venta_persistida).count() == 1
    assert list(ExistenciaModel.objects.values_list("cantidad", flat=True)) == [20, 20]
    assert not MovimientoModel.objects.exists()
    assert not AuditoriaModel.objects.exists()
```

**Medición:** 38 casos aprobados (17 de base, 12 de excepciones/coordinación y 9 de persistencia); archivo objetivo con 40 sentencias ejecutadas de 40 y 10 destinos de rama cubiertos de 10, sin ramas parciales. El archivo incluye también `__init__`; el 100% implica cobertura completa del método seleccionado. Los ayudantes de prueba y módulos colaboradores no forman parte del denominador de este reporte.

La ampliación comprueba: ventas PAGADA/ANULADA; fallos en búsqueda, promociones, segundo descuento de inventario, cierre, guardado y auditoría; excepción recibida por `__exit__`; secuencia exacta de llamadas; dos pagos sucesivos y rechazo de un tercer cobro; venta real sin productos; fallo al guardar pago parcial. Las pruebas con BD escriben realmente y provocan fallos después de escribir; comparan snapshots completos de ventas, detalles, pagos, existencias, lotes, kardex y auditoría. Verifican rollback tanto con `transaction.atomic()` como con `MySQLUnitOfWork`, y después reintentan usando repositorios nuevos.

La BD de estas pruebas es exclusiva y desechable. También se ejecuta la ampliación de persistencia contra MySQL 8.4.3/InnoDB con el wrapper existente:

```powershell
rtk proxy .venv/Scripts/python.exe scripts/qa_inventory_mysql_native.py --basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --target tests/integration/test_semana11_rollback_cobro.py --report-prefix semana11-rollback-mysql
```

El parámetro `--basedir` depende de dónde esté instalado MySQL en cada equipo. Evidencia: `reports/semana11-rollback-mysql.xml` y `.json`. Los fallos ensayados no requieren cambios en el código productivo; el rollback se garantiza al inyectar un UoW transaccional real, como hace la vista de cobro. `NullUnitOfWork` sigue sin proporcionar rollback de persistencia.

**Distinción crítica:** coverage.py mide transiciones entre líneas, por lo que no cuenta separadamente todos los operandos booleanos de una misma línea. Sus 10 ramas no son los 10 caminos McCabe. La matriz B04/B05 y B07/B08/B09 ejercita por separado los resultados alcanzables de los cortocircuitos. No se reclama MC/DC ni cobertura de todas las combinaciones lógicas.

# 5. ANÁLISIS ESTÁTICO Y ASISTENCIA DE IA (DETECCIÓN DE RUTAS MUERTAS)

## 5.1 Hallazgos del Agente IA

Se realizó inspección real de código y análisis AST; Ruff no reporta incidencias en los archivos añadidos. Un resultado limpio de Ruff no demuestra ausencia de defectos de negocio o vulnerabilidades.

| Hallazgo | Evaluación y límite |
|---|---|
| Rutas defensivas | Bucle vacío y cantidad <=0 no son caminos de venta válida con el agregado construido normalmente. Son alcanzables al aislar colaboradores o mutar objetos; no eliminar guardas por considerarlas globalmente muertas. |
| Variables inicializadas | agregado, total_anterior, pago y referencia están definidos antes de sus usos alcanzables. linea solo se usa dentro del bucle. No se detectó uso local sin inicializar. |
| Restar floats antes de Monto | `datos.monto_entregado - datos.monto` puede introducir error binario antes del redondeo monetario. Las regresiones ensayadas pasan; no prueban todos los importes. Migrar DTO a Decimal sería un cambio de contrato que requiere revisión aparte. |
| uow opcional | NullUnitOfWork no proporciona rollback real. La base aislada verifica coordinación; la ampliación de integración verifica rollback durable y reintento con UoW real. |
| Agregado de pruebas | Mock(spec=VentaAggregate) restringe nombres de métodos, pero no ejecuta sus invariantes. No confundir el 100% local con cobertura integral de ventas. |
| Identidad/autorización | El método acepta venta_id; no comprueba aquí pertenencia al cajero. Es una responsabilidad a rastrear en presentación/repositorio. No se declara vulnerabilidad confirmada sin revisar esa cadena. |
| Pago parcial | Retorna antes de descontar, cerrar o auditar VENTA_PAGADA. Es una decisión de negocio; no es código redundante. |
| Orden de efectos | La ampliación registra y compara la secuencia exacta: entrar, buscar, verificar, promociones, pago, stock por producto, cerrar, guardar, auditar, salir. Las pruebas de BD complementan ese orden con snapshots persistidos. |

## 5.2 Propuesta de Refactorización de la IA

Propuesta deliberadamente insegura y ejecutable, aislada en el archivo de pruebas como `vuelto_propuesto_ia`; **no aplicada a producción**:

```python
def vuelto_propuesto_ia(pago_datos, moneda):
    return (
        Monto(pago_datos.monto_entregado - pago_datos.monto, moneda)
        if pago_datos.monto_entregado and pago_datos.metodo == "EFECTIVO" else None
    )
```

Sustituir el chequeo explícito de None por truthiness parece simplificar, pero cambia el significado de una entrega 0.0. Otra propuesta rechazada es sustituir el redondeo de Monto por `round(float, 2)`. No se presenta una reescritura completa como equivalente sin comprobar todas las invariantes.

# 6. PUNTO DE CONTROL OBLIGATORIO: AUDITORÍA DE REFACTORIZACIONES AUTÓNOMAS POR IA

## 6.1 Riesgos Detectados en la Propuesta de la IA

| Propuesta | Contraejemplo / riesgo | Dictamen técnico |
|---|---|---|
| `if monto_entregado` | 0.0 pasa de entrega explícita insuficiente a ausencia de vuelto | Rechazada por A01 |
| `round(float,2)` | 1.005 produce 1.00 frente al 1.01 de Monto(Decimal(...)) | Rechazada por A02 |
| Descontar stock antes del retorno parcial | Consume existencias sin completar el pago | No incorporar; B02–B05 exigen cero llamadas a inventario |
| Eliminar guardas de stock | Cambia el comportamiento con líneas sin stock o estados defensivos | No incorporar; B08/B09 fijan ese comportamiento |
| Cambiar DTO a Decimal automáticamente | Cambia contratos de entrada y serialización | Requiere análisis separado y revisión humana |

## 6.2 Validación Humana Estricta (Beck, 2022)

**Estado: PENDIENTE DE REVISIÓN HUMANA.** La IA no puede acreditar que el estudiante o docente haya revisado y aprobado estos resultados. No se modificó el método productivo durante esta auditoría; se añadieron pruebas, evidencia y este informe. No hay una refactorización de producción aceptada ni correcciones manuales humanas que puedan atribuirse como realizadas.

El responsable debe ejecutar los comandos, revisar las aserciones de vuelto/saldo/stock, confirmar la separación entre casos sintéticos y ventas válidas, revisar el diff de los archivos añadidos y registrar nombre, fecha y decisión. Aceptar las pruebas requiere revisar sus oráculos; aceptar una refactorización futura exige conservar firma, valores monetarios, excepciones y efectos transaccionales.

La referencia «Beck, 2022» del enunciado no incluye título ni edición. No se le atribuye una regla específica de auditoría de IA ni una cita textual sin la referencia bibliográfica completa. Este apartado satisface el control técnico y deja explícita la aprobación pendiente; no certifica que el punto humano esté superado.

# 7. RESUMEN DE ENTREGABLES Y REFLEXIÓN A.I.R.E. (SEMANA 11)

## 7.1 Verificación de Evidencias

| Entregable | Evidencia | Estado |
|---|---|---|
| McCabe y base independiente | `scripts/qa_semana11_caja_blanca.py`, `reports/semana11-estructura.json` | V=10; rango=10; SHA256 del archivo fuente |
| Matriz de caja blanca | Sección 3 de este informe | B01–B10, regresiones y contraejemplos |
| Código xUnit | Los tres archivos de pruebas de la sección 4 | 38 casos aprobados |
| Cobertura | `reports/semana11-cobertura.json`, `reports/semana11-html/index.html` | 40/40 sentencias, 10/10 ramas del archivo |
| Resultados ejecutables | `reports/semana11-pruebas.xml` | Sin fallos |
| Rollback MySQL/InnoDB | `reports/semana11-rollback-mysql.xml` y `.json` | 9/9 aprobados; fallos después de escritura, rollback y reintentos |
| Regresión completa | `reports/semana11-regresion-completa.xml` | 1743 aprobadas, 12 omitidas, 0 fallos |
| Auditoría IA | Secciones 5 y 6; pruebas A01/A02 | Propuestas inseguras rechazadas técnicamente |
| Aprobación humana | Responsable, fecha y decisión por completar | Pendiente |

La cobertura corresponde a esta ejecución y al fuente cuyo SHA256 registra el script; no es una garantía sobre cambios posteriores. La ampliación incluye ejecución de la regresión completa y pruebas con bases desechables; no altera los datos de la web que ya estaba levantada. Las omisiones por infraestructura de otras suites se reportan por separado y no equivalen a pruebas aprobadas.

Las 12 omisiones de la ejecución general corresponden a 8 casos de otras suites que exigen MySQL/InnoDB, 1 de Redis/Celery y 3 de k6. Los 9 casos de rollback de Semana 11 se verificaron aparte con MySQL/InnoDB; no deben confundirse con esas 12 omisiones ni sumarse como pruebas únicas nuevas a la ejecución general, que ya incluye sus variantes con SQLite.

## 7.2 Reflexión A.I.R.E. personalizada al proyecto ABP

**A — Aprendizaje.** El grafo del cobro permite distinguir el retorno por pago parcial del cierre definitivo. McCabe cuantifica una base de recorridos y no sustituye la validación de todos los importes.

**I — Interacción.** La propuesta de IA se contrasta con datos concretos: entrega 0.0 y redondeo de 1.005. Un test verde con mocks tampoco acredita invariantes del agregado o una revisión humana.

**R — Retorno.** Las pruebas detectan cambios que podrían descontar stock antes de completar una venta, omitir el vuelto o alterar centavos. La separación de guardas defensivas evita presentar rutas sintéticas como compras reales.

**E — Entorno.** Una tienda local necesita coherencia entre caja, existencias y comprobantes. Evidencia reproducible y revisión humana ayudan a reducir discrepancias operativas y facilitan explicar el sistema al docente y al equipo.
