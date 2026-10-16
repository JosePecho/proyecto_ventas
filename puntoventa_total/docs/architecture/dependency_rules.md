# Reglas de dependencias

1. `src/shared/**` no importa de `src/modules/**` jamas.
2. `domain` no importa Django, ORM, HTTP ni modulos vecinos.
3. `application` solo importa `domain` y sus propios DTOs/ports.
4. `infrastructure` puede importar `domain` y `application` (para cumplir contratos).
5. `presentation` importa `application` (casos de uso y DTOs). Puede consultar repositorios
   de su propio modulo para paginar o listar, pero nunca ejecuta reglas de negocio.
6. Un modulo solo puede importar otro modulo por su capa `ports`/`adapters` de aplicacion.
7. Los modelos Django viven unicamente en `infrastructure/persistence/django_models/`.
   Los mappers son el unico puente entidad <-> modelo.
8. Toda transaccion que toque mas de un modulo se abre en el caso de uso orquestador
   (ej. `ProcesarPago`, `ConfirmarPedido`, `CerrarTurno`).

## Verificacion

- `ruff` con select `E,F,I,N,W,UP,B,C4` detecta imports circulares basicos.
- Revision en PR: buscar imports que crucen capas (`grep -rn "modules.*models import" src/*/domain`).

