from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BloqueoFecha, HorarioTurno, Mesa, Restaurante
from app.services.ocupacion import ocupacion_por_hora


@dataclass(frozen=True)
class Franja:
    hora: time
    estado: str


@dataclass(frozen=True)
class Disponibilidad:
    fecha: date
    personas: int
    franjas: list[Franja]
    motivo: str | None = None
    mensaje: str | None = None


class FechaFueraDeRango(ValueError):
    """La fecha es pasada o supera la antelación máxima del restaurante."""


def ahora_local(restaurante: Restaurante, ahora_utc: datetime) -> datetime:
    return ahora_utc.astimezone(ZoneInfo(restaurante.zona_horaria))


def generar_franjas(turnos: Sequence[HorarioTurno], duracion_min: int) -> list[time]:
    paso = timedelta(minutes=duracion_min)
    horas: set[time] = set()
    for turno in turnos:
        actual = datetime.combine(date.min, turno.apertura)
        limite = datetime.combine(date.min, turno.ultima_franja)
        while actual <= limite:
            horas.add(actual.time())
            actual += paso
    return sorted(horas)


def mesas_compatibles(mesas: Sequence[Mesa], personas: int) -> list[Mesa]:
    return [m for m in mesas if m.activa and m.capacidad_min <= personas <= m.capacidad_max]


def calcular_disponibilidad(
    db: Session,
    restaurante: Restaurante,
    fecha: date,
    personas: int,
    ahora_utc: datetime,
    ocupadas: Mapping[time, set[int]] | None = None,
) -> Disponibilidad:
    """`ocupadas` asocia cada franja con los ids de mesa ya reservados en esa fecha."""
    local = ahora_local(restaurante, ahora_utc)
    hoy = local.date()
    if fecha < hoy or fecha > hoy + timedelta(days=restaurante.antelacion_max_dias):
        raise FechaFueraDeRango(fecha.isoformat())

    turnos = db.scalars(
        select(HorarioTurno).where(
            HorarioTurno.restaurante_id == restaurante.id,
            HorarioTurno.dia_semana == fecha.weekday(),
        )
    ).all()
    if not turnos:
        return Disponibilidad(fecha, personas, [], motivo="cerrado")

    bloqueos = db.scalars(
        select(BloqueoFecha).where(
            BloqueoFecha.restaurante_id == restaurante.id, BloqueoFecha.fecha == fecha
        )
    ).all()
    dia_completo = next((b for b in bloqueos if b.hora_desde is None), None)
    if dia_completo is not None:
        return Disponibilidad(fecha, personas, [], motivo="bloqueado", mensaje=dia_completo.motivo)

    horas = [
        h
        for h in generar_franjas(turnos, restaurante.duracion_franja_min)
        if not (fecha == hoy and h <= local.time())
        and not any(b.hora_desde <= h < b.hora_hasta for b in bloqueos)
    ]

    mesas = db.scalars(
        select(Mesa).where(Mesa.restaurante_id == restaurante.id, Mesa.activa.is_(True))
    ).all()
    compatibles = {m.id for m in mesas_compatibles(mesas, personas)}
    if not compatibles:
        grande = bool(mesas) and personas > max(m.capacidad_max for m in mesas)
        return Disponibilidad(
            fecha,
            personas,
            [Franja(h, "agotada") for h in horas],
            motivo="grupo_grande" if grande else "sin_mesas",
        )

    if ocupadas is None:
        ocupadas = ocupacion_por_hora(db, restaurante, fecha, horas)
    franjas = [
        Franja(h, "libre" if compatibles - ocupadas.get(h, set()) else "agotada") for h in horas
    ]
    return Disponibilidad(fecha, personas, franjas)
