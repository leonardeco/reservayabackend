from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.seguridad import FirmadorTokens, HashContrasena, TokenInvalido
from app.core.texto import normalizar_texto
from app.models import Administrador, Restaurante
from app.services.errores import CredencialesInvalidas, NoAutenticado


def normalizar_usuario(usuario: str) -> str:
    """'La Terraza', 'la terraza' y 'laterraza' son el mismo usuario."""
    return normalizar_texto(usuario).replace(" ", "")


@dataclass(frozen=True)
class Sesion:
    token: str
    vence: datetime
    administrador: Administrador
    restaurante: Restaurante


class AuthService:
    def __init__(self, db: Session, firmador: FirmadorTokens) -> None:
        self.db = db
        self.firmador = firmador

    def iniciar_sesion(self, usuario: str, contrasena: str, ahora: datetime) -> Sesion:
        admin = self.db.scalar(
            select(Administrador).where(Administrador.usuario == normalizar_usuario(usuario))
        )
        # Mismo error si el usuario no existe o la clave falla: no se revela cuál de los dos.
        if admin is None or not admin.activo:
            HashContrasena.generar(contrasena)  # mismo tiempo de respuesta en ambos casos
            raise CredencialesInvalidas()
        if not HashContrasena.verificar(contrasena, admin.password_hash):
            raise CredencialesInvalidas()

        restaurante = self.db.get(Restaurante, admin.restaurante_id)
        token = self.firmador.emitir(admin.id, admin.restaurante_id, ahora)
        return Sesion(token, self.firmador.vence_en(ahora), admin, restaurante)

    def administrador_del_token(self, token: str, ahora: datetime) -> Administrador:
        try:
            datos = self.firmador.leer(token, ahora)
        except TokenInvalido as exc:
            raise NoAutenticado() from exc
        admin = self.db.get(Administrador, datos.get("sub"))
        if admin is None or not admin.activo or admin.restaurante_id != datos.get("rid"):
            raise NoAutenticado()
        return admin
