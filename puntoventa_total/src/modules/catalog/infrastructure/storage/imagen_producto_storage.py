"""Validacion y nombrado de imagenes de producto."""
from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.core.files.storage import default_storage

TAMANO_MAXIMO_MB = 5
FORMATOS_ACEPTADOS = ("image/jpeg", "image/png", "image/webp")


class ImagenProductoStorage:
    @staticmethod
    def validar(archivo) -> None:
        if archivo.content_type not in FORMATOS_ACEPTADOS:
            raise ValidationError("Formato de imagen no soportado (use JPEG, PNG o WebP)")
        if archivo.size > TAMANO_MAXIMO_MB * 1024 * 1024:
            raise ValidationError(f"La imagen supera {TAMANO_MAXIMO_MB}MB")
        ancho, alto = get_image_dimensions(archivo)
        if ancho and ancho < 200:
            raise ValidationError("La imagen debe tener al menos 200px de ancho")

    @staticmethod
    def guardar(archivo, nombre_base: str) -> str:
        extension = archivo.name.rsplit(".", 1)[-1].lower()
        nombre = f"{nombre_base}-{uuid.uuid4().hex[:8]}.{extension}"
        return default_storage.save(f"products/{nombre}", archivo)

    @staticmethod
    def eliminar(ruta: str) -> None:
        if ruta and default_storage.exists(ruta):
            default_storage.delete(ruta)

