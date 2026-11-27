from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.core.reloj import Ahora
from app.deps import AdminActual, DbSession
from app.models import Restaurante
from app.schemas.panel import (
    CambioEstado,
    Estadisticas,
    Perfil,
    PerfilActualizar,
    ReservaPanel,
    ReservasDelDia,
)
from app.services.panel import PanelService


def get_panel(db: DbSession, admin: AdminActual, ahora: Ahora) -> PanelService:
    return PanelService(db, db.get(Restaurante, admin.restaurante_id), ahora)


Panel = Annotated[PanelService, Depends(get_panel)]

router = APIRouter(prefix="/admin", tags=["panel del administrador"])


@router.get("/reservas", response_model=ReservasDelDia)
def reservas_del_dia(panel: Panel, fecha: Annotated[date | None, Query()] = None):
    return panel.reservas_del_dia(fecha)


@router.patch("/reservas/{reserva_id}", response_model=ReservaPanel)
def cambiar_estado(panel: Panel, reserva_id: Annotated[int, Path(ge=1)], cambio: CambioEstado):
    return panel.cambiar_estado(reserva_id, cambio.estado)


@router.get("/estadisticas", response_model=Estadisticas)
def estadisticas(panel: Panel):
    return panel.estadisticas()


@router.get("/restaurante", response_model=Perfil)
def ver_perfil(panel: Panel):
    return panel.perfil()


@router.put("/restaurante", response_model=Perfil)
def guardar_perfil(panel: Panel, datos: PerfilActualizar):
    return panel.actualizar_perfil(datos)
