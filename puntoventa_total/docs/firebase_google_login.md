# Registro e inicio de sesión con Google

## Recuperación y respaldo

- Rama: `feature/firebase-google-login`.
- Commit recuperable anterior al registro automático: `744461e`.
- Respaldo privado previo: `C:/Users/mallq/.puntoventa-backups/20261105T154442Z/puntoventa-completo.sql`.
- Verificación: restauración en una base temporal aislada, comparación de las 28 tablas,
  esquemas y 346 registros mediante SHA256 por registro. La base temporal se eliminó
  después de aprobar la comparación. No se restauró sobre la base original.
- El directorio tiene permisos restringidos al usuario de Windows y SYSTEM. No está
  en Git ni en OneDrive. Su manifiesto es `verificacion.json` y no contiene datos de las filas.

`scripts/verificar_respaldo_google.py` corresponde a la comprobación previa de la
base de 28 tablas. No debe repetirse sobre una base que ya tenga otras migraciones.

## Configuración

La dependencia de servidor es `firebase-admin==7.7.0`; los módulos web son Firebase
App y Auth 13.2.0. Analytics no se inicializa. En `.env`, excluido de Git:

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=C:/Users/mallq/.firebase/puntoventa-a7f93-admin.json
FIREBASE_PROJECT_ID=puntoventa-a7f93
FIREBASE_GOOGLE_ENABLED=True
```

La configuración web es pública. No se envía ninguna clave privada al navegador ni
se registran tokens. El adaptador rechaza `FIREBASE_AUTH_EMULATOR_HOST`.

Firebase Console → Authentication → Sign-in method: Google habilitado y correo de
soporte configurado. Authentication → Settings → Authorized domains: `localhost` y
`127.0.0.1`, sin esquema ni puerto. La última consulta remota confirmó ambos.

El servidor necesita HTTPS saliente hacia los servicios Google para consultar
certificados, revocación y cuentas. Ejecutarlo desde una terminal normal de VS Code
o con permiso de red; un proceso dentro del entorno restringido de Codex devuelve
`WinError 10013` y el acceso Google falla de forma segura con HTTP 503.

## Política y flujo

1. **UID ya vinculado:** se recupera el usuario correspondiente y se comprueba que
   siga activo y no bloqueado. Sus roles y permisos permanecen locales.
2. **Gmail nuevo:** se muestra el formulario para completar nombre, DNI y celular.
   El correo verificado es inmutable en el formulario; dirección opcional.
3. **Correo existente sin vinculación:** se pide usuario/email, contraseña tradicional
   y confirmación explícita. Esto también se exige a administradores y empleados.
4. **Cliente con perfil ausente o incompleto:** completa los datos antes de iniciar
   sesión. Un perfil de cliente desactivado o ambiguo se rechaza.
5. **Resultado exitoso:** redirección directa al catálogo; se ignora `next` para Google.

Solo se admite Gmail verificado con proveedor `google.com`. Los correos no Gmail
siguen utilizando el acceso tradicional. Las cuentas nuevas reciben exclusivamente
`CLIENTE`, nunca `is_staff` ni `is_superuser`, y una contraseña inutilizable.
No se cambia la contraseña de cuentas existentes. Este cambio no añade un flujo
para establecer contraseña en cuentas creadas exclusivamente mediante Google.

El estado pendiente reside en la sesión de Django, caduca a los 10 minutos y no
contiene el ID token. Antes de guardar se vuelve a consultar Firebase para comprobar
baja, correo/proveedor y revocación. El usuario puede cancelar sin crear cuentas.

Se reutilizan `CrearUsuario`, `AutenticarUsuario`, `RegistrarCliente`, las validaciones
de `RegistroClienteForm` y los repositorios existentes. DNI de 8 dígitos; celular
peruano de 9 dígitos empezando por 9. Un DNI existente no vincula ni fusiona personas.
No se omiten los registros inactivos al comprobar duplicados.

El alta de usuario, perfil y vínculo se realiza en una transacción. Se revierte si
falla el perfil, una restricción única o la creación de sesión. Los identificadores
deterministas de usuario y las restricciones evitan duplicados concurrentes.

La sesión conserva `rol`, `identity_role`, `usuario_id` y `cliente_id`. El cierre sigue
siendo el POST con CSRF existente. Firebase usa persistencia en memoria y `signOut`
después del intercambio. Desactivar un usuario o cambiar su rol sigue invalidando
su sesión mediante el middleware existente.

## Migración

`identity.0002_googlevinculomodel` crea únicamente `identity_google_vinculo`:

- FK uno a uno a `identity_usuario`, con eliminación protegida.
- Proyecto, UID, proveedor, correo y fecha de vinculación.
- Clave SHA256 única de proyecto + UID: evita comparaciones de UID insensibles a
  mayúsculas en MariaDB/MySQL.
- Restricción única de proyecto + correo.

No vincula automáticamente cuentas antiguas ni cambia las tablas comerciales.
Django añade el tipo de contenido y los cuatro permisos técnicos del nuevo modelo;
no se asignan a usuarios ni grupos. El script `aplicar_migracion_google.py` valida
el respaldo, exige ese único paso pendiente y comprueba la conservación de datos
previos, admitiendo únicamente esos metadatos nuevos de Django.

## Archivos principales

Todo el código de negocio nuevo se limita al módulo `identity`:

- DTO/puertos de identidad Google y autenticación por vínculo.
- Adaptador Firebase con verificación y revalidación de identidad.
- Modelo, repositorio y migración del vínculo Google.
- Coordinador transaccional `infrastructure/google_registration_service.py`.
- Formularios y vistas de alta/vinculación, rutas y limpieza del estado pendiente
  al establecer una sesión.
- `templates/identity/google_datos.html`: continuación con las clases y estilos
  actuales del login. No se alteró el CSS ni el diseño del login existente.
- Scripts de respaldo, ensayo MariaDB y aplicación comprobada de la migración.
- Pruebas de integración, concurrencia, adaptador Firebase y navegador.

No se modifican archivos de ventas, productos/catálogo, inventario, clientes,
pedidos ni reportes. El registro escribe perfiles de cliente utilizando su lógica
existente, sin cambiar esas funcionalidades.

## Comprobación manual

1. Abrir `http://127.0.0.1:8000/` y cerrar cualquier sesión previa.
2. Pulsar **Continuar con Google** y elegir un Gmail nuevo.
3. Completar nombre, DNI único y celular. Tras guardar debe aparecer el catálogo
   con los permisos de cliente.
