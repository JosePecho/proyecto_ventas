# Componentes del entorno QA local

Verificación del 19 de octubre de 2026, entorno `puntoventa_total/.venv`.

Se completó el perfil existente sin cambiar sus versiones de Django/Pytest.

| Componente agregado | Versión |
| :--- | :--- |
| Ruff | 0.4.4 |
| Freezegun | 1.5.0 |
| Responses | 0.25.0 |
| pytest-xdist | 3.6.1 |
| Execnet, dependencia de pytest-xdist | 2.1.2 |

Las dependencias de `requirements/qa-inventory-mysql.txt` ya estaban satisfechas.
Se agregó `requirements/qa-tools.txt` para reproducir la instalación:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements/qa-tools.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m ruff check src config scripts tests --select F821,F822,F823,E9
```

`pip check` y el control Ruff indicado finalizaron correctamente.
Después de la instalación, `python scripts/qa_semana9.py completa` también pasó:
34 casos, cero fallos, 8.08 s reportados por Pytest y 21.812 s de pared.
Los logs se guardaron en `reports/semana9/completa.*`.

También se comprobó la presencia del Chromium requerido por Playwright 1.64.0 y
se ejecutaron los comandos de versión de las herramientas portables existentes:

| Herramienta | Versión | Ruta |
| :--- | :--- | :--- |
| MySQL | 8.4.3 | `C:/Users/mallq/AppData/Local/Temp/qa-mysql-binaries/mysql-8.4.3-winx64/bin/mysqld.exe` |
| Redis | 8.10.2 | `C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/redis/8.10.2/Redis-8.10.2-Windows-x64-cygwin/redis-server.exe` |
| k6 | 2.3.0 | `C:/Users/mallq/AppData/Local/Temp/puntoventa-qa-tools/k6/v2.3.0/k6-v2.3.0-windows-amd64/k6.exe` |
| Chromium | revisión 1248 | `C:/Users/mallq/AppData/Local/ms-playwright/chromium-1248` |

Estas herramientas portables no están en el PATH global. Sus rutas son las que
usan los wrappers existentes documentados en `complete_validation.md`; las
ubicaciones temporales deben conservarse o restaurarse si Windows las limpia.
La comprobación de presencia/versión no implica que los servicios estén iniciados.

Docker es una alternativa opcional documentada por el proyecto, no está disponible
en el PATH y no se instaló. El proyecto dispone de wrappers MySQL/Redis nativos para
ejecutar QA sin contenedores. Tampoco se instalaron herramientas interactivas
opcionales del perfil de desarrollo ni se mezcló ese perfil con el entorno QA.
