# ReservaYa (backend)

API REST del sistema de reservas de restaurantes ReservaYa, desarrollada para la asignatura Mantenimiento de Software (Ingeniería de Software, Corporación Universitaria Iberoamericana).

## Historias de usuario

| ID | Usuario | Necesidad principal |
|---|---|---|
| HU01 | Comensal | Consultar restaurantes y su disponibilidad. |
| HU02 | Comensal | Realizar una reserva y recibir el código de confirmación. |
| HU03 | Administrador | Iniciar sesión para acceder a funciones de gestión del restaurante. |
| HU04 | Administrador | Consultar información sobre ocupación y reservas. |
| HU05 | Administrador | Consultar y cambiar la información general del restaurante. |

## Equipo

- José Leonardo Guzmán Tobón
- Kevin Smith Correal Chocontá
- Saleth Tatiana Ibarra Martínez

## Contenido del repositorio

| Ruta | Qué es |
|---|---|
| `backend/` | API con FastAPI, SQLAlchemy y Alembic. Instalación y endpoints en [backend/README.md](backend/README.md) |
| `docs/api/openapi.json` | Contrato de la API, generado desde el backend |
| `render.yaml` | Despliegue de la API y su base PostgreSQL en Render |
| `.github/workflows/ci.yml` | Integración continua: lint y pruebas sobre PostgreSQL 16 |

## Forma de trabajo

Cada historia de usuario se desarrolla en su propia rama (`feat/hu0X-...`) y entra a `main` por Pull Request cuando la integración continua pasa.
