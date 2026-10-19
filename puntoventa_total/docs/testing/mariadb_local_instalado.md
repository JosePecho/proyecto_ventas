# MariaDB compatible instalado

Instalación y comprobaciones realizadas el 19 de octubre de 2026.

Se instaló **MariaDB 10.11.19** desde el [paquete oficial de Windows](https://dlm.mariadb.com/browse/mariadb_server/10.11.19/winx64-packages/).
La instalación ZIP sigue el [procedimiento oficial](https://mariadb.com/docs/server/server-management/install-and-upgrade-mariadb/installing-mariadb/binary-packages/installing-mariadb-windows-zip-packages).
Se verificó el SHA256 publicado antes de extraer y ejecutar el paquete:

```text
398ea30e5036010bbebe01d2b1804280424dcc2626e36d8e95155c04d25a0490
```

## Conexión activa de la aplicación

| Dato | Valor |
| :--- | :--- |
| Servidor | 127.0.0.1 |
| Puerto | 3307 |
| Base | punto_venta |
| Usuario local | root |
| Contraseña local | Vacía, según configuración solicitada |
| Motor | MariaDB 10.11.19 |
| Aplicación | http://127.0.0.1:8000/ |
| phpMyAdmin | http://localhost/phpmyadmin/index.php?route=/database/structure&server=2&db=punto_venta |

La configuración se guardó en `.env`, excluido de Git. La aplicación se reinició
con `config.settings.development`; la vista SQLite anterior se detuvo.

El servidor original de XAMPP, MariaDB 10.4.32 en el puerto 3306, permanece
disponible como servidor 1 de phpMyAdmin. El servidor compatible es el servidor 2,
rotulado **Punto Venta - MariaDB 10.11 (3307)** y configurado como predeterminado.
Ambos tienen una base llamada `punto_venta`: la aplicación usa la del **3307**.

## Respaldo y datos

La base original estaba vacía. Antes de trasladarla se generaron respaldos SQL:

- `reports/punto_venta-xampp-previo-20261019.sql`
- `reports/backups/punto_venta-xampp-20261019-105523.sql`

Se restauró la base en la nueva instancia, se aplicaron las migraciones reales y
se cargaron cinco categorías, seis productos y cuatro usuarios de demostración.
La base contiene 28 tablas. El usuario de la aplicación es `admin` y su contraseña
de demostración es `Cambio1234!`; es distinto del usuario `root` de la base de datos.

El archivo phpMyAdmin original se respaldó en:
`C:/xampp2/phpMyAdmin/config.inc.php.backup-20261019-105639`.
La configuración nueva pasó la comprobación de sintaxis PHP.

Los binarios están en `reports/mariadb-local/mariadb-10.11.19-winx64/`.
El directorio `reports/mariadb-local/data/` contiene **los datos activos** de la
instancia y debe conservarse, junto con `reports/mariadb-local/my.ini`.
No se registró un servicio de Windows: el proceso se inicia en segundo plano.

## Volver a iniciar después de reiniciar Windows

Inicia Apache desde XAMPP para acceder a phpMyAdmin. Desde `puntoventa_total`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/iniciar_punto_venta.ps1 -AbrirNavegador
```

El script inicia MariaDB compatible y la aplicación. El MySQL antiguo de XAMPP
puede seguir funcionando en 3306. No es necesario apagarlo para usar 3307.

## Verificación ejecutada

- Conexión correcta desde Django 6.1.2 y Django 5.2.18.
- `scripts/check_runtime.py`: Django, base de datos, migraciones, caché y estáticos correctos.
- Sin migraciones pendientes.
- Navegador Chromium real: login `admin`, redirección al catálogo y producto visible.
- Navegador Chromium real: phpMyAdmin muestra `django_migrations` y las tablas de `punto_venta` en servidor 2.
- Capturas: `reports/mariadb-local/catalogo-mariadb.png` y `phpmyadmin-punto-venta.png`.
- Fuentes y SHA256 registrados en `reports/mariadb-local/source.json`.

La verificación de esta instalación cubre conexión, esquema y navegación indicada;
no representa una nueva ejecución de toda la regresión del repositorio.
