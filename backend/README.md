# ReservaYa API (backend)

API REST de ReservaYa construida con FastAPI, SQLAlchemy 2 y Alembic. Todas las rutas viven bajo `/api/v1`.

## Requisitos

- Python 3.12
- (Opcional) PostgreSQL 16 para correr las pruebas como en la integración continua

## Puesta en marcha (Windows)

```bash
cd backend
python -m venv .venv
# Git Bash
source .venv/Scripts/activate
# PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

- Salud: http://localhost:8000/api/v1/health
- Documentación interactiva (Swagger): http://localhost:8000/api/v1/docs

## Endpoints

Por ahora la API solo expone `GET /api/v1/health`, que revisa la conexión con la base de datos. Cada historia de usuario agrega sus rutas.

## Despliegue en Render

El archivo `render.yaml` (en la raíz del repositorio) crea la API y su base PostgreSQL:

1. En Render: **New → Blueprint** y elegir el repositorio.
2. Render crea `reservaya-api` y `reservaya-db` y conecta `DATABASE_URL`.
3. Al arrancar corre `alembic upgrade head`.
4. Probar `https://reservaya-api.onrender.com/api/v1/health`.

El plan gratuito se duerme tras un rato sin uso: la primera petición tarda unos segundos en responder.

## Pruebas

```bash
pytest
```

Por defecto las pruebas usan SQLite en un directorio temporal. Si se define `TEST_DATABASE_URL` con una URL de PostgreSQL (base `*_test`) corren contra PostgreSQL; en la integración continua siempre corren contra PostgreSQL 16.

## Calidad

```bash
ruff check .
ruff format .
```
