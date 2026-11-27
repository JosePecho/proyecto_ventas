"""Coordinación transaccional de los casos de uso existentes; no modifica módulos comerciales."""
import re
from hashlib import sha256

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import transaction

from src.modules.customers.application.dto.cliente_input import ClienteInputDTO
from src.modules.customers.application.use_cases.registrar_cliente import RegistrarCliente
from src.modules.customers.infrastructure.factories import construir_cliente_repository
from src.modules.customers.infrastructure.persistence.django_models.cliente_model import ClienteModel
from src.modules.identity.application.dto.usuario_input import UsuarioInputDTO
from src.modules.identity.application.dto.usuario_output import UsuarioOutputDTO
from src.modules.identity.application.use_cases.autenticar_usuario import AutenticarUsuario
from src.modules.identity.application.use_cases.crear_usuario import CrearUsuario
from src.modules.identity.domain.exceptions.usuario_exceptions import CredencialesInvalidas, UsuarioInactivo
from src.modules.identity.infrastructure.factories import construir_hasher, construir_repositorio
from src.modules.identity.infrastructure.persistence.django_models.google_vinculo_model import (
    GoogleVinculoModel,
    clave_google,
)
from src.modules.identity.infrastructure.persistence.django_models.usuario_model import UsuarioModel
from src.modules.identity.infrastructure.persistence.repositories.google_vinculo_repository import (
    GoogleVinculoRepository,
)
from src.shared.domain.value_objects.dni import DNI


def exigir_activo(usuario):
    if not usuario.puede_autenticarse():
        raise UsuarioInactivo()


def usuario_por_email(email):
    modelos = list(UsuarioModel.objects.filter(email__iexact=email)[:2])
    if len(modelos) > 1:
        raise CredencialesInvalidas()
    if not modelos:
        return None
    usuario = construir_repositorio().buscar_por_id(modelos[0].id)
    exigir_activo(usuario)
    return usuario


def perfil_cliente(usuario):
    perfiles = list(ClienteModel.objects.filter(usuario_id=usuario.id)[:2])
    if len(perfiles) > 1 or (perfiles and not perfiles[0].activo):
        raise CredencialesInvalidas()
    return perfiles[0] if perfiles else None


def necesita_perfil(usuario):
    if usuario.rol != "CLIENTE":
        return False
    perfil = perfil_cliente(usuario)
    return (perfil is None or not all((perfil.nombre, perfil.dni, perfil.telefono, perfil.email))
            or re.fullmatch(r"[0-9]{8}", perfil.dni or "") is None
            or re.fullmatch(r"9[0-9]{8}", perfil.telefono or "") is None)


def resolver_google(identidad):
    usuario = GoogleVinculoRepository().buscar_usuario(identidad)
    if usuario:
        exigir_activo(usuario)
        return ("completar" if necesita_perfil(usuario) else "entrar"), usuario
    # El correo ya reservado por otro UID nunca crea una segunda cuenta.
    if GoogleVinculoModel.objects.filter(proyecto=identidad.proyecto, email=identidad.email).exists():
        raise CredencialesInvalidas()
    usuario = usuario_por_email(identidad.email)
    if usuario and GoogleVinculoModel.objects.filter(usuario_id=usuario.id).exists():
        raise CredencialesInvalidas()
    return ("vincular" if usuario else "completar"), usuario


def autenticar_para_vincular(identidad, identificador, password):
    esperado = usuario_por_email(identidad.email)
    if esperado is None:
        raise CredencialesInvalidas()
    if "@" in identificador:
        encontrado = usuario_por_email(identificador.strip())
        identificador = encontrado.username if encontrado else ""
    dto = AutenticarUsuario(construir_repositorio(), construir_hasher()).ejecutar(identificador, password)
    if dto.id != str(esperado.id):
        raise CredencialesInvalidas()
    return dto


@transaction.atomic
def vincular_google(identidad, usuario_id):
    UsuarioModel.objects.select_for_update().get(pk=usuario_id)
    repo = construir_repositorio()
    usuario = repo.buscar_por_id(usuario_id)
    exigir_activo(usuario)
    if usuario.email.strip().lower() != identidad.email:
        raise CredencialesInvalidas()
    existente = GoogleVinculoModel.objects.filter(clave=clave_google(identidad.proyecto, identidad.uid)).first()
    if existente:
        if str(existente.usuario_id) != str(usuario.id):
            raise CredencialesInvalidas()
        return usuario
    GoogleVinculoModel.objects.create(usuario_id=usuario.id, proyecto=identidad.proyecto,
                                     uid=identidad.uid, email=identidad.email)
    return usuario


class SinPassword:
    def hash(self, _password):
        return make_password(None)


@transaction.atomic
def completar_google(identidad, datos):
    repo = construir_repositorio()
    usuario = GoogleVinculoRepository().buscar_usuario(identidad)
    if usuario is None:
        if usuario_por_email(identidad.email) is not None:
            # Apareció una cuenta durante el formulario: exigir vinculación, nunca fusionar.
            raise CredencialesInvalidas()
        username = "web." + sha256(identidad.email.encode()).hexdigest()[:26]
        if User.objects.filter(username=username).exists():
            # Un usuario técnico huérfano nunca debe transmitir privilegios a una cuenta nueva.
            raise CredencialesInvalidas()
        dto = CrearUsuario(repo, SinPassword()).ejecutar(UsuarioInputDTO(
            username=username, password="",
            nombre_completo=datos["nombre"], email=identidad.email, rol="CLIENTE"))
        usuario = repo.buscar_por_id(dto.id)
        GoogleVinculoModel.objects.create(usuario_id=usuario.id, proyecto=identidad.proyecto,
                                         uid=identidad.uid, email=identidad.email)
    UsuarioModel.objects.select_for_update().get(pk=usuario.id)
    usuario = repo.buscar_por_id(usuario.id)
    exigir_activo(usuario)
    if usuario.rol != "CLIENTE":
        raise CredencialesInvalidas()
    perfil = perfil_cliente(usuario)
    if perfil is None:
        RegistrarCliente(construir_cliente_repository()).ejecutar(ClienteInputDTO(
            nombre=datos["nombre"], dni=datos["dni"], email=identidad.email,
            telefono=datos["telefono"], direccion=datos.get("direccion", ""), usuario_id=str(usuario.id)))
    else:
        if perfil.dni and perfil.dni != datos["dni"]:
            raise CredencialesInvalidas()
        cliente_repo = construir_cliente_repository()
        cliente = cliente_repo.buscar_por_id(perfil.id)
        cliente.nombre = datos["nombre"]
        cliente.dni = DNI(datos["dni"])
        cliente.actualizar_contacto(email=identidad.email, telefono=datos["telefono"],
                                   direccion=datos.get("direccion", ""))
        cliente_repo.guardar(cliente)
    usuario.registrar_acceso_exitoso()
    repo.guardar(usuario)
    return UsuarioOutputDTO.desde_entidad(usuario)
