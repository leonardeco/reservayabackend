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
python -m seeds.seed     # restaurantes, mesas, horarios y administrador de ejemplo
uvicorn app.main:app --reload --port 8000
```

- Salud: http://localhost:8000/api/v1/health
- Documentación interactiva (Swagger): http://localhost:8000/api/v1/docs

Usuario de prueba del panel: **La Terraza** / **terraza123** (los mismos que muestra el login del prototipo).

## Endpoints

Todas las rutas empiezan por `/api/v1`. Los errores responden `{"detail": "<codigo>"}`.

| Historia | Método y ruta | Qué hace |
|---|---|---|
| HU01 | `GET /restaurantes` | Lista con filtros `q`, `zona`, `categoria`, `precio`, `rating_min`. Con `fecha` y `personas` solo devuelve los que tienen alguna franja libre |
| HU01 | `GET /restaurantes/{slug}` | Detalle de un restaurante |
| HU01 | `GET /restaurantes/{slug}/disponibilidad?fecha=&personas=` | Franjas del día (`libre` / `agotada`) |
| HU02 | `POST /restaurantes/{slug}/reservas` | Crea la reserva, asigna mesa y devuelve el código `RY-AAAAMMDD-NNNN` |
| HU03 | `POST /auth/login` | Usuario y contraseña → token para el panel |
| HU05 | `GET /admin/restaurante` | Perfil del restaurante del administrador |
| HU05 | `PUT /admin/restaurante` | Guarda el perfil en la base de datos |

Las rutas `/admin/*` piden la cabecera `Authorization: Bearer <token>`.

### Errores más comunes

| Código HTTP | `detail` | Cuándo |
|---|---|---|
| 401 | `credenciales_invalidas` | Usuario o contraseña incorrectos |
| 401 | `no_autenticado` | Falta el token, está vencido o alterado |
| 404 | `restaurante_no_encontrado` | El restaurante no existe |
| 409 | `fuera_de_horario` | El restaurante no atiende a esa hora, la hora ya pasó o el día está bloqueado |
| 409 | `sin_mesa_disponible` | No queda mesa para ese número de personas a esa hora |
| 422 | `fecha_fuera_de_rango` | Fecha pasada o más allá de la antelación permitida |

### Reglas de reserva

- Una reserva ocupa la mesa 90 minutos desde la hora elegida.
- Se acepta cualquier hora dentro del horario del día (por ejemplo 19:30 aunque las franjas sean cada 90 min).
- Se asigna la mesa más pequeña donde quepa el grupo, para dejar libres las grandes.

## Estructura (orientada a objetos)

| Capa | Carpeta | Clases principales |
|---|---|---|
| Modelos (tablas) | `app/models/` | `Restaurante`, `Mesa`, `HorarioTurno`, `BloqueoFecha`, `Reserva`, `Administrador` |
| Esquemas (entrada/salida) | `app/schemas/` | `RestauranteRead`, `DisponibilidadRead`, `ReservaCrear`, `ReservaCreada`, `LoginEntrada`, `Perfil` |
| Servicios (reglas) | `app/services/` | `calcular_disponibilidad`, `ReservaService`, `AuthService`, `PanelService` |
| Errores | `app/services/errores.py` | `ErrorDeNegocio` y sus subclases, cada una con su código HTTP |
| Seguridad | `app/core/seguridad.py` | `HashContrasena`, `FirmadorTokens` |
| Rutas | `app/routers/` | Reciben la petición y delegan en los servicios |

## Despliegue en Render

El archivo `render.yaml` (en la raíz del repositorio) crea la API y su base PostgreSQL:

1. En Render: **New → Blueprint** y elegir el repositorio.
2. Render crea `reservaya-api` y `reservaya-db`, genera `SECRET_KEY` y conecta `DATABASE_URL`.
3. Al arrancar corre `alembic upgrade head` y `python -m seeds.seed`, así que la base queda lista con datos de ejemplo.
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
