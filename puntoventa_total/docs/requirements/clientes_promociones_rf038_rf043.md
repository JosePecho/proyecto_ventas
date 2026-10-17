# Clientes frecuentes y promociones (RF-038 a RF-043)

El módulo utiliza los componentes `customers`, `promotions` y su integración con
`sales`. Esta matriz describe el comportamiento implementado y sus pruebas.

| Requisito | Comportamiento | Evidencia automatizada |
|---|---|---|
| RF-038 | El cajero registra nombre, DNI de ocho dígitos y teléfono obligatorio de 7 a 15 dígitos, con prefijo `+` opcional. El registro no queda asociado a la cuenta del cajero. | `test_rf038_cajero_registra_dni_telefono_sin_asociarse_como_dueno`, `test_rf038_telefono_invalido_no_produce_500` |
| RF-039 | Se consultan las ventas PAGADAS del cliente para calcular cantidad de compras, monto acumulado e intervalo promedio. Las ventas anuladas quedan excluidas. | `test_rf039_y_rf043_historial_propio_suma_solo_pagadas` |
| RF-040 | Al asociar el cliente a la venta, el POS calcula el beneficio de fidelización y lo conserva al cobrar. Requiere una promoción de fidelización activa y vigente. | `test_rf040_descuento_automatico_se_persiste_y_cobra_con_stock_real`, `tests/unit/application/test_beneficios_venta.py` |
| RF-041 | El administrador crea y edita promociones porcentuales, NX1 (2x1 por defecto) y combos de productos existentes y activos. | `test_rf041_admin_crea_tipos_reales_y_edita`, `test_rf041_042_entrada_invalida_se_muestra_sin_500` |
| RF-042 | El administrador puede indicar inicio y fin juntos; el fin debe ser posterior al inicio. La vigencia se comprueba al aplicar el beneficio. | `test_rf042_programada_ya_vencida_no_se_activa_temporalmente`, `test_promocion_no_vigente_en_instante_final` |
| RF-043 | El cliente autenticado consulta su propio historial en la web, con fecha, ticket, importe, cantidad acumulada y frecuencia. El historial ajeno devuelve 403. | `test_rf039_y_rf043_historial_propio_suma_solo_pagadas` |

Los nombres de pruebas RF pertenecen a `tests/integration/test_rf038_050.py`;
la prueba del instante final pertenece a
`tests/unit/domain/test_clientes_promociones_reportes.py`.

## Política de fidelización existente

- Menos de dos compras: clasificación `SIN_DATOS`, sin descuento.
- Intervalo promedio de hasta siete días: `FRECUENTE`, descuento del 10 %.
- Intervalo superior a siete días: `OCASIONAL`, descuento del 5 %.
- Dos compras en el mismo instante también califican como frecuentes.
- Los porcentajes actuales son constantes en
  `promotions/application/use_cases/aplicar_descuento_frecuencia.py`.
- La fidelización requiere habilitar `aplica_clientes_frecuentes` en una promoción
  vigente. Crear un cliente por sí solo no activa el beneficio.
- Las promociones pueden crearse sin fechas. Si se programa vigencia, ambas fechas
  son obligatorias y el instante final queda excluido.

Estos umbrales son decisiones de la implementación actual: los requisitos
RF-038 a RF-043 no especifican porcentajes ni umbrales de recurrencia.

## Ciclo de vida de promociones

Se aplica la secuencia suministrada por el usuario: Borrador → Activa → Vencida →
Cancelada. Internamente, Vencida se guarda como FINALIZADA y la programación
horaria utiliza PROGRAMADA. Una promoción vencida admite cancelación, con
auditoría de la acción; una cancelada es terminal. Una promoción vencida o
cancelada no admite reactivación y no vuelve a conceder descuentos.

## Acceso a las pantallas

Se utilizan las rutas Django con nombre `customers:registro`, `customers:perfil`,
`customers:historial`, `promotions:crear` y `promotions:editar`.
Administrador, gerente y cajero pueden consultar historiales; el rol CLIENTE
necesita ser propietario del registro. La creación y edición de promociones
permite los roles ADMINISTRADOR y GERENTE.
