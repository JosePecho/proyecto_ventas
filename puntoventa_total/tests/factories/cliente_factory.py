import factory
import uuid

from src.modules.customers.domain.entities.cliente import Cliente


class ClienteFactory(factory.Factory):
    class Meta:
        model = Cliente

    nombre = factory.Sequence(lambda n: f"Cliente {n}")
    email = factory.LazyAttribute(lambda o: f"{o.nombre.lower().replace(' ', '.')}@test.com")
    telefono = "999888777"
    puntos_fidelidad = 0

