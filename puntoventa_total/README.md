# PuntoVenta Total

Sistema integral de punto de venta, inventario, pedidos web, caja, promociones y reportes.

Arquitectura: **monolito modular con Clean Architecture** por modulo (identidad, catalogo, inventario,
ventas, caja, pedidos, clientes, promociones, reportes, auditoria).

## Requisitos

- Python 3.11+
- MySQL 8
- Redis
- (Opcional) Docker + Docker Compose

## Instalacion local

    cd puntoventa_total
    python -m venv .venv
    .venv\Scripts\activate        (Linux/macOS: source .venv/bin/activate)
    pip install -r requirements/development.txt
    cp .env.example .env          # ajustar valores
    python manage.py migrate
    python scripts/crear_admin.py
    python manage.py runserver

## Instalacion con Docker

    docker compose up --build

## Estructura

    config/            Configuracion multi-entorno (base/development/production/testing)
    src/shared/        Capa transversal (dominio base, uow, cache, logging, seguridad)
    src/modules/       Modulos del negocio: domain / application / infrastructure / presentation
    templates/         Plantillas Django por modulo
    static/            CSS/JS (cola offline, IndexedDB, service worker)
    tests/             unit / integration / functional / e2e / performance
    scripts/           Semilla de datos, admin, backups, health checks
    deployment/        nginx, gunicorn, celery, init MySQL
    monitoring/        Prometheus y alertas
    docs/              Arquitectura, BD, requisitos, API, despliegue, testing

## Tests

    pytest -m unit
    pytest -m integration
    pytest --cov=src

