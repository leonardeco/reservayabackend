from fastapi import APIRouter

from app.core.reloj import Ahora
from app.deps import DbSession, Firmador
from app.schemas.auth import LoginEntrada, LoginRespuesta
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["autenticación"])


@router.post("/login", response_model=LoginRespuesta)
def login(db: DbSession, firmador: Firmador, ahora: Ahora, datos: LoginEntrada):
    sesion = AuthService(db, firmador).iniciar_sesion(datos.usuario, datos.password, ahora)
    return LoginRespuesta(
        token=sesion.token,
        vence=sesion.vence,
        usuario=sesion.administrador.usuario,
        restaurante=sesion.restaurante.nombre,
        slug=sesion.restaurante.slug,
    )
