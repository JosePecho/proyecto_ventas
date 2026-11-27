# Reportes y administración RF-044 a RF-050

| RF | Contrato de aceptación |
|---|---|
| RF-044 | Dashboard del día local: suma y cantidad de ventas PAGADA, con desglose por método de pago. Excluye ayer, borradores y anuladas. |
| RF-045 | Fechas inclusivas en America/Lima. Rangos invertidos, fechas inválidas o más de 366 días retornan 400. |
| RF-046 | Ranking por `orden=cantidad` o `orden=monto`, excluyendo anuladas. |
| RF-047 | Ingresos netos, costos históricos y utilidad por producto y total. Margen sobre ventas = utilidad / ingresos × 100, con dos decimales. No es recargo sobre costo. |
| RF-048 | ADMINISTRADOR crea, edita y desactiva usuarios; conserva al último administrador y revoca sesiones al cambiar rol o desactivar. |
| RF-049 | Creación/edición de categorías con permisos y registro de auditoría atómico. |
| RF-050 | Consulta de actor, acción, entidad y fecha, exclusivamente ADMINISTRADOR; filtros malformados retornan 400 y no errores 500. |

Cambios del contrato de salida de RF-047: cada fila de utilidad agrega
`margen_pct`, calculado con Decimal y ROUND_HALF_UP. Si faltan costos históricos
o los ingresos son cero, el margen del producto es `None` y la pantalla muestra
«No disponible». El indicador `estimado` y el aviso de utilidad parcial se conservan.
El total sin ventas mantiene los importes y porcentaje en cero.

La auditoría acepta las acciones transversales CREAR, ACTUALIZAR y ELIMINAR,
además de las acciones específicas de negocio ya existentes. No se aceptan
acciones arbitrarias. `GET /auditoria/` admite filtros opcionales `accion`,
`entidad`, `entidad_id`, `usuario_id` UUID, `desde`, `hasta` y `pagina` entero
positivo. La ausencia de página equivale a 1. Las fechas de auditoría deben estar
ordenadas; no se aplica el límite anual de los reportes a esta consulta.

Reportes permiten ADMINISTRADOR y GERENTE según la política existente. Usuarios
y auditoría exigen ADMINISTRADOR. Las mutaciones HTML usan sesión y CSRF.

Límites existentes: consulta de auditoría truncada a 100 eventos; informes cargan
en memoria las líneas del rango; los importes de salida usan float. Los porcentajes
de históricos incompletos son parciales y no acreditan rentabilidad contable.
