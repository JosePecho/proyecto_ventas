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
