"""Auditoría de mutaciones HTTP dentro de la misma transacción de negocio."""
from contextvars import ContextVar
from uuid import uuid4
from functools import wraps

from django.contrib.auth import logout
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.shortcuts import redirect

contexto = ContextVar("audit_request", default=None)
MODULOS = {"identity", "catalog", "customers", "promotions", "orders", "sales", "inventory", "cash_register"}
AGREGADOS = {"UsuarioModel", "ProductoModel", "CategoriaModel", "ClienteModel", "PromocionModel",
             "PedidoModel", "VentaModel", "TurnoCajaModel"}


def registrar(sender, instance, created=False, **kwargs):
    datos = contexto.get()
    if datos is None or sender._meta.app_label not in MODULOS or sender.__name__ not in AGREGADOS:
        return
    from src.modules.auditing.infrastructure.persistence.django_models.auditoria_model import AuditoriaModel
    accion = "ELIMINAR" if kwargs.get("signal") is post_delete else ("CREAR" if created else "ACTUALIZAR")
    AuditoriaModel.objects.create(id=uuid4(), accion=accion, entidad=sender.__name__, entidad_id=str(instance.pk),
                                  usuario_id=datos["usuario_id"], detalle={"ruta": datos["ruta"]})


class RequestAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario_id = request.session.get("usuario_id")
        if request.user.is_authenticated and usuario_id:
            from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel
            usuario = UsuarioModel.objects.only("activo", "estado", "rol").filter(pk=usuario_id).first()
            if usuario and (not usuario.activo or usuario.estado != "ACTIVO" or (
                request.session.get("identity_role") and request.session["identity_role"] != usuario.rol
            )):
                logout(request)
                return redirect("identity:login")
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return self.get_response(request)
        token = contexto.set({"usuario_id": usuario_id, "ruta": request.path})
        try:
            with transaction.atomic():
                respuesta = self.get_response(request)
                if respuesta.status_code >= 400:
                    transaction.set_rollback(True)
                return respuesta
        finally:
            contexto.reset(token)


post_save.connect(registrar, dispatch_uid="business_save_audit", weak=False)
post_delete.connect(registrar, dispatch_uid="business_delete_audit", weak=False)


def auditar_tarea(funcion):
    @wraps(funcion)
    def ejecutar(*args, **kwargs):
        token = contexto.set({"usuario_id": None, "ruta": "celery:" + funcion.__module__})
        try:
            with transaction.atomic():
                return funcion(*args, **kwargs)
        finally:
            contexto.reset(token)
    return ejecutar
