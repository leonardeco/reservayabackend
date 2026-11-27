from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EstadoReserva, Mesa, Reserva, Restaurante
from app.schemas.panel import (
    DiaSemana,
    Estadisticas,
    FranjaHoraria,
    Perfil,
    PerfilActualizar,
    ReservaPanel,
    ReservasDelDia,
    ResumenDia,
)
from app.services.disponibilidad import ahora_local
from app.services.errores import CambioDeEstadoInvalido, ReservaNoEncontrada

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

# Estado actual -> estados a los que puede pasar. Una cancelada ya no vuelve:
# su mesa pudo quedar asignada a otra persona.
TRANSICIONES: dict[EstadoReserva, set[EstadoReserva]] = {
    EstadoReserva.PENDIENTE: {EstadoReserva.CONFIRMADA, EstadoReserva.CANCELADA},
    EstadoReserva.CONFIRMADA: {EstadoReserva.CONFIRMADA, EstadoReserva.CANCELADA},
    EstadoReserva.CANCELADA: set(),
}


def porcentaje(parte: int, total: int) -> int:
    return round(100 * parte / total) if total else 0


class PanelService:
    """Todo lo que ve y cambia el administrador, siempre limitado a su restaurante."""

    def __init__(self, db: Session, restaurante: Restaurante, ahora_utc: datetime) -> None:
        self.db = db
        self.restaurante = restaurante
        self.hoy = ahora_local(restaurante, ahora_utc).date()

    # --- HU04: reservas del día ---------------------------------------------------------

    def reservas_del_dia(self, fecha: date | None = None) -> ReservasDelDia:
        fecha = fecha or self.hoy
        reservas = list(
            self.db.scalars(
                select(Reserva)
                .where(Reserva.restaurante_id == self.restaurante.id, Reserva.fecha == fecha)
                .order_by(Reserva.hora, Reserva.id)
            )
        )
        mesas = self._mesas_activas()
        etiquetas = {m.id: m.etiqueta for m in mesas}
        activas = [r for r in reservas if r.activa]
        con_reserva = {r.mesa_id for r in activas}

        resumen = ResumenDia(
            reservas_hoy=len(activas),
            mesas_totales=len(mesas),
            mesas_disponibles=len([m for m in mesas if m.id not in con_reserva]),
            ocupacion=porcentaje(len(con_reserva & etiquetas.keys()), len(mesas)),
            pendientes=sum(r.estado == EstadoReserva.PENDIENTE for r in reservas),
        )
        return ReservasDelDia(
            fecha=fecha,
            resumen=resumen,
            reservas=[self._a_panel(r, etiquetas) for r in reservas],
        )

    def cambiar_estado(self, reserva_id: int, etiqueta: str) -> ReservaPanel:
        reserva = self.db.get(Reserva, reserva_id)
        if reserva is None or reserva.restaurante_id != self.restaurante.id:
            raise ReservaNoEncontrada()
        actual, nuevo = EstadoReserva(reserva.estado), EstadoReserva(etiqueta.lower())
        if nuevo not in TRANSICIONES[actual]:
            raise CambioDeEstadoInvalido(f"{actual} -> {nuevo}")
        reserva.estado = nuevo.value
        self.db.commit()
        etiquetas = {m.id: m.etiqueta for m in self._mesas_activas()}
        return self._a_panel(reserva, etiquetas)

    # --- HU04: estadísticas -------------------------------------------------------------

    def estadisticas(self) -> Estadisticas:
        """Reservas del mes en curso, ocupación de la semana actual y reservas por hora.

        Ocupación de un día = % de mesas activas con al menos una reserva no cancelada.
        """
        inicio_mes = self.hoy.replace(day=1)
        lunes = self.hoy - timedelta(days=self.hoy.weekday())
        domingo = lunes + timedelta(days=6)
        desde, hasta = min(inicio_mes, lunes), max(self._fin_de_mes(), domingo)

        reservas = [
            r
            for r in self.db.scalars(
                select(Reserva).where(
                    Reserva.restaurante_id == self.restaurante.id,
                    Reserva.fecha >= desde,
                    Reserva.fecha <= hasta,
                    Reserva.estado != EstadoReserva.CANCELADA,
                )
            )
        ]
        total_mesas = len(self._mesas_activas())

        semanal = []
        for i, dia in enumerate(DIAS):
            fecha = lunes + timedelta(days=i)
            mesas_dia = {r.mesa_id for r in reservas if r.fecha == fecha}
            semanal.append(DiaSemana(dia=dia, porcentaje=porcentaje(len(mesas_dia), total_mesas)))

        del_mes = [r for r in reservas if inicio_mes <= r.fecha <= self._fin_de_mes()]
        por_hora = Counter(r.hora.strftime("%H:%M") for r in del_mes)

        return Estadisticas(
            reservas_mes=len(del_mes),
            ocupacion_promedio=round(sum(d.porcentaje for d in semanal) / len(semanal)),
            calificacion=self.restaurante.rating,
            ocupacion_semanal=semanal,
            franjas=[FranjaHoraria(hora=h, reservas=n) for h, n in sorted(por_hora.items())],
        )

    # --- HU05: perfil del restaurante ---------------------------------------------------

    def perfil(self) -> Perfil:
        r = self.restaurante
        return Perfil(
            nombre=r.nombre,
            categoria=r.categoria,
            descripcion=r.descripcion,
            direccion=r.ubicacion,
            telefono=r.telefono,
            web=r.pagina,
            horario=r.horario_resumen,
            capacidad=len(self._mesas_activas()),
            precio="$" * r.precio_nivel,
            imagen=r.imagen_url,
        )

    def actualizar_perfil(self, datos: PerfilActualizar) -> Perfil:
        r = self.restaurante
        r.nombre = datos.nombre
        r.categoria = datos.categoria
        r.descripcion = datos.descripcion
        r.ubicacion = datos.direccion
        r.telefono = datos.telefono
        r.pagina = datos.web
        r.horario_resumen = datos.horario
        r.precio_nivel = len(datos.precio)
        r.imagen_url = datos.imagen
        # El slug no cambia: es la URL pública del restaurante y la usan las reservas.
        self.db.commit()
        return self.perfil()

    # --- apoyo --------------------------------------------------------------------------

    def _mesas_activas(self) -> list[Mesa]:
        return list(
            self.db.scalars(
                select(Mesa).where(
                    Mesa.restaurante_id == self.restaurante.id, Mesa.activa.is_(True)
                )
            )
        )

    def _fin_de_mes(self) -> date:
        siguiente = (self.hoy.replace(day=28) + timedelta(days=4)).replace(day=1)
        return siguiente - timedelta(days=1)

    @staticmethod
    def _a_panel(reserva: Reserva, etiquetas: dict[int, str]) -> ReservaPanel:
        return ReservaPanel(
            id=reserva.id,
            codigo=reserva.codigo,
            cliente=reserva.nombre,
            telefono=reserva.telefono,
            correo=reserva.correo,
            hora=reserva.hora.strftime("%H:%M"),
            personas=reserva.personas,
            mesa=etiquetas.get(reserva.mesa_id, "—"),
            estado=EstadoReserva(reserva.estado).etiqueta,
            notas=reserva.notas,
        )
