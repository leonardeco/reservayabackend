from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from app.core.reloj import Ahora
from app.deps import DbSession
from app.models import EstadoReserva, Mesa
from app.routers.restaurantes import SLUG_PATTERN
from app.schemas.reserva import ReservaCreada, ReservaCrear
from app.services.disponibilidad import FechaFueraDeRango
from app.services.errores import RestauranteNoEncontrado
from app.services.reservas import ReservaService
from app.services.restaurantes import obtener_restaurante

router = APIRouter(tags=["reservas"])


@router.post(
    "/restaurantes/{slug}/reservas",
    response_model=ReservaCreada,
    status_code=status.HTTP_201_CREATED,
)
def crear_reserva(
    db: DbSession,
    ahora: Ahora,
    slug: Annotated[str, Path(max_length=80, pattern=SLUG_PATTERN)],
    datos: ReservaCrear,
):
    restaurante = obtener_restaurante(db, slug)
    if restaurante is None:
        raise RestauranteNoEncontrado()
    try:
        reserva = ReservaService(db, ahora).crear(restaurante, datos)
    except FechaFueraDeRango as exc:
        raise HTTPException(status_code=422, detail="fecha_fuera_de_rango") from exc

    mesa = db.get(Mesa, reserva.mesa_id)
    return ReservaCreada(
        codigo=reserva.codigo,
        restaurante=restaurante.nombre,
        slug=restaurante.slug,
        ubicacion=restaurante.ubicacion,
        fecha=reserva.fecha,
        hora=reserva.hora,
        personas=reserva.personas,
        mesa=mesa.etiqueta if mesa else "",
        estado=EstadoReserva(reserva.estado).etiqueta,
        nombre=reserva.nombre,
        correo=reserva.correo,
    )
