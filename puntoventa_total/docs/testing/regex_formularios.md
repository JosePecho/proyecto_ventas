# Formatos de los formularios

En regex101 selecciona Python, sin las opciones multiline ni ignorecase.
Estos patrones verifican la cadena completa; los campos opcionales también aceptan vacío en Django.

| Campo | Expresión Python | Válido | Inválido |
| --- | --- | --- | --- |
| DNI | `\A[0-9]{8}\Z` | `12345678` | `1234567a` |
| Teléfono | `\A\+?[0-9]{7,15}\Z` | `+51987654321` | `987ABC321` |
| Código de barras | `\A(?:[0-9]{8}|[0-9]{12,14})\Z` | `7751234567890` | `ABC12345` |
| Usuario al crear cuenta | `\A[\w.]{4,30}\Z` | `maria.ventas` | `ab` |

Los patrones de teléfono y DNI se aplican también al perfil y al pedido.
El navegador recibe `pattern`, longitud máxima y teclado sugerido para estos formatos.
El servidor vuelve a comprobarlos aunque se omita la validación del navegador.

Todos los formularios Django de los módulos heredan `ValidatedForm`, incluidos los filtros.
Los textos conservan tildes, apóstrofos y alfabetos internacionales; se rechazan caracteres
de control, y se conservan las longitudes máximas de cada campo.
Las contraseñas conservan los espacios introducidos; su seguridad y confirmación siguen
las reglas existentes de Django. El acceso admite usuario o correo sin imponer el patrón de alta.

Correo, números, decimales, fechas, UUID, imágenes y opciones se validan con sus tipos Django.
Las reglas existentes de stock, permisos, duplicados, importes relacionados y vigencias se
comprueban en formularios y servicios. Una expresión regular no demuestra esas reglas.
Esta revisión cubre las clases de formulario; los endpoints que reciben JSON y los campos
HTML escritos manualmente requieren su propia validación y no quedan cubiertos por herencia.
