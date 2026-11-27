import secrets
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BloqueoFecha, EstadoReserva, HorarioTurno, Mesa, Reserva, Restaurante
from app.schemas.reserva import ReservaCrear
from app.services.disponibilidad import FechaFueraDeRango, ahora_local, mesas_compatibles
from app.services.errores import FueraDeHorario, SinMesaDisponible
from app.services.ocupacion import mesas_ocupadas, reservas_activas


class ReservaService:
    """Crea reservas: valida fecha y hora, asigna una mesa libre y genera el código."""

    INTENTOS_CODIGO = 10

    def __init__(self, db: Session, ahora_utc: datetime) -> None:
        self.db = db
        self.ahora_utc = ahora_utc

    def crear(self, restaurante: Restaurante, datos: ReservaCrear) -> Reserva:
        hora = datos.hora.replace(second=0, microsecond=0, tzinfo=None)
        self._validar_fecha(restaurante, datos.fecha, hora)
        self._validar_horario(restaurante, datos.fecha, hora)
        mesa = self._elegir_mesa(restaurante, datos.fecha, hora, datos.personas)

        reserva = Reserva(
            codigo=self._generar_codigo(datos.fecha),
            restaurante_id=restaurante.id,
            mesa_id=mesa.id,
            fecha=datos.fecha,
            hora=hora,
            personas=datos.personas,
            nombre=datos.nombre,
            telefono=datos.telefono,
            correo=datos.correo,
            notas=datos.notas,
            estado=EstadoReserva.CONFIRMADA.value,
        )
        self.db.add(reserva)
        self.db.commit()
        return reserva

    def _validar_fecha(self, restaurante: Restaurante, fecha: date, hora: time) -> None:
        local = ahora_local(restaurante, self.ahora_utc)
        hoy = local.date()
        if fecha < hoy or fecha > hoy + timedelta(days=restaurante.antelacion_max_dias):
            raise FechaFueraDeRango(fecha.isoformat())
        if fecha == hoy and hora <= local.time().replace(tzinfo=None):
            raise FueraDeHorario("la hora ya pasó")

    def _validar_horario(self, restaurante: Restaurante, fecha: date, hora: time) -> None:
        turnos = self.db.scalars(
            select(HorarioTurno).where(
                HorarioTurno.restaurante_id == restaurante.id,
                HorarioTurno.dia_semana == fecha.weekday(),
            )
        ).all()
        if not any(t.apertura <= hora <= t.ultima_franja for t in turnos):
            raise FueraDeHorario("el restaurante no atiende a esa hora")

        bloqueos = self.db.scalars(
            select(BloqueoFecha).where(
                BloqueoFecha.restaurante_id == restaurante.id, BloqueoFecha.fecha == fecha
            )
        ).all()
        for bloqueo in bloqueos:
            if bloqueo.hora_desde is None or bloqueo.hora_desde <= hora < bloqueo.hora_hasta:
                raise FueraDeHorario(bloqueo.motivo)

    def _elegir_mesa(
        self, restaurante: Restaurante, fecha: date, hora: time, personas: int
    ) -> Mesa:
        # FOR UPDATE: en PostgreSQL dos reservas simultáneas del mismo restaurante esperan
        # su turno y no se quedan con la misma mesa. SQLite lo ignora (un solo escritor).
        mesas = self.db.scalars(
            select(Mesa)
            .where(Mesa.restaurante_id == restaurante.id, Mesa.activa.is_(True))
            .with_for_update()
        ).all()
        ocupadas = mesas_ocupadas(
            reservas_activas(self.db, restaurante.id, fecha),
            fecha,
            hora,
            restaurante.duracion_franja_min,
        )
        libres = [m for m in mesas_compatibles(mesas, personas) if m.id not in ocupadas]
        if not libres:
            raise SinMesaDisponible()
        # La mesa más pequeña que sirva: deja las grandes para los grupos.
        return min(libres, key=lambda m: (m.capacidad_max, m.id))

    def _generar_codigo(self, fecha: date) -> str:
        for _ in range(self.INTENTOS_CODIGO):
            codigo = f"RY-{fecha:%Y%m%d}-{secrets.randbelow(9000) + 1000}"
            if self.db.scalar(select(Reserva.id).where(Reserva.codigo == codigo)) is None:
                return codigo
        raise RuntimeError("no se pudo generar un código de reserva único")
