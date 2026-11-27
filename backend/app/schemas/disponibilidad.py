from datetime import date, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer


class FranjaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hora: time
    estado: Literal["libre", "agotada"]

    @field_serializer("hora")
    def _hora_hhmm(self, hora: time) -> str:
        return hora.strftime("%H:%M")


class DisponibilidadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fecha: date
    personas: int
    franjas: list[FranjaRead]
    motivo: Literal["cerrado", "bloqueado", "grupo_grande", "sin_mesas"] | None
    mensaje: str | None
