"""Repositorio de Usuario sobre Django ORM."""
from __future__ import annotations

from typing import Optional, Sequence

from django.db import IntegrityError

from src.modules.identity.domain.entities.usuario import Usuario
from src.modules.identity.domain.exceptions.usuario_exceptions import UsernameDuplicado
from src.modules.identity.domain.repositories.usuario_repository import UsuarioRepository
from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel
from src.modules.identity.infrastructure.persistence.mappers.usuario_mapper import UsuarioMapper


class DjangoUsuarioRepository(UsuarioRepository):
    def __init__(self):
        self._mapper = UsuarioMapper()

    def buscar_por_id(self, usuario_id) -> Optional[Usuario]:
        try:
            modelo = UsuarioModel.objects.select_related().get(pk=usuario_id)
        except UsuarioModel.DoesNotExist:
            return None
        return self._mapper.a_dominio(modelo)

    def buscar_por_username(self, username: str) -> Optional[Usuario]:
        modelo = UsuarioModel.objects.filter(username__iexact=username).first()
        return self._mapper.a_dominio(modelo) if modelo else None

    def buscar_por_email(self, email: str) -> Optional[Usuario]:
        modelo = UsuarioModel.objects.filter(email__iexact=email).first()
        return self._mapper.a_dominio(modelo) if modelo else None

    def listar(self, incluir_inactivos: bool = False) -> Sequence[Usuario]:
        qs = UsuarioModel.objects.all()
        if not incluir_inactivos:
            qs = qs.filter(activo=True)
        return [self._mapper.a_dominio(m) for m in qs.order_by("username")]

    def guardar(self, usuario: Usuario) -> Usuario:
        modelo = UsuarioModel.objects.filter(pk=usuario.id).first()
        modelo = self._mapper.a_modelo(usuario, modelo)
        try:
            modelo.save()
        except IntegrityError as exc:
            raise UsernameDuplicado(usuario.username) from exc
        return usuario

    def eliminar(self, usuario: Usuario) -> None:
        UsuarioModel.objects.filter(pk=usuario.id).delete()

