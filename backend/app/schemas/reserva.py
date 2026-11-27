from datetime import date, time
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_serializer

Nombre = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
Telefono = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=7, max_length=30, pattern=r"^\+?[0-9 ()-]+$"
    ),
]
Correo = Annotated[
    str,
    StringConstraints(strip_whitespace=True, max_length=160, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
]
Notas = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class ReservaCrear(BaseModel):
    """Lo que envía el formulario de reserva (mismos campos que ReservationService del front)."""

    model_config = ConfigDict(extra="forbid")

    fecha: date
    hora: time
    personas: Annotated[int, Field(ge=1, le=20)]
    nombre: Nombre
    telefono: Telefono
    correo: Correo
    notas: Notas = ""


class ReservaCreada(BaseModel):
    codigo: str
    restaurante: str
    slug: str
    ubicacion: str
    fecha: date
    hora: time
    personas: int
    mesa: str
    estado: str
    nombre: str
    correo: str

    @field_serializer("hora")
    def _hora_hhmm(self, hora: time) -> str:
        return hora.strftime("%H:%M")
