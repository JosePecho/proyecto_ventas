# Acta de aceptación del módulo Inventario

Estado: pendiente de revisión y aprobación por el responsable de negocio.
La ejecución automatizada no sustituye esta aprobación.

| Requisito | Validación para el responsable | Resultado / observaciones |
|---|---|---|
| RF-016 | Crear y editar producto con código, categoría, precio, costo, mínimo y vencimiento | Pendiente |
| RF-017 | Cobrar una venta y comprobar la reducción exacta de stock; repetir el cobro sin duplicar la salida | Pendiente |
| RF-018 | Pasar de mínimo a menor que mínimo y comprobar la notificación | Pendiente |
| RF-019 | Verificar inclusión de vencimientos entre hoy y 30 días; exclusión del día 31 | Pendiente |
| RF-020 | Recibir un lote y comprobar cantidad y vencimiento | Pendiente |
| RF-021 | Registrar merma por vencimiento, daño o robo y rechazar cantidades mayores que el disponible | Pendiente |
| RF-022 | Consultar entradas, salidas y ajustes del producto en el kardex | Pendiente |
| RF-023 | Verificar productos sin ventas pagadas en los últimos 60 días | Pendiente |
| RF-024 | Revisar el orden por margen y confirmar la fórmula de negocio | Pendiente |

Ejecución automatizada reproducible desde `puntoventa_total`:

```powershell
.venv/Scripts/python.exe -m pytest tests/uat/test_inventario_bdd.py -q -p no:cacheprovider
```

Consultar `inventory_master_plan.md` y los reportes de pruebas para la evidencia
técnica y las validaciones de infraestructura aún pendientes.

Responsable: ____________________

Fecha y versión/commit revisado: ____________________

Decisión (aprobado / rechazado): ____________________

Observaciones e incidencias: ____________________
