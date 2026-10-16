import uuid

from src.modules.customers.domain.entities.cliente import Cliente
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.shared.domain.value_objects.dni import DNI


class ClienteMapper:
    @staticmethod
    def a_dominio(m: ClienteModel) -> Cliente:
        return Cliente(
            id=m.id,
            nombre=m.nombre,
            dni=DNI(m.dni) if m.dni else None,
            email=m.email,
            telefono=m.telefono,
            direccion=m.direccion,
            usuario_id=str(m.usuario_id) if m.usuario_id else None,
            puntos_fidelidad=m.puntos_fidelidad,
            activo=m.activo,
            fecha_creacion=m.fecha_creacion,
            fecha_actualizacion=m.fecha_actualizacion,
        )

    @staticmethod
    def a_modelo(e: Cliente, m: ClienteModel | None = None) -> ClienteModel:
        m = m or ClienteModel(id=e.id)
        m.id = e.id if isinstance(e.id, uuid.UUID) else uuid.UUID(str(e.id))
        m.nombre = e.nombre
        m.dni = str(e.dni) if e.dni else None
        m.email = e.email
        m.telefono = e.telefono
        m.direccion = e.direccion
        m.usuario_id = uuid.UUID(str(e.usuario_id)) if e.usuario_id else None
        m.puntos_fidelidad = e.puntos_fidelidad
        m.activo = e.activo
        return m

