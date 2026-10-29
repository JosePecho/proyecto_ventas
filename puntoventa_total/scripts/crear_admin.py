"""Crea (o desbloquea) un usuario administrador.

Uso: python scripts/crear_admin.py [--username admin] [--password Secreta123]
"""
import argparse
from getpass import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django  # noqa: E402

django.setup()

from src.modules.identity.application.dto.usuario_input import ActualizarUsuarioDTO, UsuarioInputDTO  # noqa: E402
from src.modules.identity.application.use_cases.actualizar_usuario import ActualizarUsuario  # noqa: E402
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario  # noqa: E402
from src.modules.identity.domain.enums.rol_usuario import RolUsuario  # noqa: E402
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", help="Si se omite, se solicita sin mostrarla en pantalla")
    parser.add_argument("--nombre", default="Administrador")
    args = parser.parse_args()
    if not args.password:
        args.password = getpass("Contrasena del administrador: ")
        if args.password != getpass("Confirmar contrasena: "):
            parser.error("Las contrasenas no coinciden")

    repo, hasher = construir_repositorio(), construir_hasher()
    existente = repo.buscar_por_username(args.username)

    if existente:
        ActualizarUsuario(repo, hasher).ejecutar(
            ActualizarUsuarioDTO(usuario_id=str(existente.id), password_nueva=args.password)
        )
        print(f"[ok] password reiniciado para '{args.username}'")
    else:
        dto = CrearUsuario(repo, hasher).ejecutar(
            UsuarioInputDTO(
                username=args.username,
                password=args.password,
                nombre_completo=args.nombre,
                rol=RolUsuario.ADMINISTRADOR.value,
            )
        )
        print(f"[ok] administrador creado: {dto.username} ({dto.id})")


if __name__ == "__main__":
    main()

