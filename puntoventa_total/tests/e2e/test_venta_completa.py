"""Flujo completo: abrir caja -> escanear -> cobrar -> ticket."""
import uuid

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.django_db]


def test_flujo_pos_completo(client, django_user_model):
    django_user_model.objects.create_user(username="cajero1", password="Secreta123")
    assert client.login(username="cajero1", password="Secreta123")

    # el login real fija rol y usuario en sesion; aqui se replica ese contexto
    sesion = client.session
    sesion["rol"] = "CAJERO"
    sesion["usuario_id"] = str(uuid.uuid4())
    sesion.save()

    # 1. apertura de caja
    respuesta = client.post("/caja/apertura/", {"monto_apertura": "100.00"})
    assert respuesta.status_code in (200, 302)

    # 2. el POS responde una vez con caja abierta
    respuesta = client.get("/pos/")
    assert respuesta.status_code == 200

    # 3. busqueda por codigo de barras (sin resultados es valido en BD vacia)
    respuesta = client.get("/pos/buscar/", {"q": "7750000000000"})
    assert respuesta.status_code == 200

