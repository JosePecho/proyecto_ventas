"""Comprueba configuración remota sin mostrar credenciales ni tokens."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django  # noqa: E402

django.setup()

import requests  # noqa: E402
from django.conf import settings  # noqa: E402
from google.auth.transport.requests import Request  # noqa: E402

from src.modules.identity.infrastructure.security.firebase_google_adapter import (  # noqa: E402
    obtener_firebase_app,  # noqa: E402
)


def main():
    try:
        app = obtener_firebase_app()
        credencial = app.credential.get_credential()
        print("Credencial Admin válida y proyecto coincidente.")
        credencial.refresh(Request())
        print("Autenticación de cuenta de servicio correcta.")
        respuesta = requests.get(
            f"https://identitytoolkit.googleapis.com/admin/v2/projects/{settings.FIREBASE_PROJECT_ID}/config",
            headers={"Authorization": f"Bearer {credencial.token}"}, timeout=15,
        )
        if respuesta.status_code != 200:
            print(f"Consulta de dominios no disponible: HTTP {respuesta.status_code}. Revisar Firebase Console.")
            return 1
        dominios = respuesta.json().get("authorizedDomains", [])
        for dominio in ("localhost", "127.0.0.1"):
            print(f"{dominio}: {'autorizado' if dominio in dominios else 'FALTA AUTORIZAR'}")
        for modulo in ("app", "auth"):
            respuesta = requests.get(f"https://www.gstatic.com/firebasejs/13.2.0/firebase-{modulo}.js", timeout=15)
            print(f"SDK JavaScript {modulo} 13.2.0: HTTP {respuesta.status_code}")
        return 0
    except Exception as exc:
        # No imprimir str(exc): respuestas externas podrían incluir datos sensibles.
        print(f"Comprobación no completada ({type(exc).__name__}). No se muestran detalles privados.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
