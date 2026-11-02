"""Ventana real en Chromium usando los campos Django y el JS de produccion."""
from pathlib import Path

import pytest
from django.template.loader import render_to_string
from playwright.sync_api import expect, sync_playwright

from src.modules.customers.presentation.forms.perfil_cliente_form import PerfilClienteForm
from src.modules.customers.presentation.forms.registro_cliente_form import RegistroClienteForm
from src.modules.customers.presentation.forms.registro_web_form import RegistroWebForm
from src.modules.orders.presentation.forms.pedido_form import PedidoForm

pytestmark = pytest.mark.system
RAIZ = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def navegador_telefono():
    with sync_playwright() as motor:
        navegador = motor.chromium.launch()
        yield navegador
        navegador.close()


@pytest.fixture(params=[
    (PerfilClienteForm, "telefono"), (RegistroClienteForm, "telefono"),
    (RegistroWebForm, "telefono"), (PedidoForm, "cliente_telefono"),
], ids=["perfil", "registro-cliente", "registro-web", "pedido"])
def pagina_telefono(request, navegador_telefono):
    clase, campo = request.param
    pagina = navegador_telefono.new_page()
    pagina.set_content(
        '<form id="prueba-telefono">' + str(clase()[campo]) + '<button type="submit">Guardar</button></form>'
        + render_to_string("components/phone_warning.html")
    )
    pagina.add_script_tag(path=str(RAIZ / "static/js/phone_validation.js"))
    pagina.evaluate("""() => {
        window.envios = 0;
        document.getElementById('prueba-telefono').addEventListener('submit', e => {
            e.preventDefault(); window.envios += 1;
        });
    }""")
    try:
        yield pagina, pagina.locator("input[data-phone-peru]")
    finally:
        pagina.close()


@pytest.mark.parametrize("valor,explicacion", [
    ("98765432", "Ingresaste 8. Falta 1"),
    ("9876543210", "Ingresaste 10. Sobra 1"),
    ("987abc321", "solo debe contener números"),
    ("+51987654321", "sin espacios, guiones ni +51"),
    ("887654321", "debe comenzar con 9"),
])
def test_numero_invalido_muestra_motivo_y_bloquea_envio(pagina_telefono, valor, explicacion):
    pagina, campo = pagina_telefono
    # Simula tambien datos asignados por autocompletado/JS que exceden maxlength.
    campo.evaluate("(campo, valor) => { campo.value = valor; campo.dispatchEvent(new Event('input', {bubbles: true})); }", valor)
    pagina.get_by_role("button", name="Guardar", exact=True).click()
    expect(pagina.get_by_role("alertdialog")).to_be_visible()
    expect(pagina.locator("#phone-warning-message")).to_contain_text(explicacion)
    assert pagina.evaluate("window.envios") == 0
    pagina.get_by_role("button", name="Corregir teléfono").click()
    expect(campo).to_be_focused()
    campo.fill("987654321")
    pagina.get_by_role("button", name="Guardar", exact=True).click()
    assert pagina.evaluate("window.envios") == 1
    expect(pagina.get_by_role("alertdialog")).not_to_be_visible()


def test_decimo_digito_advierte_sin_recortar_silenciosamente(pagina_telefono):
    pagina, campo = pagina_telefono
    campo.fill("987654321")
    campo.press("End")
    campo.press_sequentially("0")
    expect(pagina.get_by_role("alertdialog")).to_be_visible()
    expect(pagina.locator("#phone-warning-message")).to_contain_text("Ingresaste 10")
    expect(campo).to_have_value("987654321")
    assert pagina.evaluate("window.envios") == 0


def test_pegar_numero_largo_advierte_y_conserva_valor_anterior(pagina_telefono):
    pagina, campo = pagina_telefono
    campo.fill("987")
    campo.evaluate("""campo => {
        campo.select();
        const portapapeles = new DataTransfer();
        portapapeles.setData('text', '9876543210');
        const evento = new ClipboardEvent('paste', {bubbles: true, cancelable: true, clipboardData: portapapeles});
        window.pegadoRechazado = !campo.dispatchEvent(evento);
    }""")
    expect(pagina.get_by_role("alertdialog")).to_be_visible()
    expect(pagina.locator("#phone-warning-message")).to_contain_text("Sobra 1")
    expect(campo).to_have_value("987")
    assert pagina.evaluate("window.pegadoRechazado")


def test_formulario_sin_validacion_nativa_tambien_bloquea(pagina_telefono):
    pagina, campo = pagina_telefono
    pagina.locator("#prueba-telefono").evaluate("form => form.noValidate = true")
    campo.fill("987")
    pagina.get_by_role("button", name="Guardar", exact=True).click()
    expect(pagina.get_by_role("alertdialog")).to_be_visible()
    assert pagina.evaluate("window.envios") == 0
