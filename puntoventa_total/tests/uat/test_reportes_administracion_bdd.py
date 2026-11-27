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
