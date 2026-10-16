# Backup y restore

## Estrategia

- **Diario**: `mysqldump --single-transaction` comprimido con gzip (ver `scripts/backup_database.sh`).
- **Rotacion**: se conservan los ultimos 30 backups.
- **Media**: el directorio `media/` (imagenes) debe sincronizarse con `rsync`/S3.
- **Retencion recomendada**: 7 diarios + 4 semanales + 12 mensuales.

## Programacion (cron)

    0 2 * * * cd /opt/puntoventa_total && DB_PASSWORD=xxx ./scripts/backup_database.sh >> /var/log/puntoventa-backup.log 2>&1
    0 3 * * 0 rsync -av /opt/puntoventa_total/media/ respaldo:/backups/puntoventa/media/

## Restore

    ./scripts/restore_database.sh backups/puntoventa_20260101_020000.sql.gz

El script pide confirmacion antes de sobreescribir. Para practicar el restore:

    docker compose exec -T db mysql -upuntoventa -p puntoventa < backup.sql

## Verificacion periodic

Restaurar en un entorno de staging al menos una vez por mes y ejecutar
`bash scripts/check_health.sh`.

