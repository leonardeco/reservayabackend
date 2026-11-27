"""Qué mesas están ocupadas a una hora dada.

Una reserva ocupa su mesa desde la hora reservada durante `duracion_franja_min`
(90 min por defecto). Dos reservas chocan si sus intervalos se solapan.
"""

from collections.abc import Iterable
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EstadoReserva, Reserva, Restaurante


def _inicio(fecha: date, hora: time) -> datetime:
    return datetime.combine(fecha, hora)


def se_solapan(fecha: date, hora_a: time, hora_b: time, duracion_min: int) -> bool:
    duracion = timedelta(minutes=duracion_min)
    a, b = _inicio(fecha, hora_a), _inicio(fecha, hora_b)
    return a < b + duracion and b < a + duracion


def reservas_activas(db: Session, restaurante_id: int, fecha: date) -> list[Reserva]:
    return list(
        db.scalars(
            select(Reserva).where(
                Reserva.restaurante_id == restaurante_id,
                Reserva.fecha == fecha,
                Reserva.estado != EstadoReserva.CANCELADA,
            )
        )
    )


def mesas_ocupadas(
    reservas: Iterable[Reserva], fecha: date, hora: time, duracion_min: int
) -> set[int]:
    return {r.mesa_id for r in reservas if se_solapan(fecha, r.hora, hora, duracion_min)}


def ocupacion_por_hora(
    db: Session, restaurante: Restaurante, fecha: date, horas: Iterable[time]
) -> dict[time, set[int]]:
    reservas = reservas_activas(db, restaurante.id, fecha)
    duracion = restaurante.duracion_franja_min
    return {h: mesas_ocupadas(reservas, fecha, h, duracion) for h in horas}
