"""Respuestas del panel del administrador.

Los nombres de campo copian los del objeto `perfil` del componente Perfil del front,
para conectarlo sin traducir nada.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints


def _texto(maximo: int, minimo: int = 1):
    return Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=minimo, max_length=maximo)
    ]


class Perfil(BaseModel):
    nombre: str
    categoria: str
    descripcion: str
    direccion: str
    telefono: str
    web: str
    horario: str
    capacidad: int
    precio: str
    imagen: str


class PerfilActualizar(BaseModel):
    """`capacidad` se ignora si llega: sale del número de mesas activas, no se edita aquí."""

    model_config = ConfigDict(extra="ignore")

    nombre: _texto(120, 2)
    categoria: _texto(40)
    descripcion: _texto(1000)
    direccion: _texto(160)
    telefono: _texto(30)
    web: _texto(160, 0)
    horario: _texto(160)
    precio: Literal["$", "$$", "$$$"]
    imagen: Annotated[
        str, StringConstraints(strip_whitespace=True, max_length=500, pattern=r"^https?://\S+$")
    ]
