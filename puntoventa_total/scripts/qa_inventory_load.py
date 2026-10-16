"""Carga HTTP autenticada y acotada sobre las pantallas reales de inventario."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from http.cookiejar import CookieJar
import json
import math
import os
from time import perf_counter
from urllib.parse import urlencode, urlsplit
from urllib.request import build_opener, HTTPCookieProcessor, Request


class TokenCSRF(HTMLParser):
    token = None

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if tag == "input" and atributos.get("name") == "csrfmiddlewaretoken":
            self.token = atributos.get("value")


def ejecutar_carga(url, username, password, usuarios=4, peticiones=20, p95_max_ms=2000):
    base = url.rstrip("/")
    rutas = ("/inventario/", "/inventario/alertas/", "/reportes/inventario/")

    def autenticar():
        cliente = build_opener(HTTPCookieProcessor(CookieJar()))
        try:
            with cliente.open(base + "/", timeout=10) as respuesta:
                parser = TokenCSRF()
                parser.feed(respuesta.read().decode("utf-8"))
            if not parser.token:
                raise ValueError("Login sin token CSRF")
            datos = urlencode({"username": username, "password": password, "csrfmiddlewaretoken": parser.token}).encode()
            with cliente.open(Request(base + "/", data=datos, headers={"Referer": base + "/"}), timeout=10) as respuesta:
                if urlsplit(respuesta.geturl()).path != "/catalogo/":
                    raise ValueError("Login rechazado")
                respuesta.read()
        except Exception as exc:
            return None, type(exc).__name__
        return cliente, None

    # Prepara sesiones fuera de la ventana medida. El objetivo son lecturas
    # concurrentes de inventario; autenticacion masiva requiere su propia prueba.
    sesiones = [autenticar() for _ in range(usuarios)]

    def usuario(indice):
        total = peticiones // usuarios + (indice < peticiones % usuarios)
        if not total:
            return []
        cliente, error = sesiones[indice]
        if error:
            return [{"ok": False, "ms": 0, "error": error, "fase": "login"}]
        muestras = []
        for i in range(total):
            ruta = rutas[i % len(rutas)]
            inicio = perf_counter()
            try:
                with cliente.open(base + ruta, timeout=10) as respuesta:
                    cuerpo = respuesta.read()
                    ok = respuesta.status == 200 and urlsplit(respuesta.geturl()).path == ruta and b"<main" in cuerpo
                muestras.append({"ok": ok, "ms": (perf_counter() - inicio) * 1000, "ruta": ruta})
            except Exception as exc:
                muestras.append({"ok": False, "ms": (perf_counter() - inicio) * 1000,
                                 "error": type(exc).__name__, "ruta": ruta})
        return muestras

    with ThreadPoolExecutor(max_workers=usuarios) as pool:
        muestras = [m for lote in pool.map(usuario, range(usuarios)) for m in lote]
    tiempos = sorted(m["ms"] for m in muestras)
    p95 = tiempos[max(0, math.ceil(len(tiempos) * 0.95) - 1)] if tiempos else 0
    errores = sum(not m["ok"] for m in muestras)
    aprobado = len(muestras) == peticiones and errores == 0 and p95 <= p95_max_ms
    return {"aprobado": aprobado, "usuarios": usuarios, "peticiones_solicitadas": peticiones,
            "muestras": len(muestras), "errores": errores, "p95_ms": round(p95, 2), "p95_max_ms": p95_max_ms}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", required=True)
    parser.add_argument("--users", type=int, choices=range(1, 51), default=4)
    parser.add_argument("--requests", type=int, default=20)
    parser.add_argument("--p95-max-ms", type=float, default=2000)
    args = parser.parse_args()
    password = os.environ.get("INVENTORY_LOAD_PASSWORD")
    if not password:
        parser.error("Defina INVENTORY_LOAD_PASSWORD para un usuario de QA con rol ALMACENERO")
    if not 1 <= args.requests <= 10000:
        parser.error("--requests debe estar entre 1 y 10000")
    resultado = ejecutar_carga(args.url, args.username, password, args.users, args.requests, args.p95_max_ms)
    print(json.dumps(resultado, ensure_ascii=False))
    return 0 if resultado["aprobado"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
