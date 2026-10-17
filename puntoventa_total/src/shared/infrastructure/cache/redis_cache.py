"""Cliente de cache con claves namespaced y invalidacion por entorno."""
from __future__ import annotations

from functools import wraps
from hashlib import sha256
import json
from typing import Callable

from django.core.cache import cache

PREFIJO = "puntoventa"


class RedisCache:
    """Fachada sobre la cache de Django (Redis en produccion)."""

    @staticmethod
    def clave(*partes: object) -> str:
        return ":".join([PREFIJO, *[str(p) for p in partes]])

    @staticmethod
    def obtener(clave: str, por_defecto=None):
        return cache.get(RedisCache.clave(clave), por_defecto)

    @staticmethod
    def establecer(clave: str, valor, segundos: int = 300) -> None:
        cache.set(RedisCache.clave(clave), valor, segundos)

    @staticmethod
    def eliminar(clave: str) -> None:
        cache.delete(RedisCache.clave(clave))

    @staticmethod
    def eliminar_patron(prefijo: str) -> None:
        cache.delete_many(cache.keys(RedisCache.clave(prefijo) + "*"))


def cache_resultado(segundos: int = 300, prefijo: str = "query") -> Callable:
    """Decorador de memoizacion para casos de uso de solo lectura."""

    def envolver(func: Callable) -> Callable:
        @wraps(func)
        def interno(*args, **kwargs):
            # Incluye argumentos posicionales: buscar arroz no puede devolver pan.
            payload = json.dumps([args, sorted(kwargs.items())], default=str, ensure_ascii=True)
            digest = sha256(payload.encode("utf-8")).hexdigest()
            clave = f"{prefijo}:{func.__name__}:{digest}"
            resultado = RedisCache.obtener(clave)
            if resultado is None:
                resultado = func(*args, **kwargs)
                RedisCache.establecer(clave, resultado, segundos)
            return resultado

        return interno

    return envolver

