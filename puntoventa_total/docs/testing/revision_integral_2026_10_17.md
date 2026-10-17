# Revision integral de PuntoVenta Total — 17/10/2026

Se revisaron configuracion, rutas, capas de negocio/persistencia, templates,
JavaScript, permisos, migraciones, despliegue y las pruebas de los diez modulos.
El alcance verificado y los limites del entorno se distinguen a continuacion.

## Correcciones aplicadas

| Area | Defecto | Correccion |
| --- | --- | --- |
| POS | Carrito vacio visualmente, totales fijos y enlace de cobro `#` | Renderizar lineas/totales persistidos y enlace de pago habilitado solo con productos |
| POS | UUID de rutas no coincide con IDs de dominio en cantidad/eliminacion | Normalizar identificadores y comprobar persistencia despues de recargar |
| Persistencia | Eliminar una linea no la elimina en la BD | Borrar los detalles retirados del agregado, incluso al vaciar el carrito |
| Validacion | Cantidades no numericas y monto efectivo invalido pueden producir 500 | Errores HTTP 400 para AJAX y validacion del formulario antes de comparar importes |
| Seguridad | Mutaciones por GET y acceso a ventas/tickets ajenos | POST obligatorio, CSRF existente y comprobacion de propietario; gerencia conserva consulta de tickets |
| Pagos parciales | Se pierde la venta de sesion y puede editarse un carrito con pagos | Conservar venta en curso y bloquear cambios del carrito despues del primer pago |
| Productos sin stock | Cobro intenta descontar existencias que no deben existir | Conservar `requiere_stock` en el detalle y respetarlo en cobro/anulacion |
| Promociones | Cambiar cantidades conserva porcentaje incorrecto de 2x1 | Recalcular por unidades; comprobar cantidades 1, 2, 3 y 4 y stock disponible |
| Precision | Convertir un regalo NX1 en porcentaje redondeado cambia su importe | Conservar el descuento monetario exacto calculado por el motor |
| Promociones | Un fallo inesperado del motor se transforma silenciosamente en descuento cero | Propagar el fallo para evitar agregar productos con un beneficio incorrecto |
| Caja | Sesion perdida impide recuperar un turno abierto | Consultar turno abierto del cajero y restaurar su identificador |
| Caja | Cierre pierde acceso al arqueo; formulario de anulacion no pide motivo | Enlazar arqueo del turno cerrado y mostrar campo obligatorio de motivo |
| Caja | Arqueo acepta IDs invalidos o turnos de otros cajeros | UUID validado y filtro de propietario |
| Auditoria | Listado oculta registros posteriores al numero 100 | Consultar el conjunto filtrado completo y paginar sin truncarlo |
| Auditoria | Repositorio puede sobrescribir registros declarados inmutables | Insercion append-only y rechazo de UUID duplicado |
| Paginacion | Cambiar pagina descarta filtros de auditoria | Conservar parametros de consulta con el tag `querystring` |
| Sesiones | Una identidad eliminada conserva acceso de una sesion real | Invalidar sesiones con `identity_role` cuya identidad ya no existe |
| Sesiones | Logout modifica sesion mediante GET | Formulario POST con token CSRF y rechazo de GET |
| Navegacion | Cliente ve enlaces administrativos y faltan enlaces de gestion | Menu segun rol, usuarios/productos/categorias/promociones/cierre e historial propio |
| JavaScript | Nombres y alertas se insertan como HTML | Crear nodos de texto para evitar ejecutar contenido inyectado |
| PWA | Worker limitado al directorio de su script; cache indiscriminada | Endpoint con alcance raiz y cache solo de estaticos locales exitosos |
| Templates | Parcial de producto usa `static` sin cargar la biblioteca | Agregar `{% load static %}` y compilar las 52 plantillas del proyecto |
| Desarrollo | Falta de Debug Toolbar bloquea arranque | Cargarlo cuando esta instalado y registrar sus URLs solo en desarrollo |
| Produccion | Logger depende de una carpeta inexistente | Logging por consola compatible con contenedores |
| Produccion | Imagen puede iniciar configuracion de desarrollo y copiar secretos/venvs | Settings explicitos y `.dockerignore` |
| Despliegue | Credenciales MySQL distintas entre Compose y `.env` | Unificar variables; exigir claves de aplicacion/root sin valores ocultos por defecto |
| Despliegue | HTTP local incompatible con cookies/redirect HTTPS de produccion | Overrides separados para demostracion local y HTTPS con certificados del dominio |
| Readiness | Nginx devuelve 200 fijo aunque la aplicacion falle | `/healthz` consulta SQL/cache y devuelve 503 sin detalles privados si falla |
| Dependencias | Versiones antiguas y avisos en REST Framework, Pillow, cryptography y Sentry | Django 5.2.18, REST Framework 3.17.2, Pillow 12.3.0, cryptography 50.0.2 y sentry-sdk 2.8.0; auditoria directa repetida |
| Desarrollo | Instalacion de desarrollo no incluye las bibliotecas de toda la suite | Heredar `requirements/testing.txt`, conservando las herramientas de desarrollo |
| Configuracion local | Clave Django debil | Generar clave aleatoria en `.env` sin mostrarla; sesiones previas deben reiniciarse |
| Rendimiento | Consultas repetidas al persistir la misma venta y registros nuevos | Reutilizar identidad ORM dentro de la instancia de repositorio e insertar registros nuevos directamente |
| Pruebas UI | `networkidle` no garantiza que se haya agregado el producto | Esperar respuesta AJAX y linea visible del carrito |
| Carga | Cobro medido dentro del servidor de pruebas instrumentado | Proceso WSGI independiente: Waitress en Windows, Gunicorn en Linux; conservar p95 <100 ms |

