"""Interfaz real y JS de producción con frontera OAuth controlada."""
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

pytestmark = [pytest.mark.system, pytest.mark.django_db]
RAIZ = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("modo", ["cancelado", "rechazado", "correcto", "sdk-caido"])
def test_boton_google_y_formulario_tradicional(client, settings, modo):
    settings.FIREBASE_GOOGLE_ENABLED = True
    html = client.get("/login/").content.decode()
    app_js = "export function initializeApp(config) { return config; }"
    auth_js = """
      export const inMemoryPersistence = {};
      export function getAuth() { return {}; }
      export function setPersistence() { return Promise.resolve(); }
      export class GoogleAuthProvider { setCustomParameters(p) { window.providerParams = p; } }
      export async function signInWithPopup() {
        if (window.modo === 'cancelado') throw {code: 'auth/popup-closed-by-user'};
        return {user: {getIdToken: async () => 'id-token-falso'}};
      }
      export async function signOut() { window.signedOut = true; }
    """
    solicitudes = []
    with sync_playwright() as motor:
        browser = motor.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.add_init_script(f"window.modo = '{modo}';")

        def local(route):
            path = route.request.url.split("login.test", 1)[1]
            if path == "/login/":
                route.fulfill(body=html, content_type="text/html")
            elif path == "/login/google/":
                solicitudes.append(route.request)
                route.fulfill(status=403 if modo == "rechazado" else 200,
                    json={"error": "Cuenta no autorizada"} if modo == "rechazado" else {"redirect": "/catalogo/"})
            elif path == "/catalogo/":
                route.fulfill(body="Acceso autorizado", content_type="text/html")
            elif path.startswith("/static/"):
                archivo = RAIZ / path.lstrip("/").split("?", 1)[0]
                route.fulfill(path=str(archivo)) if archivo.is_file() else route.fulfill(body="")
            else:
                route.fulfill(body="")

        def firebase(route):
            if modo == "sdk-caido":
                route.abort()
            else:
                route.fulfill(body=app_js if "firebase-app.js" in route.request.url else auth_js,
                    content_type="application/javascript", headers={"Access-Control-Allow-Origin": "*"})

        page.route("http://login.test/**", local)
        page.route("https://www.gstatic.com/**", firebase)
        page.goto("http://login.test/login/")
        expect(page.get_by_label("Usuario o email")).to_be_visible()
        expect(page.locator("input[name=password]")).to_be_visible()
        expect(page.get_by_role("button", name="Ingresar", exact=True)).to_be_enabled()
        boton = page.get_by_role("button", name="Continuar con Google")
        if modo == "sdk-caido":
            expect(page.locator("#google-login-error")).to_contain_text("Google no está disponible")
            expect(boton).to_be_disabled()
        else:
            expect(boton).to_be_enabled()
            assert page.evaluate("window.providerParams.prompt") == "select_account"
            if modo == "rechazado":
                carpeta = RAIZ / "reports"
                carpeta.mkdir(exist_ok=True)
                page.screenshot(path=str(carpeta / "login-google.png"), full_page=True, animations="disabled")
            boton.click()
            if modo == "correcto":
                page.wait_for_url("http://login.test/catalogo/")
            else:
                expect(page.locator("#google-login-error")).to_contain_text(
                    "Se canceló" if modo == "cancelado" else "Cuenta no autorizada")
                expect(boton).to_be_enabled()
                assert page.evaluate("window.signedOut") is True
            if modo != "cancelado":
                assert len(solicitudes) == 1
                assert solicitudes[0].headers.get("x-csrftoken")
                assert solicitudes[0].post_data_json["id_token"] == "id-token-falso"
        browser.close()
