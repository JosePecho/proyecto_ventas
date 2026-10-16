# Migraciones

- Django descubre las migraciones en `src/modules/<modulo>/migrations/` por defecto.
  Las carpetas `infrastructure/persistence/migrations/` no se usan sin configurar
  explicitamente `MIGRATION_MODULES`.
- Los modelos se importan en `src/modules/<modulo>/models.py` para que las aplicaciones
  los descubran en el arranque.

## Flujo

    python manage.py makemigrations identity catalog inventory sales cash_register \
                                orders customers promotions auditing
    python manage.py migrate

Para bases anteriores sin historial de migraciones de catalogo, usar
`python manage.py migrate catalog --fake-initial`. La migracion inicial representa
el esquema anterior; la siguiente agrega minimo y vencimiento. Ver
`docs/requirements/inventario_rf016_rf024.md`.

## Reglas

1. Nunca editar una migracion ya aplicada en produccion; crear una nueva.
2. Cambios destructivos (borrar columna) se hacen en dos pasos: deprecar + limpiar en
   una migracion posterior.
3. Agregar indices para toda columna filtrada en reportes (ya incluidos en los Meta).
4. `deployment/mysql/init.sql` solo configura charset, zona horaria y privilegios:
   el esquema lo definen las migraciones.

