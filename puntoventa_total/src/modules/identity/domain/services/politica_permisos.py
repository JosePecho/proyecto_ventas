"""Politica central de permisos por rol (fuente de verdad unica)."""
from __future__ import annotations

from src.modules.identity.domain.enums.rol_usuario import RolUsuario

PERMISOS_VENTAS = {"ventas.cobrar", "ventas.anular", "ventas.consultar"}
PERMISOS_CAJA = {"caja.abrir", "caja.cerrar", "caja.arqueo"}
PERMISOS_INVENTARIO = {"inventario.recibir", "inventario.ajustar", "inventario.merma"}
PERMISOS_CATALOGO = {"catalogo.gestionar", "catalogo.consultar"}
PERMISOS_REPORTES = {"reportes.ver", "reportes.exportar"}
PERMISOS_ADMIN = {"usuarios.gestionar", "auditoria.ver", "config.gestionar"}


class PoliticaPermisos:
    MATRIZ: dict[RolUsuario, set[str]] = {
        RolUsuario.ADMINISTRADOR: set().union(
            PERMISOS_VENTAS, PERMISOS_CAJA, PERMISOS_INVENTARIO,
            PERMISOS_CATALOGO, PERMISOS_REPORTES, PERMISOS_ADMIN,
        ),
        RolUsuario.GERENTE: set().union(
            PERMISOS_VENTAS, PERMISOS_CAJA, PERMISOS_INVENTARIO,
            PERMISOS_CATALOGO, PERMISOS_REPORTES,
        ),
        RolUsuario.CAJERO: set().union(PERMISOS_VENTAS, PERMISOS_CAJA, PERMISOS_CATALOGO),
        RolUsuario.ALMACENERO: set().union(PERMISOS_INVENTARIO, PERMISOS_CATALOGO),
        RolUsuario.CLIENTE: {"pedidos.realizar", "pedidos.consultar"},
    }

    @classmethod
    def permisos_de(cls, rol: RolUsuario) -> set[str]:
        return set(cls.MATRIZ.get(rol, set()))

    @classmethod
    def puede(cls, rol: RolUsuario, permiso: str) -> bool:
        return permiso in cls.permisos_de(rol)

    @classmethod
    def puede_todos(cls, rol: RolUsuario, permisos: list[str]) -> bool:
        return all(cls.puede(rol, p) for p in permisos)

    @classmethod
    def puede_alguno(cls, rol: RolUsuario, permisos: list[str]) -> bool:
        return any(cls.puede(rol, p) for p in permisos)

