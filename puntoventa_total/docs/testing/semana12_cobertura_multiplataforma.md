# Laboratorio Semana 12: pruebas unitarias y cobertura

**Unidad didáctica:** Pruebas Unitarias y Análisis de Datos  
**Docente:** Ing. Percy Acha Taipe  
**Indicador C7.I2:** Desarrolla el plan de pruebas unitarias y análisis de datos, de acuerdo al proceso de implantación.  
**Sesión 12:** Criterios de cobertura y pruebas de caja negra con IA

## 1. Objetivos y conceptos

Al finalizar, el equipo podrá diseñar pruebas desde requisitos, ejecutar pruebas unitarias, interpretar cobertura y documentar límites de medición. La cobertura sirve para identificar código no ejecutado; por sí sola no demuestra que las pruebas sean correctas ni que el producto esté libre de defectos.

- **Sentencias/líneas:** proporción de líneas ejecutables ejecutadas.
- **Ramas:** proporción de destinos de decisión recorridos (por ejemplo, verdadero y falso).
- **Condiciones:** evaluación verdadera y falsa de cada condición booleana independiente. No todas las herramientas miden esta métrica; branch coverage no equivale a condition coverage.

Un porcentaje de 100% solo describe el alcance seleccionado, los archivos incluidos y las métricas reportadas por la herramienta. Las excepciones deben probarse cuando formen parte del comportamiento esperado.

## 2. Diseño de caja negra

Antes de mirar la implementación, derive escenarios de los requisitos con particiones de equivalencia y valores límite. Incluya entradas válidas, inválidas, fronteras, ausentes y tipos inesperados cuando el contrato lo permita. Registre entrada, resultado esperado y requisito asociado; después contraste con las ramas del código.

### Ejemplo Python

```python
def calcular_precio_final(monto: float, cupon: str, es_afiliado: bool) -> float:
    if monto <= 0:
        raise ValueError("El monto debe ser mayor a cero")

    descuento = 0.0
    if cupon == "SARASARA20" and monto >= 100:
        descuento = 0.20
    elif es_afiliado:
        descuento = 0.10

    return round(monto * (1 - descuento), 2)
```

Casos representativos: monto cero (excepción), cupón correcto con monto 100 (20%), afiliado sin cupón elegible (10%), cliente regular (sin descuento), cupón correcto con monto inferior a 100 (evalúa el límite falso y permite probar el `elif`). La última condición compuesta debe tener casos que permitan evaluar ambas salidas de sus operandos; considere el cortocircuito de `and`.

```python
import pytest

from descuentos import calcular_precio_final


def test_monto_cero_es_invalido():
    with pytest.raises(ValueError, match="mayor a cero"):
        calcular_precio_final(0, "SARASARA20", False)


def test_aplica_cupon_en_limite():
    assert calcular_precio_final(100, "SARASARA20", False) == 80


def test_afiliado_recibe_descuento():
    assert calcular_precio_final(80, "NINGUNO", True) == 72


def test_cliente_regular_no_recibe_descuento():
    assert calcular_precio_final(50, "NINGUNO", False) == 50


def test_cupon_no_aplica_bajo_el_limite():
    assert calcular_precio_final(99.99, "SARASARA20", False) == 99.99
```

Ejecución desde el directorio del proyecto:

```powershell
rtk proxy .venv\Scripts\python.exe -m pytest tests\unit -q
rtk proxy .venv\Scripts\python.exe -m pytest tests\unit --cov=src --cov-branch --cov-report=term-missing --cov-report=html:htmlcov
```

El proyecto ya configura `pytest-cov`/coverage.py en `pyproject.toml`, mide `src`, omite migraciones, modelos y archivos indicados, e impone un umbral global de 80%. El informe HTML queda en `htmlcov\index.html`. Para medir un módulo concreto se puede usar `--cov=paquete.modulo`; verificar siempre qué archivos fueron incluidos.

## 3. React / Node / TypeScript

