from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.reloj import Ahora
from app.core.seguridad import FirmadorTokens
from app.db.session import SessionLocal
from app.models import Administrador
from app.services.auth import AuthService
from app.services.errores import NoAutenticado


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


DbSession = Annotated[Session, Depends(get_db)]


def get_firmador() -> FirmadorTokens:
    settings = get_settings()
    return FirmadorTokens(settings.secret_key, settings.token_horas)


Firmador = Annotated[FirmadorTokens, Depends(get_firmador)]

_bearer = HTTPBearer(auto_error=False)


def get_admin_actual(
    db: DbSession,
    firmador: Firmador,
    ahora: Ahora,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Administrador:
    """Exige 'Authorization: Bearer <token>' con un token emitido por /auth/login."""
    if credenciales is None:
        raise NoAutenticado()
    return AuthService(db, firmador).administrador_del_token(credenciales.credentials, ahora)


AdminActual = Annotated[Administrador, Depends(get_admin_actual)]
