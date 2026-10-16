from src.shared.domain.exceptions.domain_exception import DomainException


class ProductoException(DomainException):
    codigo = "PRODUCTO_INVALIDO"


class ProductoNoEncontrado(ProductoException):
    codigo = "PRODUCTO_NO_ENCONTRADO"

    def __init__(self, identificador):
        super().__init__(f"Producto no encontrado: {identificador}")


class ProductoDescontinuado(ProductoException):
    codigo = "PRODUCTO_DESCONTINUADO"

    def __init__(self, nombre: str):
        super().__init__(f"El producto '{nombre}' esta descontinuado")


class CodigoBarrasDuplicado(ProductoException):
    codigo = "CODIGO_BARRAS_DUPLICADO"

    def __init__(self, codigo: str):
        super().__init__(f"Ya existe un producto con el codigo {codigo}")


class CategoriaNoEncontrada(DomainException):
    codigo = "CATEGORIA_NO_ENCONTRADA"

    def __init__(self, identificador):
        super().__init__(f"Categoria no encontrada: {identificador}")

