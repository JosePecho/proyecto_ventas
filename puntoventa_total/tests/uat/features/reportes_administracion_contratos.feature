Feature: Criterios de aceptación de reportes y usuarios RF-045 RF-046 RF-048
  Scenario: Separar ranking por volumen y por importe
    Given un administrador con cinco unidades de diez soles y una de treinta soles
    When consulta el ranking por cantidad y por monto
    Then el orden cambia y las ventas anuladas no cuentan

  Scenario: Rechazar un rango de fechas invertido
    Given un administrador de reportes autenticado
    When pide ventas desde el veinte hasta el diecinueve de octubre
    Then recibe un error de validación sin generar un reporte engañoso

  Scenario: Conservar al último administrador
    Given un único administrador activo
    When intenta desactivar su propia cuenta
    Then conserva su rol y el acceso a la gestión de usuarios