4. Cerrar sesión y repetir con ese Gmail: debe ir directamente al catálogo.
5. Probar un correo local existente no vinculado: debe pedir sus credenciales y
   consentimiento. Tras vincular, debe conservar su rol original.
6. Verificar también el acceso tradicional con una cuenta que ya tenga contraseña.

El selector real se comprueba sin introducir credenciales personales. Los escenarios
de registro/vinculación se automatizan con navegador y backend reales sobre una
base aislada, sustituyendo solamente la frontera Firebase/OAuth. La prueba con una
cuenta Google personal corresponde a su titular.

```powershell
rtk proxy .venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
rtk proxy .venv/Scripts/python.exe scripts/probar_google_mysql_local.py
rtk proxy .venv/Scripts/python.exe scripts/check_firebase_login.py
rtk proxy .venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

El ensayo MariaDB crea y usa un esquema QA independiente, y lo elimina solo cuando
las pruebas pasan. Nunca ejecuta las pruebas contra la base de datos del punto de venta.

## Resultado verificado

- Respaldo restaurado: 28/28 tablas, 346 registros y esquemas coincidentes.
- Migración aplicada: `identity.0002_googlevinculomodel`. Se conservaron las 28 tablas
  originales y sus registros; únicamente se añadieron la tabla de vínculos y los
  metadatos de Django esperados. No se vincularon usuarios automáticamente.
- Suite completa: **1836 aprobadas, 13 omitidas, 0 fallos**. Evidencia:
  `reports/google-registro-completo.xml`.
- MariaDB/InnoDB aislado: **52 aprobadas**, incluyendo concurrencia y rollback.
  Evidencia: `reports/google-registro-mysql.xml`. Estas pruebas repiten casos de
  la suite general: no deben sumarse como 52 casos únicos adicionales.
- La suite general omite 8 casos MySQL/InnoDB de otros módulos, 1 Redis, 3 k6 y
  el caso de concurrencia Google; este último sí pasó en el ensayo MariaDB aparte.
- Chromium completó alta y vinculación contra Django real en una base de pruebas;
  se controló solamente la frontera Firebase/OAuth.
- Ruff, Django check y comprobación de migraciones pendientes: correctos.
- 54/54 plantillas y 17/17 archivos JavaScript compilados.
- Consulta remota real: cuenta de servicio correcta, ambos dominios locales
  autorizados y módulos SDK 13.2.0 con HTTP 200.
- Servidor reiniciado con acceso a la red: HTTP 200 y selector real de Google abierto
  en `accounts.google.com`, sin mensajes de error. No se introdujeron credenciales
  personales ni se crearon clientes de demostración en la base original.
