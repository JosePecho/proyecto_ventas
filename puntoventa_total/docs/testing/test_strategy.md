# Estrategia de pruebas

## Piramide

| Nivel | Directoria | Marker | Base de datos | Objetivo |
|---|---|---|---|---|
| Unit | `tests/unit/domain` | `unit` | no | Invariantes de negocio |
| Unit | `tests/unit/application` | `unit` | no | Casos de uso con fakes |
| Integration | `tests/integration` | `integration` | si | Repositorios y transacciones |
| Functional | `tests/functional` | `functional` | si | Vistas y flujos HTTP |
| E2E | `tests/e2e` | `e2e` | si | Flujos completos de negocio |
| Performance | `tests/performance` | `performance` | opcional | Presupuestos de tiempo |

## Ejecucion

    pytest -m unit                  # rapidas, sin BD
    pytest -m integration           # con BD de prueba (sqlite en testing)
    pytest -m "functional or e2e"
    pytest --cov=src --cov-report=html

## Convenciones

1. Las pruebas de dominio construyen entidades directamente (sin mocks de ORM).
2. Los casos de uso se prueban con repositorios `MagicMock` y verificando interacciones
   (ej. "el cobro descuenta stock solo si se paga completo").
3. Las integraciones usan los repositorios reales sobre `config.settings.testing`.
4. Los e2e validan el contrato HTTP que usan templates y la cola offline.
5. Presupuestos de rendimiento: busqueda < 200ms, cobro < 100ms en aislamiento.

## Datos de prueba

- `tests/factories/*` (factory-boy) para entidades de dominio.
- `tests/conftest.py` para fixtures compartidas (`producto_faker`, `monto_base`, ...).

## Cobertura minima esperada

- `domain` + `application`: >= 85%
- `infrastructure` + `presentation`: >= 50% (se cubren via e2e)
