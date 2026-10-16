"""Mapper entre entidad de dominio y modelo ORM."""
from __future__ import annotations

import uuid

from src.modules.identity.domain.entities.usuario import Usuario
from src.modules.identity.domain.enums.estado_usuario import EstadoUsuario
from src.modules.identity.domain.enums.rol_usuario import RolUsuario
from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel


class UsuarioMapper:
    @staticmethod
    def a_dominio(modelo: UsuarioModel) -> Usuario:
        return Usuario(
            id=modelo.id,
            username=modelo.username,
            password_hash=modelo.password_hash,
            nombre_completo=modelo.nombre_completo,
            email=modelo.email,
            rol=RolUsuario(modelo.rol),
            estado=EstadoUsuario(modelo.estado),
            intentos_fallidos=modelo.intentos_fallidos,
            ultimo_acceso=modelo.ultimo_acceso,
            activo=modelo.activo,
            fecha_creacion=modelo.fecha_creacion,
            fecha_actualizacion=modelo.fecha_actualizacion,
        )

    @staticmethod
    def a_modelo(entidad: Usuario, modelo: UsuarioModel | None = None) -> UsuarioModel:
        modelo = modelo or UsuarioModel(id=entidad.id)
        modelo.id = entidad.id if isinstance(entidad.id, uuid.UUID) else uuid.UUID(str(entidad.id))
        modelo.username = entidad.username
        modelo.password_hash = entidad.password_hash
        modelo.nombre_completo = entidad.nombre_completo
        modelo.email = entidad.email
        modelo.rol = entidad.rol.value
        modelo.estado = entidad.estado.value
        modelo.intentos_fallidos = entidad.intentos_fallidos
        modelo.ultimo_acceso = entidad.ultimo_acceso
        modelo.activo = entidad.activo
        return modelo