La migracion nueva es `sales.0005_detalleventamodel_requiere_stock`.
Incluye ajuste de detalles existentes segun los productos sin control de stock.
No se ha aplicado sobre una base de negocio inaccesible.

## Validacion

| Perfil | Runtime | Pruebas aprobadas | Fallos / omisiones | Cobertura global | Cobro p95 |
| --- | --- | ---: | --- | ---: | ---: |
| Produccion con dependencias corregidas | Python 3.11.16 / Django 5.2.18 | 650/650 | 0 / 0 | 90,01 % | 60,81 ms |
| QA independiente | Python 3.14.7 / Django 6.1.2 | 650/650 | 0 / 0 | 89,80 % | 87,92 ms |

Cada suite contiene **340 unitarias, 234 de integracion, 42 de sistema y 34 de
aceptacion automatizada**. Las suites completas terminaron con codigo de salida 0.
La ejecucion de produccion se repitio despues de instalar las versiones finales
de REST Framework, Pillow y cryptography. QA mantiene su perfil independiente,
cuyos paquetes no cambiaron con esas actualizaciones del archivo base.

El gate unitario de dominio/aplicacion dio 90,21 % en produccion y 89,87 % en QA;
el gate especifico RF-044..050 dio 87,85 % y 87,76 %, respectivamente. Son ambitos
de cobertura distintos de la cobertura global de los cuatro niveles.

La captura reproducible esta en `scripts/qa_site_audit_evidence.py` y conserva
JUnit, cobertura, resultados de k6 y huella SHA256 de los archivos verificados.
Los artefactos locales son `reports/site-final-production-evidence.json` y
`reports/site-final-qa-evidence.json`, junto con sus XML, JSON de cobertura y
snapshots de k6/Redis. `reports/` esta excluido de Git.

Tambien pasaron la compilacion de **52/52 templates**, **14/14 archivos
JavaScript**, el analisis sintactico de **8 YAML**, `pip check` del entorno de
produccion y `git diff --check`.

Las pruebas nuevas estan en:

- `tests/integration/test_revision_pagina.py`.
- `tests/system/test_revision_pagina_playwright.py`.
- `tests/unit/application/test_revision_descuentos.py`.

Se verificaron tambien `manage.py check`, consistencia de migraciones y Ruff
para errores fatales/identificadores indefinidos (`F821,F822,F823,E9`). Esto
no equivale a afirmar que todos los avisos de estilo del repositorio estan resueltos.

La consulta de seguridad con pip-audit termino sin vulnerabilidades conocidas
en los **14 paquetes directos fijados**, consultando explicitamente
`requirements/base.txt` y `requirements/production.txt` en la misma ejecucion.
No es un analisis exhaustivo de dependencias transitivas ni una garantia futura.

## Entorno real pendiente

`python scripts/check_runtime.py` comprueba el entorno configurado sin imprimir
credenciales. En esta maquina Django, cache de desarrollo y estaticos pasan;
la conexion a MySQL local falla con `OperationalError`, codigo 2002.
Se solicito confirmar donde existe la base real. No se ha creado una base vacia
para sustituir datos existentes ni modificado credenciales de base de datos.

Cuando la base correcta este accesible, ejecutar desde `puntoventa_total`:

```powershell
rtk proxy .venv-production\Scripts\python.exe manage.py migrate
rtk proxy .venv-production\Scripts\python.exe scripts/check_runtime.py
rtk proxy .venv-production\Scripts\python.exe manage.py runserver
```

Para crear un administrador, `scripts/crear_admin.py` solicita su clave sin
mostrarla cuando no se proporciona `--password`; se retiro la clave publica
por defecto. No ejecutar un reseteo sobre un usuario existente sin necesitarlo.

## Limites de la evidencia

- MySQL y Redis se levantan como procesos temporales reales; no se uso Docker
  local ni se ejecuto Nginx/TLS en esta maquina.
- Waitress local no acredita el rendimiento del despliegue Linux/Gunicorn.
  El workflow raiz conserva Gunicorn y debe verificarse en su runner.
- Los tests de correo usan SMTP local. Correo/SMS productivos necesitan un
  proveedor configurado; el adaptador SMS existente no acredita entregas reales.
- Cachear estaticos no implementa por si solo ventas offline completas.
- `check --deploy` conserva el aviso opcional HSTS preload. No se activo la
  inclusion de un dominio en listas de navegadores sin disponer del despliegue TLS.
- Los planes maestros previos contienen evidencia historica; no certifican
  automaticamente esta revision posterior.
- Ninguna suite permite prometer que una pagina funciona al 100% en todo entorno.

## Referencias utilizadas

- [Correcciones de seguridad Django del 06/10/2026](https://www.djangoproject.com/weblog/2026/oct/06/security-releases/).
- [Checklist oficial de despliegue Django](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).
- [Waitress: compatibilidad y uso WSGI en Windows](https://docs.pylonsproject.org/projects/waitress/en/stable/).
