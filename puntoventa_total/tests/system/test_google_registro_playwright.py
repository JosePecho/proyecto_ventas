"""Navegador y Django reales; solo la frontera Firebase/OAuth está controlada."""
import time
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from django.contrib.auth.hashers import make_password
from playwright.sync_api import expect, sync_playwright

from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.identity.application.dto.google_identity import GoogleIdentity
from src.modules.identity.infrastructure.persistence.django_models.google_vinculo_model import (
    GoogleVinculoModel,
)
from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel

pytestmark = [pytest.mark.system, pytest.mark.django_db(transaction=True)]
RAIZ = Path(__file__).resolve().parents[2]
ADAPTADOR = "src.modules.identity.infrastructure.security.firebase_google_adapter.FirebaseGoogleAdapter"


@pytest.mark.parametrize("existente", [False, True])
def test_registro_y_vinculacion_con_backend_real(live_server, settings, existente):
    settings.FIREBASE_GOOGLE_ENABLED = True
    identidad = GoogleIdentity(uid="uid-google-browser", email="browser@gmail.com", nombre="Cliente QA",
                               proyecto="puntoventa-a7f93", auth_time=int(time.time()))
    password = "Segura!Browser#725"
    if existente:
        UsuarioModel.objects.create(id=uuid4(), username="browser.admin", email=identidad.email,
            nombre_completo="Usuario QA", password_hash=make_password(password), rol="ADMINISTRADOR", estado="ACTIVO")
    sdk_auth = """
        export const inMemoryPersistence = {};
        export function getAuth() { return {}; }
        export async function setPersistence() {}
        export class GoogleAuthProvider { setCustomParameters() {} }
        export async function signInWithPopup() { return {user: {getIdToken: async () => 'token-qa'}}; }
        export async function signOut() {}
    """
    with patch(ADAPTADOR + ".verificar", return_value=identidad), patch(ADAPTADOR + ".revalidar"), sync_playwright() as motor:
        browser = motor.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1000})

        def firebase(route):
            route.fulfill(content_type="application/javascript", headers={"Access-Control-Allow-Origin": "*"},
                body="export function initializeApp(config) { return config; }" if "firebase-app.js" in route.request.url else sdk_auth)

        def static(route):
            path = RAIZ / urlsplit(route.request.url).path.lstrip("/")
            route.fulfill(path=str(path)) if path.is_file() else route.fulfill(body="")

        page.route("https://www.gstatic.com/**", firebase)
        page.route("**/static/**", static)
        page.goto(live_server.url + "/login/")
        page.get_by_role("button", name="Continuar con Google").click()
        if existente:
            page.wait_for_url(live_server.url + "/login/google/vincular/")
            expect(page.get_by_role("heading", name="Vincula tu cuenta")).to_be_visible()
            page.get_by_label("Usuario o email").fill("browser.admin")
            page.locator("input[name=password]").fill(password)
            page.get_by_role("checkbox").check()
            page.get_by_role("button", name="Vincular y continuar").click()
        else:
            page.wait_for_url(live_server.url + "/login/google/completar/")
            expect(page.get_by_role("heading", name="Completa tus datos")).to_be_visible()
            expect(page.locator("input[name=email]")).to_be_disabled()
            page.locator("input[name=dni]").fill("87654321")
            page.locator("input[name=telefono]").fill("987654321")
            (RAIZ / "reports").mkdir(exist_ok=True)
            page.screenshot(path=str(RAIZ / "reports/google-completar-datos.png"), full_page=True, animations="disabled")
            page.get_by_role("button", name="Guardar y continuar").click()
        page.wait_for_url(live_server.url + "/catalogo/")
        browser.close()
    assert GoogleVinculoModel.objects.count() == UsuarioModel.objects.count() == 1
    assert UsuarioModel.objects.get().rol == ("ADMINISTRADOR" if existente else "CLIENTE")
    assert ClienteModel.objects.count() == (0 if existente else 1)
