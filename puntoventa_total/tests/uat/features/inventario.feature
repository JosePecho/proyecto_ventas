Feature: Inventario de la tienda RF-016 a RF-024
  Como almacenero quiero controlar entradas y mermas con trazabilidad.

  Background:
    Given un almacenero autenticado con un producto y minimo de 5 unidades

  Scenario: Recepcion de mercaderia con lote
    When registra una recepcion de 10 unidades con lote "UAT-INGRESO"
    Then el stock fisico es de 10 unidades
    And el kardex contiene una entrada de 10 unidades

  Scenario: Merma por dano justificada
    Given una recepcion previa de 10 unidades
    When registra una merma de 3 unidades por "DANADO"
    Then el stock fisico es de 7 unidades
    And el kardex conserva el motivo "MERMA:DANADO"

  Scenario: Una merma excesiva se rechaza sin perdida de datos
    Given una recepcion previa de 10 unidades
    When registra una merma de 11 unidades por "ROBO"
    Then la operacion muestra un error de validacion
    And el stock fisico es de 10 unidades
    And no hay movimientos de merma

  Scenario: Se notifica al caer debajo del minimo
    Given una recepcion previa de 6 unidades
    When registra una merma de 2 unidades por "DANADO"
    Then el stock fisico es de 4 unidades
    And recibe una notificacion de stock minimo

  Scenario: La alerta incluye 30 dias y excluye 31 dias
    Given un lote que vence en 30 dias y otro en 31 dias
    When consulta las alertas de inventario
    Then ve solo el lote que vence en 30 dias

  Scenario: Productos sin ventas aparecen en baja rotacion y ranking
    Given otro producto con margen mayor y sin ventas
    When consulta los reportes de inventario
    Then ambos productos aparecen en baja rotacion
    And el producto con mayor margen encabeza el ranking
