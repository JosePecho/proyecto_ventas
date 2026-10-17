Feature: Pedidos web con recojo en tienda RF-030 a RF-037
  Scenario: Confirmar un pedido con hora de recojo
    Given una cliente web autenticada con dos panes en su carrito
    When confirma el pedido para recojo mañana en una franja válida
    Then el pedido queda Pendiente con dos unidades reservadas

  Scenario: Cancelar mientras está pendiente
    Given una cliente web autenticada con dos panes en su carrito
    When confirma el pedido para recojo mañana en una franja válida
    And solicita cancelar su pedido
    Then el pedido queda Cancelado y el stock queda disponible

  Scenario: La preparación impide cancelar
    Given una cliente web autenticada con dos panes en su carrito
    When confirma el pedido para recojo mañana en una franja válida
    And la tienda inicia la preparación
    And solicita cancelar su pedido
    Then el pedido sigue En preparación y conserva su reserva

  Scenario: Avisar cuando está listo
    Given una cliente web autenticada con dos panes en su carrito
    When confirma el pedido para recojo mañana en una franja válida
    And la tienda inicia la preparación
    And la tienda marca el pedido Listo
    Then la cliente recibe un email con su número de pedido
