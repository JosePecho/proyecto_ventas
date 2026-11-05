"""Vinculación explícita; la clave hash conserva la sensibilidad del UID a mayúsculas."""
import hashlib
import uuid

from django.db import models


def clave_google(proyecto, uid):
    return hashlib.sha256((proyecto + "\0" + uid).encode()).hexdigest()


class GoogleVinculoModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.OneToOneField("identity.UsuarioModel", on_delete=models.PROTECT, related_name="google_vinculo")
    clave = models.CharField(max_length=64, unique=True, editable=False)
    proyecto = models.CharField(max_length=128)
    uid = models.CharField(max_length=128)
    proveedor = models.CharField(max_length=20, default="google.com", editable=False)
    email = models.EmailField()
    fecha_vinculacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_google_vinculo"
        constraints = [models.UniqueConstraint(fields=["proyecto", "email"], name="google_proyecto_email_unico")]

    def save(self, *args, **kwargs):
        self.clave = clave_google(self.proyecto, self.uid)
        self.email = self.email.strip().lower()
        super().save(*args, **kwargs)