En proyectos Vite, instale Vitest y el proveedor de cobertura que use el repositorio (`@vitest/coverage-v8` o el proveedor configurado). Añada pruebas a las funciones de negocio y ejecute:

```sh
npx vitest run --coverage
```

Para Jest:

```sh
npx jest --coverage --collectCoverageFrom="src/**/*.{js,jsx,ts,tsx}"
```

El colector y la ruta HTML dependen de la configuración; normalmente se genera bajo `coverage/`. Verifique métricas de líneas, ramas y funciones. En un validador de stock cubra cantidad inválida, reserva activa e inactiva, stock insuficiente y pedido exactamente igual al stock disponible.

## 4. Laravel / PHP

PHPUnit/Pest necesita Xdebug en modo coverage o PCOV disponible en el PHP que ejecuta las pruebas. Confirme con `php --ri xdebug` o `php -m` y use la versión del framework instalada:

```sh
php artisan test --testsuite=Unit --coverage
```

Para exigir un mínimo, use la opción soportada por la versión instalada (`--min=100` cuando esté disponible). El reporte HTML se configura mediante PHPUnit/Pest y requiere un formato de cobertura compatible; no asuma una ruta fija.

## 5. Java / Spring Boot

Configure JaCoCo en Maven o Gradle, junto con JUnit 5. Una configuración Maven habitual enlaza `prepare-agent` y `report`:

```sh
mvn clean test jacoco:report
```

El HTML Maven se genera normalmente en `target/site/jacoco/index.html`. Consulte la tabla de JaCoCo para sentencias y ramas; la cobertura de condiciones individuales no es una métrica equivalente disponible en todas las herramientas.

## 6. Comparación rápida

| Plataforma | Pruebas / cobertura | Comando habitual | Informe habitual |
|---|---|---|---|
| Python | Pytest / pytest-cov | `python -m pytest --cov=src --cov-branch` | `htmlcov/index.html` |
| React con Vite | Vitest / proveedor configurado | `npx vitest run --coverage` | `coverage/index.html` |
| Node / React | Jest / Istanbul | `npx jest --coverage` | `coverage/lcov-report/index.html` |
| Laravel | PHPUnit o Pest / Xdebug o PCOV | `php artisan test --testsuite=Unit --coverage` | Configurable |
| Java | JUnit 5 / JaCoCo | `mvn clean test jacoco:report` | `target/site/jacoco/index.html` |

## 7. Prompts de apoyo con IA

**Diseño de caja negra:**

> Actúa como especialista QA. A partir del siguiente requisito, sin asumir detalles de implementación, construye una matriz con particiones válidas e inválidas, valores límite, entradas ausentes o inesperadas según el contrato, resultado esperado y requisito asociado. No escribas código todavía.
>
> Requisito: [pegar historia o regla de negocio]

**Revisión de brechas de cobertura:**

> Revisa el código y las pruebas adjuntas. Para cada línea o rama sin cubrir, explica qué comportamiento representa y propone casos de prueba adicionales con entradas y resultados esperados. Distingue cobertura de líneas, ramas y condiciones; no declares 100% sin evidencia del informe y señala cuando el comportamiento no esté definido por los requisitos.
>
> Código: [pegar]  Pruebas: [pegar]  Informe: [pegar]

El equipo debe revisar las sugerencias contra los requisitos y descartar casos que no correspondan al contrato.

## 8. Lista de cotejo y evidencia

- [ ] Entorno y herramienta de cobertura configurados.
- [ ] Matriz de caja negra asociada a requisitos, equivalencias y límites.
- [ ] Sugerencias de IA contrastadas y validadas por el equipo.
- [ ] Informe registra cobertura de líneas/sentencias y ramas del alcance indicado.
- [ ] Condiciones booleanas relevantes y excepciones esperadas analizadas, indicando límites de la herramienta.
- [ ] Reporte HTML archivado y acompañado de interpretación honesta.

En la evidencia se debe anotar comando, versión de herramientas, suite ejecutada, archivos incluidos/excluidos, resultado de pruebas, métricas y umbral. No describir la cobertura de un componente como cobertura del sistema completo.
