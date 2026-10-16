# Clean Architecture por modulo

Cada modulo de `src/modules/` aplica Clean Architecture de forma aislada:

```
domain/            Reglas de negocio puras (sin Django, sin SQL, sin HTTP)
  entities/        Agregados y entidades con invariantes
  value_objects/   Montos, DNI, codigos de barras (inmutables y validados)
  aggregates/      Coordinan varias entidades bajo una unica invariante
  enums/           Vocabulario del negocio
  events/          Hechos del dominio (VentaPagada, StockMinimoAlcanzado...)
  repositories/    Interfaces (ABC) - el dominio define el contrato
  services/        Politicas y calculos sin estado (PEPS, arqueo, permisos)
  exceptions/      Errores imputables al usuario, nunca excepciones de framework

application/       Orquestacion (casos de uso) - no conoce Django
  use_cases/       Un archivo = una accion de negocio
  dto/             Contratos de entrada/salida inmunes a cambios internos
  ports/           Interfaces hacia otros modulos o servicios externos
  commands/queries Modelos de datos para CQRS liviano

infrastructure/    Adaptadores concretos (SI conoce Django y el dominio)
  persistence/     Modelos ORM + mappers + repositorios concretos
  adapters/        Implementaciones de los ports (capa anticorrupcion)
  tasks/           Tareas Celery
  factories.py     Composition root local del modulo

presentation/      Capa web (SI conoce application, nunca domain directamente)
  views/           Vistas delgadas: validan HTTP y delegan al caso de uso
  forms/           Formularios Django
  permissions/     Decoradores de acceso
  urls.py          Rutas del modulo
```

## Regla de dependencia

La flecha de dependencia siempre apunta hacia adentro:

```
presentation -> application -> domain <- infrastructure
```

- `domain` no importa nada de Django ni de otros modulos.
- `application` importa `domain` y define ports para lo externo.
- `infrastructure` implementa los ports y puede importar `domain`.
- `presentation` solo invoca casos de uso y DTOs.

## Ejemplo de flujo (cobro en el POS)

1. `pago_view` recibe el POST y arma un `ProcesarPagoDTO`.
2. `ProcesarPago` abre transaccion, valida el agregado `VentaAggregate`.
3. El caso de uso llama al port `InventarioPort` (no a inventory directamente).
4. `InventarioAdapter` traduce la llamada a `DescontarStock` (modulo inventory).
5. Se publica `VentaPagada` y `AuditoriaPort.registrar(...)` deja la traza.
6. El repositorio `VentaRepository` persiste el agregado completo.

