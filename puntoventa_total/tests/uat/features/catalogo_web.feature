Feature: Catalogo publico actualizado
  El cliente consulta productos sin iniciar sesion.

  Scenario: Consultar precio y disponibilidad
    Given un catalogo con agua en Bebidas y galletas en Snacks
    When consulta el catalogo publico
    Then ve Agua mineral con precio y 5 unidades disponibles

  Scenario: Combinar categoria y busqueda por nombre
    Given un catalogo con agua en Bebidas y galletas en Snacks
    When filtra Bebidas y busca mineral
    Then solo aparece Agua mineral

  Scenario: Consultar el detalle del producto
    Given un catalogo con agua en Bebidas y galletas en Snacks
    When abre el detalle de Agua mineral
    Then ve descripcion precio imagen y stock del producto

  Scenario: Mantener visible un producto agotado
    Given un catalogo con agua en Bebidas y galletas en Snacks
    And se vende toda el agua disponible
    When consulta el catalogo publico
    Then Agua mineral aparece como Agotado
