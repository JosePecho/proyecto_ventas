# Puesta en produccion

## Topologia

```
Internet -> nginx (estaticos + proxy) -> gunicorn (web:8000)
                                       -> celery worker (tareas)
                                       -> celery beat (programados)
          MySQL 8 (volumen persistente) + Redis 7 (cache/cola)
```

## Pasos

1. Generar secret: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`.
2. `.env` de produccion: `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS=dominio.com`,
   `SECURE_SSL_REDIRECT=true`, credenciales de DB/Redis dedicadas.
3. `docker compose up -d --build`
4. `docker compose exec web python manage.py migrate --noinput`
5. `docker compose exec web python manage.py collectstatic --noinput`
6. `docker compose exec web python scripts/crear_admin.py --username admin --password <fuerte>`
7. Certificado TLS: usar certbot en el host y apuntar nginx a los certificados.
8. Activar backups: cron con `scripts/backup_database.sh` (ej. 02:00 diario).
9. Verificar alertas en Prometheus (`monitoring/alerts.yml`).

## Operacion

- Logs: `docker compose logs -f web worker beat`.
- Escalar workers: variable `GUNICORN_WORKERS` (2*CPU+1) y `--concurrency` del worker.
- Ventanas de mantenimiento: detener `beat` y `worker` antes de migrar.

## Rollback

1. `git checkout <tag anterior>`
2. `docker compose up -d --build`
3. Restaurar la migracion anterior solo si el esquema cambio
   (`scripts/restore_database.sh <backup previo>`).

