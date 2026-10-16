from typing import Optional, Sequence

from src.modules.customers.domain.entities.cliente import Cliente
from src.modules.customers.domain.repositories.cliente_repository import ClienteRepository
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.customers.infrastructure.persistence.mappers.cliente_mapper import ClienteMapper


class DjangoClienteRepository(ClienteRepository):
    def __init__(self):
        self._mapper = ClienteMapper()

    def buscar_por_id(self, cliente_id) -> Optional[Cliente]:
        m = ClienteModel.objects.filter(pk=cliente_id).first()
        return self._mapper.a_dominio(m) if m else None

    def buscar_por_dni(self, dni: str) -> Optional[Cliente]:
        m = ClienteModel.objects.filter(dni=dni).first()
        return self._mapper.a_dominio(m) if m else None

    def buscar_por_usuario(self, usuario_id: str) -> Optional[Cliente]:
        m = ClienteModel.objects.filter(usuario_id=usuario_id).first()
        return self._mapper.a_dominio(m) if m else None

    def listar(self, termino: str | None = None) -> Sequence[Cliente]:
        qs = ClienteModel.objects.filter(activo=True)
        if termino:
            from django.db.models import Q

            qs = qs.filter(Q(nombre__icontains=termino) | Q(dni__icontains=termino))
        return [self._mapper.a_dominio(m) for m in qs]

    def guardar(self, cliente: Cliente) -> Cliente:
        m = ClienteModel.objects.filter(pk=cliente.id).first()
        self._mapper.a_modelo(cliente, m).save()
        return cliente

