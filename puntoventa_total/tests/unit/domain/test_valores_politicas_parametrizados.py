"""Oraculos explicitos de limites monetarios, fechas y politicas de negocio."""
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from src.modules.cash_register.domain.services.calculadora_arqueo import CalculadoraArqueo
from src.modules.catalog.domain.value_objects.precio import Precio
from src.modules.customers.domain.services.frecuencia_compra import FrecuenciaCompra
from src.modules.identity.domain.enums.rol_usuario import RolUsuario
from src.modules.identity.domain.services.politica_permisos import PoliticaPermisos
from src.modules.inventory.domain.services.politica_stock import PoliticaStock
from src.modules.promotions.domain.services.politica_promociones import PoliticaPromociones
from src.modules.promotions.domain.value_objects.descuento import Descuento
from src.modules.reporting.domain.value_objects.rango_fechas import RangoFechas
from src.modules.sales.domain.value_objects.metodo_pago import MetodoPago
from src.shared.domain.exceptions.validation_exception import ValidationException
from src.shared.domain.value_objects.codigo_barras import CodigoBarras
from src.shared.domain.value_objects.dni import DNI
from src.shared.domain.value_objects.monto import Monto

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("entrada,esperado", [(0, "0.00"), (1, "1.00"), ("1.004", "1.00"), ("1.005", "1.01"), ("999.995", "1000.00")])
@pytest.mark.parametrize("moneda", ["PEN", "USD"])
def test_monto_redondea_half_up(entrada, esperado, moneda):
    monto = Monto(entrada, moneda)
    assert monto.valor == Decimal(esperado)
    assert monto.moneda == moneda
    assert str(monto) == f"{esperado} {moneda}"


@pytest.mark.parametrize("valor,moneda", [("-0.001", "PEN"), (-1, "PEN"), (1, ""), (1, "PE"), (1, "PENX")])
def test_monto_rechaza_valores_invalidos(valor, moneda):
    with pytest.raises(ValidationException):
        Monto(valor, moneda)


@pytest.mark.parametrize("operacion", ["__add__", "__sub__"])
@pytest.mark.parametrize("otro", [Monto(1, "USD"), 1, "1", None])
def test_monto_no_opera_con_moneda_o_tipo_incorrecto(operacion, otro):
    monto = Monto(10)
    with pytest.raises(ValidationException):
        getattr(monto, operacion)(otro)
    assert monto == Monto(10)


@pytest.mark.parametrize("pct,esperado", [(0, "0"), (1, "0.10"), (50, "5"), (100, "10"), (-1, None), (101, None)])
def test_porcentaje_monto(pct, esperado):
    if esperado is None:
        with pytest.raises(ValidationException):
            Monto(10).porcentaje(Decimal(pct))
    else:
        assert Monto(10).porcentaje(Decimal(pct)) == Monto(esperado)


@pytest.mark.parametrize("entrada,esperado", [("12345678", "12345678"), (" 00123456 ", "00123456"), (12345678, "12345678")])
def test_dni_normaliza_y_enmascara(entrada, esperado):
    dni = DNI(entrada)
    assert str(dni) == esperado
    assert dni.enmascarado() == esperado[:3] + "****" + esperado[-1]


@pytest.mark.parametrize("entrada", ["", "1234567", "123456789", "1234a678", "１２３４５６７８", "1234 678"])
def test_dni_invalido(entrada):
    with pytest.raises(ValidationException):
        DNI(entrada)


@pytest.mark.parametrize("longitud,valido", [(7, False), (8, True), (9, False), (11, False), (12, True), (13, True), (14, True), (15, False)])
def test_longitudes_codigo_barras(longitud, valido):
    entrada = "1" * longitud
    if valido:
        assert str(CodigoBarras(entrada)) == entrada
    else:
        with pytest.raises(ValidationException):
            CodigoBarras(entrada)


@pytest.mark.parametrize("codigo,valido", [("4006381333931", True), ("4006381333932", False), ("12345678", False), ("0000000000000", True)])
def test_checksum_ean13(codigo, valido):
    assert CodigoBarras(codigo).checksum_ean13_valido() is valido


@pytest.mark.parametrize("costo,venta,margen", [(0, 10, "100"), (10, 11, "10"), (10, 15, "50"), (10, 10.99, None), (10, 0, None)])
def test_precio_margen_minimo(costo, venta, margen):
    if margen is None:
        with pytest.raises(ValidationException):
            Precio(Monto(costo), Monto(venta))
    else:
        precio = Precio(Monto(costo), Monto(venta))
        assert precio.margen_pct() == Decimal(margen)
        assert precio.ganancia_unitaria() == Monto(Decimal(str(venta)) - Decimal(str(costo)))


