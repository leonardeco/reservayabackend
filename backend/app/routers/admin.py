from typing import Annotated

from fastapi import APIRouter, Depends

from app.deps import AdminActual, DbSession
from app.models import Restaurante
from app.schemas.panel import Perfil, PerfilActualizar
from app.services.panel import PanelService


def get_panel(db: DbSession, admin: AdminActual) -> PanelService:
    return PanelService(db, db.get(Restaurante, admin.restaurante_id))


Panel = Annotated[PanelService, Depends(get_panel)]

router = APIRouter(prefix="/admin", tags=["panel del administrador"])


@router.get("/restaurante", response_model=Perfil)
def ver_perfil(panel: Panel):
    return panel.perfil()


@router.put("/restaurante", response_model=Perfil)
def guardar_perfil(panel: Panel, datos: PerfilActualizar):
    return panel.actualizar_perfil(datos)
