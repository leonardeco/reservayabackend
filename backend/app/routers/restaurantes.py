from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import StringConstraints

from app.core.reloj import Ahora
from app.deps import DbSession
from app.schemas.disponibilidad import DisponibilidadRead
from app.schemas.restaurante import RestauranteRead
from app.services.disponibilidad import FechaFueraDeRango, calcular_disponibilidad
from app.services.restaurantes import listar_restaurantes, obtener_restaurante

router = APIRouter(tags=["restaurantes"])

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
SIN_CONTROL = r"^[^\x00-\x1f\x7f]*$"

Categoria = Annotated[str, StringConstraints(max_length=40, pattern=SIN_CONTROL)]


@router.get("/restaurantes", response_model=list[RestauranteRead])
def listar(
    db: DbSession,
    ahora: Ahora,
    q: Annotated[str | None, Query(max_length=80, pattern=SIN_CONTROL)] = None,
    zona: Annotated[str | None, Query(max_length=80, pattern=SIN_CONTROL)] = None,
    categoria: Annotated[list[Categoria] | None, Query(max_length=10)] = None,
    precio: Annotated[int | None, Query(ge=1, le=3)] = None,
    rating_min: Annotated[float | None, Query(ge=0, le=5)] = None,
    fecha: Annotated[date | None, Query()] = None,
    personas: Annotated[int | None, Query(ge=1, le=20)] = None,
):
    restaurantes = listar_restaurantes(
        db,
        q=q,
        zona=zona,
        categorias=categoria or (),
        precio=precio,
        rating_min=rating_min,
    )
    if fecha is None and personas is None:
        return restaurantes
    if fecha is None or personas is None:
        raise HTTPException(status_code=422, detail="fecha_y_personas_van_juntos")
    # HU01 CA03: con fecha y personas solo se listan los que tienen alguna franja libre.
    try:
        return [
            r
            for r in restaurantes
            if any(
                f.estado == "libre"
                for f in calcular_disponibilidad(db, r, fecha, personas, ahora).franjas
            )
        ]
    except FechaFueraDeRango as exc:
        raise HTTPException(status_code=422, detail="fecha_fuera_de_rango") from exc


@router.get("/restaurantes/{slug}", response_model=RestauranteRead)
def detalle(
    db: DbSession,
    slug: Annotated[str, Path(max_length=80, pattern=SLUG_PATTERN)],
):
    restaurante = obtener_restaurante(db, slug)
    if restaurante is None:
        raise HTTPException(status_code=404, detail="restaurante_no_encontrado")
    return restaurante


@router.get("/restaurantes/{slug}/disponibilidad", response_model=DisponibilidadRead)
def disponibilidad(
    db: DbSession,
    ahora: Ahora,
    slug: Annotated[str, Path(max_length=80, pattern=SLUG_PATTERN)],
    fecha: Annotated[date, Query()],
    personas: Annotated[int, Query(ge=1, le=20)],
):
    restaurante = obtener_restaurante(db, slug)
    if restaurante is None:
        raise HTTPException(status_code=404, detail="restaurante_no_encontrado")
    try:
        return calcular_disponibilidad(db, restaurante, fecha, personas, ahora)
    except FechaFueraDeRango as exc:
        raise HTTPException(status_code=422, detail="fecha_fuera_de_rango") from exc