@pytest.mark.parametrize("tipo,valor,tope,esperado", [
    ("PORCENTAJE", 10, None, 10), ("PORCENTAJE", 100, None, 100),
    ("PORCENTAJE", 50, 5, 5), ("MONTO_FIJO", 5, None, 5), ("MONTO_FIJO", 150, None, 100),
])
@pytest.mark.parametrize("moneda", ["PEN", "USD"])
def test_descuento_aplica_tope_y_conserva_moneda(tipo, valor, tope, esperado, moneda):
    descuento = Descuento(Decimal(valor), tipo, Decimal(tope) if tope is not None else None)
    assert descuento.aplicar_a(Monto(100, moneda)) == Monto(esperado, moneda)


@pytest.mark.parametrize("tipo", ["EFECTIVO", "TARJETA", "YAPE", "PLIN", "TRANSFERENCIA"])
@pytest.mark.parametrize("monto", ["0.01", "10", "9999.99"])
def test_metodos_pago(tipo, monto):
    metodo = MetodoPago(tipo, Monto(monto), "ref-1")
    assert metodo.es_efectivo is (tipo == "EFECTIVO")
    assert metodo.monto == Monto(monto)
    assert metodo.referencia == "ref-1"


@pytest.mark.parametrize("tipo,monto", [("OTRO", 1), ("efectivo", 1), ("", 1), ("EFECTIVO", 0)])
def test_metodo_pago_invalido(tipo, monto):
    with pytest.raises(ValidationException):
        MetodoPago(tipo, Monto(monto))


@pytest.mark.parametrize("dias,valido", [(-1, False), (0, True), (1, True), (365, True), (366, True), (367, False)])
def test_rango_fechas_fronteras(dias, valido):
    inicio = date(2026, 1, 1)
    fin = inicio + timedelta(days=dias)
    if valido:
        fechas = RangoFechas(inicio, fin).en_dias()
        assert len(fechas) == dias + 1
        assert fechas[0] == inicio
        assert fechas[-1] == fin
    else:
        with pytest.raises(ValidationException):
            RangoFechas(inicio, fin)


@pytest.mark.parametrize("anio,mes,ultimo", [(2024, 2, 29), (2025, 2, 28), (2026, 4, 30), (2026, 12, 31)])
def test_mes_calendario(anio, mes, ultimo):
    rango = RangoFechas.del_mes(date(anio, mes, 15))
    assert rango.desde == date(anio, mes, 1)
    assert rango.hasta == date(anio, mes, ultimo)


@pytest.mark.parametrize("dias,clasificacion", [(0, "SIN_DATOS"), (0.01, "FRECUENTE"), (7, "FRECUENTE"), (7.01, "OCASIONAL"), (30, "OCASIONAL"), (31, "OCASIONAL")])
def test_frecuencia_clasificacion(dias, clasificacion):
    assert FrecuenciaCompra.clasificar(dias) == clasificacion


@pytest.mark.parametrize("offsets,promedio,ultimo", [([], 0, 0), ([0], 0, 0), ([0, 7], 7, 7), ([14, 0, 7], 7, 7), ([0, 0], 0.01, 0)])
def test_frecuencia_ordena_compras(offsets, promedio, ultimo):
    inicio = datetime(2026, 1, 1, tzinfo=UTC)
    fechas = [inicio + timedelta(days=d) for d in offsets]
    assert FrecuenciaCompra.dias_entre_compras(fechas) == promedio
    assert FrecuenciaCompra.ultimo_intervalo(fechas) == ultimo


@pytest.mark.parametrize("rol,permitidos", [
    (RolUsuario.ADMINISTRADOR, (True, True, True, True)),
    (RolUsuario.GERENTE, (True, True, True, False)),
    (RolUsuario.CAJERO, (True, False, False, False)),
    (RolUsuario.ALMACENERO, (False, True, False, False)),
    (RolUsuario.CLIENTE, (False, False, False, False)),
])
def test_permisos_por_rol(rol, permitidos):
    permisos = ["ventas.cobrar", "inventario.ajustar", "reportes.ver", "usuarios.gestionar"]
    assert tuple(PoliticaPermisos.puede(rol, p) for p in permisos) == permitidos
    copia = PoliticaPermisos.permisos_de(rol)
    copia.add("permiso.inventado")
    assert not PoliticaPermisos.puede(rol, "permiso.inventado")


@pytest.mark.parametrize("stock,merma,permitida", [(0, 1, False), (10, 0, False), (10, -1, False), (10, 1, True), (10, 10, True), (10, 11, False)])
def test_merma_acotada(stock, merma, permitida):
    assert PoliticaStock.puede_registrar_merma(stock, merma) is permitida


@pytest.mark.parametrize("diferencia,congruente", [("0", True), ("0.04", True), ("0.05", True), ("0.06", False)])
def test_arqueo_tolerancia(diferencia, congruente):
    assert CalculadoraArqueo.es_congruente(Monto(diferencia)) is congruente


@pytest.mark.parametrize("acumular,esperado", [(False, 80), (True, 70)])
def test_promociones_acumulacion_configurable(acumular, esperado, monkeypatch):
    monkeypatch.setattr(PoliticaPromociones, "PERMITE_ACUMULAR", acumular)
    assert PoliticaPromociones.combinar(Monto(100), [Monto(10), Monto(20)]) == Monto(esperado)
