Feature: Clientes frecuentes, promociones y administración RF-038 a RF-050
  Scenario: Calcular beneficio automático al asociar una cliente recurrente
    Given un carrito de dos soles para una cliente recurrente con fidelización vigente
    When el cajero asocia el DNI de esa cliente a la venta
    Then el importe a cobrar baja automáticamente a un sol con ochenta céntimos

  Scenario: Registrar al cliente frecuente en caja
    Given un cajero autenticado
    When registra el DNI y teléfono del cliente
    Then el cliente frecuente queda registrado sin pertenecer al cajero

  Scenario: Consultar historial propio
    Given una cliente con dos compras pagadas y una anulada
    When consulta su historial web
    Then ve dos compras por un total de treinta soles

  Scenario: Aplicar una promoción 2x1
    Given un administrador con un producto de dos soles
    When crea y activa una promoción 2x1
    Then dos unidades reciben dos soles de descuento

  Scenario: Vencer una promoción cuyo periodo terminó
    Given una promoción programada cuyo periodo ya terminó
    When se actualiza la vigencia de promociones
    Then queda Vencida y no aparece entre las promociones públicas

  Scenario: Cancelar una promoción vencida conforme al ciclo de vida
    Given un administrador con una promoción Vencida
    When cancela la promoción vencida
    Then queda Cancelada y no ofrece descuentos públicos

  Scenario: Reportar solo ventas pagadas
    Given un administrador y ventas pagadas y anuladas
    When consulta el reporte de ventas
    Then ve una transacción pagada y su método de pago

  Scenario: Auditar cambios de categorías
    Given un administrador autenticado
    When crea una categoría de productos
    Then la auditoría identifica al administrador y la categoría creada

  Scenario: Proteger la administración
    Given un cajero autenticado
    When intenta crear una promoción
    Then el sistema deniega la operación y no crea promociones
