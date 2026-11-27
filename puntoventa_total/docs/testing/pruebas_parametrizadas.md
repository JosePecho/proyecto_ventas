# Pruebas parametrizadas

Las matrices nuevas usan `pytest.mark.parametrize` y fixtures parametrizadas.
Cada combinacion aparece como un caso independiente con su identificador en pytest y JUnit.

Validacion del 30 de octubre de 2026 tras corregir los formularios de telefono:
1395 pruebas correctas, sin fallos. Incluye los 946 casos nuevos, 40 casos
adicionales de formato de telefono y 32 casos de advertencias en Chromium. Ruff pasa sobre los archivos
agregados y los formularios corregidos. El inventario previo registra
226 clases con cuerpos de metodos ejecutados por casos parametrizados, ninguna
pendiente y 117 clases sin cuerpo medible (declarativas o contratos abstractos).

| Archivo | Contratos comprobados |
| --- | --- |
| `tests/unit/domain/test_entidades_parametrizadas.py` | Identidad y eventos aislados en todas las entidades derivadas de BaseEntity; campos obligatorios, cantidades, puntos, bloqueo, movimientos y auditoria |
| `tests/unit/domain/test_valores_politicas_parametrizados.py` | Montos, monedas, DNI, codigos, precios, descuentos, pagos, fechas y politicas de permisos, frecuencia, inventario y caja |
| `tests/unit/test_contratos_clases_parametrizados.py` | Formularios descubiertos por clase y eventos de dominio; controles invalidos, aislamiento y serializacion |
| `tests/unit/application/test_recursos_inexistentes_parametrizados.py` | 35 casos de uso ante tres identificadores inexistentes, con errores de dominio y ausencia de efectos externos |
| `tests/unit/test_mappers_parametrizados.py` | Conversion de entidades a modelos y de vuelta, actualizacion de instancias existentes, decimales, ceros, nulos y detalles de auditoria historicos |
| `tests/integration/test_repositorios_parametrizados.py` | Persistencia y actualizacion con ORM real en la base temporal de pytest-django; ventas y pedidos con distintas cantidades |
| `tests/unit/domain/test_tipos_publicos_parametrizados.py` | Opciones de todos los enums y contratos de mensajes/codigos de todas las excepciones de dominio |
| `tests/unit/application/test_consultas_parametrizadas.py` | Consultas, alertas, reportes, filtros por categoria, contratos predeterminados de repositorios y DTOs de salida |
| `tests/unit/test_servicios_infraestructura_parametrizados.py` | Hashes, correos locales, SMS sin proveedor, PDF/CSV, tickets y logs |
| `tests/unit/test_reglas_formularios_parametrizadas.py` | Fechas, ajustes con signo, referencia de pago, efectivo entregado y contrasenas |
| `tests/unit/test_modelos_parametrizados.py` | Etiquetas de identificacion de todos los modelos en listados administrativos |
| `tests/integration/test_adaptadores_parametrizados.py` | Cobro y anulacion con adaptadores reales, reservas, reportes, historial y rollback/contexto del middleware de auditoria |
| `tests/system/test_telefono_advertencia_playwright.py` | Ventana de error, bloqueo del envio, correccion, escritura del decimo digito y pegado excesivo en los cuatro formularios |

La base temporal usa `config.settings.testing`; estas pruebas no validan MySQL,
Redis, SMTP, proveedores externos ni el navegador.
Las dependencias de los casos de uso se sustituyen localmente por mocks;
las pruebas de repositorios usan el ORM y una base de pruebas real SQLite.

## Ejecutar solo los casos nuevos

Desde `puntoventa_total`, en PowerShell:

```powershell
rtk proxy .\.venv\Scripts\python.exe -m pytest tests/unit tests/integration/test_repositorios_parametrizados.py tests/integration/test_adaptadores_parametrizados.py -k parametriz -q -p no:cacheprovider --junitxml=reports/parametrizadas_nuevas.xml
```

## Ejecutar junto con las unitarias existentes y medir por clase

```powershell
rtk proxy .\.venv\Scripts\python.exe -m pytest tests/unit tests/integration/test_repositorios_parametrizados.py tests/integration/test_adaptadores_parametrizados.py -q -p no:cacheprovider --cov=src --cov-config=tests/parametrizadas.coveragerc --cov-context=test --cov-fail-under=0 --cov-report=json:reports/parametrizadas_cobertura.json --junitxml=reports/parametrizadas_resultados.xml --cov-report=
rtk proxy .\.venv\Scripts\python.exe scripts/reporte_clases_parametrizadas.py
```

El umbral global se desactiva solo para esta medicion parcial: no se ejecuta
la suite completa de sistema/integracion y no se modifica el gate general del proyecto.
La configuracion de coverage usa `ctrace`: el motor `sysmon` de Python 3.14
no soporta los contextos dinamicos necesarios para atribuir lineas a casos parametrizados.

El inventario `reports/parametrizadas_clases.md` enumera todas las clases de `src`
excepto migraciones y diferencia cuerpos ejecutados por casos parametrizados,
cuerpos pendientes y clases sin cuerpo medible (por ejemplo, DTOs declarativos).
No cuenta la mera importacion como prueba ni equipara ejecutar una linea con
probar todas las reglas de una clase. La ampliacion no acredita cobertura funcional
completa de todas las clases de la aplicacion.

El alcance del inventario es por clase: tener lineas ejecutadas por un caso
parametrizado no implica tener todas las ramas cubiertas. Las clases declarativas
y los contratos abstractos sin implementacion se enumeran aparte.

## Contrato de telefono peruano

Por requisito del usuario, los formularios de perfil, registro de cliente,
registro web y pedido admiten celulares peruanos de exactamente nueve digitos,
comenzando con 9, sin prefijo `+51`. La regla compartida valida tanto el servidor
como los atributos HTML (`pattern`, `maxlength` y `minlength`). El telefono
es obligatorio en el registro web y conserva su caracter opcional en los demas
formularios. Las pruebas incluyen longitudes incorrectas, prefijos internacionales,
letras, separadores, digitos Unicode y numeros que no comienzan con 9.

La ventana de advertencia indica cuantos digitos se ingresaron y cuantos faltan
o sobran. La escritura o el pegado de mas de nueve caracteres se rechaza con
explicacion, conservando el valor previo. Al cerrar la ventana, el foco vuelve
al telefono; al corregirlo se puede enviar el formulario. La comprobacion cubre
tambien formularios con `novalidate`, y Django conserva la validacion del servidor.

Para comprobar las 32 interacciones en Chromium instalado:

```powershell
rtk proxy .\.venv\Scripts\python.exe -m pytest tests/system/test_telefono_advertencia_playwright.py -q -p no:cacheprovider
```
