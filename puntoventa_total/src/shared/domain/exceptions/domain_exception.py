"""Excepcion base de todas las violaciones de reglas de negocio."""


class DomainException(Exception):
    """Error imputable al usuario/rol que ejecuta la operacion (no es bug)."""

    codigo = "DOMINIO_INVALIDO"

    def __init__(self, mensaje: str, codigo: str | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        if codigo:
            self.codigo = codigo

    def __str__(self) -> str:
        return self.mensaje

