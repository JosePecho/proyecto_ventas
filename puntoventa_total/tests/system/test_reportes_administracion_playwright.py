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
