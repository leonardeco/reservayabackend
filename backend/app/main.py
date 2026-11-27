from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.routers import auth, health, reservas, restaurantes
from app.services.errores import ErrorDeNegocio

API_PREFIX = "/api/v1"


async def _error_de_negocio(_request: Request, exc: ErrorDeNegocio) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.codigo})


def create_app() -> FastAPI:
    app = FastAPI(
        title="ReservaYa API",
        version="1.0.0",
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
    )
    app.add_exception_handler(ErrorDeNegocio, _error_de_negocio)

    origenes = get_settings().lista_cors
    if origenes:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origenes,
            allow_methods=["GET", "POST", "PATCH", "PUT"],
            allow_headers=["Authorization", "Content-Type"],
        )

    for modulo in (health, restaurantes, reservas, auth):
        app.include_router(modulo.router, prefix=API_PREFIX)
    return app


app = create_app()
