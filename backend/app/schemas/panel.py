"""Respuestas del panel del administrador.

Los nombres de campo copian los del front (ReservaItem, DiaSemana, FranjaHoraria y el
objeto `perfil` del componente Perfil) para conectarlo sin traducir nada.
"""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

EtiquetaEstado = Literal["Pendiente", "Confirmada", "Cancelada"]


class ReservaPanel(BaseModel):
    id: int
    codigo: str
    cliente: str
    telefono: str
    correo: str
    hora: str
    personas: int
    mesa: str
    estado: EtiquetaEstado
    notas: str


class ResumenDia(BaseModel):
    reservas_hoy: int
    mesas_totales: int
    mesas_disponibles: int
    ocupacion: int
    pendientes: int


class ReservasDelDia(BaseModel):
    fecha: date
    resumen: ResumenDia
    reservas: list[ReservaPanel]


class CambioEstado(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estado: Literal["Confirmada", "Cancelada"]


class DiaSemana(BaseModel):
    dia: str
    porcentaje: int


class FranjaHoraria(BaseModel):
    hora: str
    reservas: int


class Estadisticas(BaseModel):
    reservas_mes: int
    ocupacion_promedio: int
    calificacion: float
    ocupacion_semanal: list[DiaSemana]
    franjas: list[FranjaHoraria]


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
