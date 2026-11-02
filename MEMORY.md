# Memoria del proyecto

Última actualización: 2026-11-02. Este archivo conserva contexto de trabajo; las instrucciones para contribuir están en [AGENTS.md](AGENTS.md).

## Contexto y organización

- Proyecto ABP: **PuntoVenta Total**, sistema de ventas, inventario, caja, pedidos, clientes, promociones y reportes.
- Aplicación en `puntoventa_total/`: Python 3.11+, Django y arquitectura de monolito modular con Clean Architecture.
- Cada módulo de `src/modules/` separa dominio, aplicación, infraestructura y presentación. Código transversal en `src/shared/`.
- Pruebas en `tests/`; plantillas en `templates/`; recursos en `static/`; documentación en `docs/`.
- Entorno de trabajo observado: Windows y PowerShell. Prefijar comandos de shell con `rtk`; usar `rtk proxy` cuando corresponda.
- Conservar cambios previos del usuario y nombres de negocio en español. No guardar credenciales en este archivo.

## Ejecución local

Ejecutar desde `puntoventa_total/`, usando el entorno virtual existente:

```powershell
rtk proxy .venv/Scripts/python.exe scripts/mariadb_local.py start
rtk proxy .venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

La instancia local existente de MariaDB 10.11.19 usa el puerto 3307. La web respondió HTTP 200 en `http://127.0.0.1:8000/` durante esta sesión. Confirmar que los procesos siguen activos antes de reutilizarlos; este registro no garantiza su disponibilidad futura. No iniciar otra instancia sobre el mismo puerto.

## Comprobaciones habituales

```powershell
rtk proxy .venv/Scripts/python.exe manage.py check --settings=config.settings.testing
rtk proxy .venv/Scripts/python.exe -m ruff check .
rtk proxy .venv/Scripts/python.exe scripts/check_assets.py --javascript
rtk proxy .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
```

Pytest usa `config.settings.testing` y SQLite aislado por defecto. El umbral general configurado de cobertura es 80%. Las pruebas de navegador requieren Chromium/Playwright. Las suites específicas de MySQL, Redis y k6 necesitan infraestructura explícita; una omisión no equivale a una prueba aprobada.

## Trabajo realizado

- Corregidos indentación y retorno del DNI opcional en el formulario de registro de clientes.
- Resueltas incidencias de Ruff y añadidas excepciones justificadas para fixtures de Pytest y convenciones públicas existentes.
- Ocultados iconos decorativos a lectores de pantalla para conservar nombres accesibles de botones.
- Adaptadas pruebas de navegador al botón «Guardar producto» y al horario automático de recojo.
- Añadidas pruebas de caja blanca, fallos, orden de operaciones, pagos sucesivos y rollback durable del cobro.

## Semana 11: evidencia y alcance

Componente analizado: `ProcesarPago.ejecutar`, en `src/modules/sales/application/use_cases/procesar_pago.py`.

- CFG explícito: 9 predicados, 26 nodos, 34 aristas; **McCabe = 10** y rango de la base de caminos = 10.
- El modelo incluye cortocircuitos y excluye excepciones implícitas de colaboradores. Algunos caminos de la base aislada usan estados sintéticos; no todos representan ventas válidas.
- **38 casos aprobados**: 17 estructurales/regresiones, 12 de coordinación/excepciones y 9 de persistencia.
- Cobertura medida del archivo: **40/40 sentencias y 10/10 ramas**, 100%. Las ramas de coverage.py no equivalen a los caminos McCabe.
- Los 9 casos de persistencia también pasaron en MySQL 8.4.3/InnoDB desechable. Comprueban rollback y reintentos con `transaction.atomic()` y `MySQLUnitOfWork`.
- La ampliación de pruebas no requirió modificar el método productivo. `NullUnitOfWork` no ofrece rollback de BD.

Archivos principales, relativos a `puntoventa_total/`:

- `docs/testing/semana11_caja_blanca.md`: informe completo, matriz y código reproducido.
- `tests/unit/application/test_semana11_procesar_pago.py`.
- `tests/unit/application/test_semana11_fallos_cobro.py`.
- `tests/integration/test_semana11_rollback_cobro.py`.
- `scripts/qa_semana11_caja_blanca.py`: valida CFG, rango, cobertura y resultados JUnit; requiere generar antes ambos reportes indicados en el informe.
- `reports/semana11-cobertura.json`, `reports/semana11-html/index.html`, `reports/semana11-pruebas.xml`.
- `reports/semana11-rollback-mysql.xml` y `.json`.

## Última regresión y pendientes

La última ejecución general produjo **1743 aprobadas, 12 omitidas y 0 fallos**; evidencia en `puntoventa_total/reports/semana11-regresion-completa.xml`.

Las omisiones corresponden a 8 casos de otras suites que exigen MySQL/InnoDB, 1 de Redis/Celery y 3 de k6. Los 9 casos de rollback ejecutados aparte en MySQL son los mismos casos ya probados con SQLite: no sumarlos como pruebas únicas adicionales.

Redis portable no pudo iniciar; devolvió el código de Windows `0xC0000135`, compatible con una dependencia ausente. Las pruebas omitidas de Redis y k6 siguen sin acreditar ejecución en esta revisión.

La aprobación humana de la auditoría de refactorización sigue **pendiente**. No atribuirla a la IA ni dar por superado ese control. La referencia «Beck, 2022» necesita título y edición para una atribución bibliográfica precisa.

Estos resultados describen ejecuciones históricas, no garantías sobre cambios posteriores. Regenerar evidencia tras modificar el componente; las rutas de binarios temporales del informe dependen del equipo.
