# Repository Guidelines

## Project Structure & Module Organization

The Django application lives in `puntoventa_total/`. Run commands there. It is a modular monolith with Clean Architecture:

- `src/modules/`: sales, inventory, catalog, customers, orders, and other business modules, organized into `domain`, `application`, `infrastructure`, and `presentation` layers.
- `src/shared/`: shared domain types, application interfaces, and infrastructure utilities.
- `config/`: URLs and environment-specific Django settings.
- `templates/` and `static/`: HTML templates, CSS, JavaScript, and images.
- `tests/`: unit, integration, functional, system, E2E, UAT, and performance suites.
- `scripts/`, `docs/`, and `deployment/`: maintenance tools, technical documentation, and deployment configuration.

Keep domain logic independent of Django persistence; connect modules through application ports and infrastructure adapters.

## Build, Test, and Development Commands

Activate the project virtual environment first. Prefix shell commands with `rtk`; use `rtk proxy` for unfiltered execution.

```powershell
rtk proxy python -m pip install -r requirements/development.txt
rtk proxy python manage.py migrate
rtk proxy python manage.py runserver 127.0.0.1:8000
rtk proxy python manage.py check --settings=config.settings.testing
rtk proxy python -m ruff check .
rtk proxy python -m pytest tests/unit -q
rtk proxy python -m pytest --cov=src --cov-branch
rtk proxy python scripts/check_assets.py --javascript
```

These commands install dependencies, apply migrations, start development, check configuration, lint, test, measure coverage, and validate templates/JavaScript. Development requires configured MySQL/MariaDB; default tests use isolated SQLite.

## Coding Style & Naming Conventions

Use four-space indentation, `snake_case` functions/files, and `PascalCase` classes. Preserve established Spanish business names. Target Python 3.11+ and the configured 110-character line length. Ruff checks imports, naming, correctness, and modernization. Use `Monto`/`Decimal` for monetary calculations.

## Testing Guidelines

Name files `test_*.py` and functions `test_*`. Use Pytest, pytest-django, and registered markers from `pyproject.toml`. The configured coverage floor is 80%. Add regression tests for changed business behavior; verify transaction rollback with real database integration tests. Browser tests use Playwright/Chromium. MySQL, Redis, and k6 suites require explicit infrastructure; report skips separately from passes.

## Commit & Pull Request Guidelines

Recent commits use short, informal Spanish subjects; no consistent Conventional Commits scheme is established. Prefer descriptive imperative subjects identifying the affected module. PRs should explain the problem, resulting behavior, validation commands, and remaining limitations. Link relevant issues and include screenshots for visible UI changes. Preserve unrelated working-tree changes.

## Security & Configuration

Use the supplied environment examples; never commit `.env` secrets or expose credentials in logs. Run destructive fixtures and load tests only against isolated QA databases. Review schema migrations and monetary behavior changes carefully.
