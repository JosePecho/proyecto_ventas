"""Reemplaza una clave Django debil en .env; no revela ni guarda copias de la clave."""
from pathlib import Path
import secrets


def main():
    archivo = Path(__file__).resolve().parents[1] / ".env"
    lineas = archivo.read_text(encoding="utf-8-sig").splitlines() if archivo.exists() else []
    prefijo = "DJANGO_SECRET_KEY"
    anteriores = [linea.partition("=")[2].strip().strip("\"'") for linea in lineas
                  if linea.partition("=")[0].strip() == prefijo]
    if anteriores and len(anteriores[0]) >= 50 and len(set(anteriores[0])) >= 5 and not anteriores[0].startswith("django-insecure-"):
        print("La clave local ya cumple las comprobaciones basicas de longitud y diversidad.")
        return
    nueva = f"{prefijo}={secrets.token_urlsafe(64)}"
    resultado = [nueva if linea.partition("=")[0].strip() == prefijo else linea for linea in lineas]
    if not anteriores:
        resultado.append(nueva)
    archivo.write_text("\n".join(resultado) + "\n", encoding="utf-8")
    print("Clave Django local generada sin mostrar su valor. Reiniciar las sesiones anteriores.")


if __name__ == "__main__":
    main()
