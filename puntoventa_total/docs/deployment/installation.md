# Instalacion

## Opcion A: Docker (recomendada)

    git clone <repo> && cd puntoventa_total
    cp .env.example .env       # ajustar claves y contrasenas
    docker compose up --build
    docker compose exec web python scripts/crear_admin.py --username admin --password "Admin1234!"
    docker compose exec web python scripts/seed_data.py

Queda disponible en http://localhost (nginx) o http://localhost:8000 (gunicorn directo).

## Opcion B: local

Requisitos: Python 3.11, MySQL 8, Redis.

    python -m venv .venv
    .venv\Scripts\activate        # Windows
    pip install -r requirements/development.txt
    cp .env.example .env          # DB_HOST=127.0.0.1
    python manage.py migrate
    python scripts/crear_admin.py
    python manage.py runserver

## Verificacion

    bash scripts/check_health.sh

## Solucion de problemas

- **mysqlclient no compila (Windows)**: instalar MySQL Connector/C o usar
  `pip install pymysql && pymysql.install_as_MySQLdb()` en desarrollo.
- **Redis no disponible**: en `config/settings/development.py` se usa locmem automaticamente.
- **Error de claves**: revisar `DJANGO_SECRET_KEY` y `ALLOWED_HOSTS` en `.env`.

