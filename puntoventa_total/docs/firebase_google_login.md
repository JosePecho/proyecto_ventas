# Acceso con Google

La rama `feature/firebase-google-login` parte del commit recuperable `ec0889e`.
No hay migraciones. Los usuarios y permisos permanecen en la base local.

## Archivos de la integración

Modificados:

- `.env` local, ignorado por Git: ruta de la cuenta de servicio y proyecto.
- `.env.example` y `.env.development.example`: variables de ejemplo.
- `config/settings/base.py`: configuración Firebase.
- `requirements/base.txt`: dependencia Admin SDK.
- `templates/identity/login.html`: botón y carga del módulo JS.
- `src/modules/identity/domain/repositories/usuario_repository.py`: búsqueda inequívoca.
- `src/modules/identity/infrastructure/persistence/repositories/django_usuario_repository.py`: consulta por correo único.
- `src/modules/identity/presentation/urls.py`: endpoint Google.
- `src/modules/identity/presentation/views/login_view.py`: reutilización de sesión y configuración pública.

Nuevos:

- `src/modules/identity/application/ports/google_identity_port.py`.
- `src/modules/identity/application/use_cases/autenticar_google.py`.
- `src/modules/identity/infrastructure/security/firebase_google_adapter.py`.
- `src/modules/identity/presentation/views/google_login_view.py`.
- `src/modules/identity/presentation/views/session_login.py`.
- `static/js/identity/google_login.js`.
- `scripts/check_firebase_login.py`.
- `tests/unit/test_firebase_google_adapter.py`.
- `tests/integration/test_google_login.py`.
- `tests/system/test_google_login_playwright.py`.
- Este documento.

No se modificaron módulos de ventas, catálogo/productos, inventario, clientes,
pedidos ni reportes. La utilidad de sesión conserva la consulta al perfil de cliente
que ya realizaba el login anterior.

## Configuración

Instalar `requirements/base.txt` en el entorno de destino sin cambiar la versión de
Django del entorno actual solo por esta integración. La dependencia nueva es
`firebase-admin==7.7.0`.

Guardar la cuenta de servicio de `puntoventa-a7f93` fuera del repositorio y de
carpetas sincronizadas. En `.env` (ignorado por Git):

```dotenv
GOOGLE_APPLICATION_CREDENTIALS=C:/Users/mallq/.firebase/puntoventa-a7f93-admin.json
FIREBASE_PROJECT_ID=puntoventa-a7f93
FIREBASE_GOOGLE_ENABLED=True
```

La configuración web es pública; ninguna clave privada se envía al navegador.
No usar `FIREBASE_AUTH_EMULATOR_HOST`: el adaptador rechaza el emulador.
El login tradicional funciona también con `FIREBASE_GOOGLE_ENABLED=False`.

En Firebase Console, Authentication → Sign-in method, habilitar Google y configurar
el correo de soporte. En Authentication → Settings → Authorized domains, agregar
`localhost` y `127.0.0.1` sin esquema ni puerto. En producción usar HTTPS y autorizar
el dominio real. No hace falta activar Analytics.

La comprobación remota realizada encontró `localhost` autorizado y `127.0.0.1`
ausente. Es necesario agregar este último para acceder desde la URL solicitada.

## Política de autorización

`POST /login/google/` recibe JSON `{"id_token": "...", "next": "/catalogo/"}`
y exige CSRF. Devuelve 200 con `redirect`, 400 para entradas inválidas, 403 para
identidades no autorizadas, 409 si ya hay sesión o 503 si Firebase no está disponible.
Las redirecciones solo permiten destinos locales seguros.
La página de login usa `Cross-Origin-Opener-Policy: same-origin-allow-popups`
para permitir la comunicación con la ventana OAuth; las demás páginas conservan
su política existente. Las respuestas de autenticación no se almacenan en caché.

El Admin SDK verifica el ID token y su revocación. Se exige proveedor `google.com`,
correo verificado y Gmail. Otros correos, incluido Workspace, requieren una futura
vinculación explícita desde una sesión tradicional; no se confía en un supuesto
claim `hd` dentro del token Firebase. No se asocian cuentas de terceros solo por
coincidencia del correo.

Debe existir exactamente un usuario local con ese correo (sin distinguir mayúsculas),
activo y no bloqueado. No se crean usuarios de negocio ni perfiles de cliente.
Se conserva el rol local y las claves de sesión anteriores. La creación del usuario
técnico Django para Google no concede `is_staff` ni `is_superuser`.

Firebase puede crear un registro en su propia lista Authentication → Users al
completar Google OAuth, incluso si Django rechaza el acceso. Ese registro remoto
no autoriza el acceso al punto de venta.

Se usa persistencia Firebase en memoria y `signOut` después del intercambio.
La sesión restante es Django y se cierra mediante el POST con CSRF existente.
Desactivar el usuario o cambiar su rol mantiene la invalidación de sesión existente.

## Prueba manual

1. Autorizar `127.0.0.1` en Firebase y reiniciar Django para cargar `.env`.
2. Abrir `http://127.0.0.1:8000/` sin una sesión previa.
3. Comprobar primero usuario/email y contraseña, y cerrar sesión.
4. Pulsar **Continuar con Google** y elegir una cuenta Gmail ya registrada y activa
   en el sistema. Verificar que solo aparezcan las funciones de su rol.
5. Cerrar sesión y repetir con una cuenta desconocida: debe rechazarse.
6. Cancelar el selector y comprobar que el formulario tradicional sigue disponible.

No compartir tokens, el JSON de servicio ni su contenido. La prueba interactiva de
una cuenta real debe realizarla su titular; las pruebas automatizadas no acreditan
que una persona haya completado ese selector.

Comprobaciones:

```powershell
rtk proxy .venv/Scripts/python.exe scripts/check_firebase_login.py
rtk proxy .venv/Scripts/python.exe -m pytest tests/integration/test_google_login.py tests/unit/test_firebase_google_adapter.py tests/system/test_google_login_playwright.py -q -p no:cacheprovider
```

## Resultados de validación

- Suite completa: **1783 aprobadas, 12 omitidas, 0 fallos**.
  Evidencia local: `reports/firebase-google-pruebas.xml`.
- Las omisiones son 8 pruebas MySQL/InnoDB, 1 Redis y 3 k6; no acreditan ejecución
  de esa infraestructura.
- Las 40 pruebas específicas cubren tokens rechazados, revocación solicitada,
  proveedor y correo, usuarios desconocidos/duplicados/inactivos/bloqueados,
  todos los roles, perfil de cliente, CSRF, logout, redirecciones y login tradicional.
- Cuatro escenarios Chromium: éxito, rechazo, cancelación y SDK inaccesible.
  Usan una frontera OAuth controlada, no cuentas Google personales.
- Ruff completo y `manage.py check --settings=config.settings.testing`: correctos.
- 53/53 plantillas y 17/17 archivos JavaScript compilados.
- Comprobación remota real: cuenta de servicio autenticada, proyecto coincidente,
  consulta de dominios exitosa y módulos Firebase App/Auth 13.2.0 con HTTP 200.
- Chromium con SDK real: botón habilitado en la web local. Captura en
  `reports/login-google-real.png`; no se inició sesión con una cuenta personal.
- Servidor local reiniciado: HTTP 200, botón presente y política de popup correcta.
