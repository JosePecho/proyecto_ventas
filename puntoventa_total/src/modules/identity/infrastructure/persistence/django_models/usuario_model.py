"""Modelo ORM de Usuario (esquema `identity`)."""
from django.db import models


class UsuarioModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False)
    username = models.CharField(max_length=30, unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)
    nombre_completo = models.CharField(max_length=120)
    email = models.EmailField(blank=True, default="")
    rol = models.CharField(max_length=20, choices=[])
    estado = models.CharField(max_length=20, choices=[])
    intentos_fallidos = models.PositiveSmallIntegerField(default=0)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "identity_usuario"
        ordering = ["username"]

    def __str__(self) -> str:
        return f"{self.username} ({self.rol})"

