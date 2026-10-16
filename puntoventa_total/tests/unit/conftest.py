"""Unitarias sin BD: pytest-django bloquea su acceso por defecto.

Los casos de uso reciben UnitOfWork y usan NullUnitOfWork en ausencia de uno.
No se sustituye globalmente transaction.atomic: eso ocultaria acoplamientos
accidentales con infraestructura. Cada test inyecta sus propios puertos.
"""
