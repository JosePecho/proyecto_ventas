# Validación completa del sistema

Se ejecutaron **385 pruebas, sin omisiones, xfail ni fallos**, en ambos perfiles:

| Perfil | Runtime / Framework | Infraestructura | Cobertura global |
|---|---|---|---:|
| QA | Python 3.14.7 / Django 6.1.2 | MySQL 8.4.3, Redis 8.10.2, worker Celery real, SMTP local, Chromium y k6 2.3.0 | 82,11 % |
| Producción declarada | Python 3.11.16 / Django 5.0.6 | La misma infraestructura efímera real | 82,50 % |

El 100 % del inventario de pruebas se ejecutó. Esto no significa cobertura de código
del 100 % ni una garantía de ausencia de defectos.

Durante estas validaciones se corrigieron también:

- Dependencias incompatibles del perfil de producción: PyMySQL RSA necesitaba un
  cryptography incompatible con el declarado. El perfil Python 3.11 ahora instala
  y ejecuta correctamente su conjunto de dependencias.
- Broker Celery de pruebas contaminado por `.env`: las comprobaciones usan el Redis
  efímero explícito y prueban una tarea de inventario real, además de entrega/resultados.
- Tareas de promociones y pedidos ausentes de CELERY_IMPORTS.
- Colisión de tickets entre cajas: secuencia diaria persistente y reserva atómica,
  probada con ocho escritores simultáneos y seis cobros HTTP con k6.
- Deadlock de inicialización de esa secuencia: upsert con bloqueo exclusivo en MySQL.
- Migraciones iniciales ausentes en ocho módulos y nueva migración separada para la
  secuencia de tickets. Son compatibles con ambos perfiles de Django.
- CI MySQL usando `localhost`, que mysqlclient en Linux convertía a un socket Unix
  ignorando el puerto del contenedor: el wrapper ahora fuerza TCP con 127.0.0.1.

El SMTP de pruebas recibe el mensaje real por socket y comprueba destinatario/cuerpo.
No se contactó a clientes ni se enviaron SMS o correos a destinatarios reales.

## Reproducción sin servicios persistentes

`qa_download_tools.py` descarga ZIP portables desde las publicaciones de sus
mantenedores y verifica el digest SHA256 publicado por GitHub. Redis Windows es
el port comunitario `redis-windows/redis-windows`, usado solo para QA local;
CI usa el contenedor Redis Linux. Las herramientas quedan en carpetas temporales.

Desde `puntoventa_total`:

```powershell
rtk proxy .venv/Scripts/python.exe scripts/qa_redis_native.py --binary C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/redis/8.10.2/Redis-8.10.2-Windows-x64-cygwin/redis-server.exe --mysql-basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --k6-binary C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/k6/v2.3.0/k6-v2.3.0-windows-amd64/k6.exe --coverage --report-prefix complete-qa
rtk proxy .venv-production/Scripts/python.exe scripts/qa_redis_native.py --binary C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/redis/8.10.2/Redis-8.10.2-Windows-x64-cygwin/redis-server.exe --mysql-basedir C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64 --k6-binary C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/k6/v2.3.0/k6-v2.3.0-windows-amd64/k6.exe --coverage --report-prefix complete-production
```

El wrapper crea instancias aisladas con puertos y claves aleatorios, ejecuta la
suite y detiene las instancias al finalizar. `QA_REQUIRE_ALL_TESTS=1` hace fallar
la ejecución completa si aparece cualquier omitido o xfail.

## Migraciones y despliegues existentes

Instalación vacía: `python manage.py migrate --noinput`.
Para una BD existente cuyas tablas fueron creadas sin migraciones Django, revisar
primero su esquema y las migraciones iniciales; después usar `migrate --fake-initial`
solo si coinciden. La secuencia está en sales/0002 y debe crearse realmente.
No se ejecutaron migraciones contra datos de negocio durante esta validación.
Las reservas de correlativos pueden dejar huecos si una venta posterior falla;
no se reutilizan y no se presentan como numeración fiscal certificada.

## Evidencia

- `reports/complete-qa.xml`, `complete-qa-coverage.json/xml`.
- `reports/complete-production.xml`, `complete-production-coverage.json/xml`.
- `reports/k6-pos-summary.json`, `k6-pos-output.txt`: thresholds, checks y latencias.
- `reports/redis-real.json`: Redis real y salida de la ejecución conjunta.

## Servicios externos

La entrega a teléfonos reales requiere proveedor SMS, credenciales y remitente
habilitado; no se inventaron credenciales ni se contrató un servicio de pago.
La aceptación del Product Owner requiere una persona responsable y no puede
sustituirse por una declaración del agente.
El resultado de GitHub Actions se registrará con su enlace y commit verificables.
