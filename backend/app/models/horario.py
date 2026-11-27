from datetime import date, time

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, SmallInteger, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class HorarioTurno(Base):
    __tablename__ = "horario_turno"
    __table_args__ = (
        CheckConstraint("dia_semana BETWEEN 0 AND 6", name="dia_semana"),
        CheckConstraint("apertura <= ultima_franja", name="rango"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(
        ForeignKey("restaurante.id", ondelete="CASCADE"), index=True
    )
    dia_semana: Mapped[int] = mapped_column(SmallInteger)
    apertura: Mapped[time] = mapped_column(Time)
    ultima_franja: Mapped[time] = mapped_column(Time)


class BloqueoFecha(Base):
    __tablename__ = "bloqueo_fecha"
    __table_args__ = (
        CheckConstraint(
            "(hora_desde IS NULL AND hora_hasta IS NULL) "
            "OR (hora_desde IS NOT NULL AND hora_hasta IS NOT NULL AND hora_desde < hora_hasta)",
            name="rango",
        ),
        Index("ix_bloqueo_fecha_restaurante_fecha", "restaurante_id", "fecha"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id", ondelete="CASCADE"))
    fecha: Mapped[date] = mapped_column(Date)
    hora_desde: Mapped[time | None] = mapped_column(Time, nullable=True)
    hora_hasta: Mapped[time | None] = mapped_column(Time, nullable=True)
    motivo: Mapped[str] = mapped_column(String(120))
