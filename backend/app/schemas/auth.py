from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Usuario = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Contrasena = Annotated[str, StringConstraints(min_length=1, max_length=128)]


class LoginEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")

    usuario: Usuario
    password: Contrasena


class LoginRespuesta(BaseModel):
    token: str
    tipo: str = "Bearer"
    vence: datetime
    usuario: str
    restaurante: str
    slug: str
