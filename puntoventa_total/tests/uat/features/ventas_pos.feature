Feature: Cobro y anulacion en el punto de venta
  Como cajero del local
  Quiero cobrar ventas con efectivo, aplicar descuentos autorizados y anular tickets
  Para que el ticket, el vuelto y el stock siempre reflejen la venta real

  Rule: RN-08 - El vuelto nunca puede ser negativo
  Rule: RN-06 - Una venta no se cierra sin pago total ni se anula dos veces
  Rule: RN-07 - El descuento total no puede superar 50%

  Scenario: Cobro completo en efectivo genera el vuelto correcto
    Given una venta en borrador con 1 "Pan" a "10.00"
    And la caja registra un pago de "10.00" con "20.00" entregados en efectivo
    When el cajero cierra la venta
    Then la venta queda "PAGADA"
    And el vuelto del cajero es "10.00"

  Scenario: Un pago parcial no puede cerrar la venta
    Given una venta en borrador con 1 "Pan" a "10.00"
    And la caja registra un pago de "4.00" con "4.00" entregados en efectivo
    When el cajero intenta cerrar la venta
    Then el cierre se rechaza por saldo pendiente
    And la venta sigue en estado "BORRADOR"

  Scenario: El gerente no puede aplicar un descuento mayor al 50%
    Given una venta en borrador con 1 "Camiseta" a "20.00"
    When el gerente aplica un descuento del "60" por ciento a la venta
    Then el descuento se rechaza con el tope de 50 por ciento
    And la venta sigue en estado "BORRADOR"

  Scenario: Aplicar exactamente el tope de descuento del 50% si es posible
    Given una venta en borrador con 1 "Camiseta" a "20.00"
    When el gerente aplica un descuento del "50" por ciento a la venta
    Then el total de la venta queda en "10.00"
    And la venta sigue en estado "BORRADOR"

  Scenario: Anular una venta pagada devuelve stock y solo puede hacerse una vez
    Given una venta pagada con 1 "Pan" a "10.00"
    When el gerente anula la venta con motivo "cliente se equivoco"
    Then la venta queda "ANULADA"
    And el inventario recibe una devolucion de stock
    When el gerente anula la venta con motivo "segundo intento"
    Then la segunda anulacion se rechaza
    And el inventario no recibe una segunda devolucion
