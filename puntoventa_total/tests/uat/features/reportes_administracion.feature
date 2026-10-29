Feature: Reportes y administración RF-044 a RF-050
  Scenario: Consultar utilidad y margen histórico por producto
    Given un administrador con una venta de diez soles y costo histórico de seis
    When consulta el reporte de utilidad
    Then ve cuatro soles de utilidad y cuarenta por ciento de margen por producto y total

  Scenario: Rastrear creación y edición de una categoría
    Given un administrador que crea y edita una categoría
    When consulta la auditoría de esa categoría
    Then identifica ambas acciones con su actor y fecha

  Scenario: Revocar el acceso de un usuario desactivado
    Given un administrador y un cajero con sesión iniciada
    When el administrador desactiva al cajero
    Then la cuenta queda inactiva y su sesión pierde el acceso
