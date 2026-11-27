from datetime import UTC, date, datetime, time
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EstadoReserva(StrEnum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CANCELADA = "cancelada"

    @property
    def etiqueta(self) -> str:
        """Texto que muestra el panel: 'Confirmada', 'Pendiente', 'Cancelada'."""
        return self.value.capitalize()


def _ahora_utc() -> datetime:
    return datetime.now(UTC)


class Reserva(Base):
    __tablename__ = "reserva"
    __table_args__ = (
        CheckConstraint("personas BETWEEN 1 AND 20", name="personas"),
        CheckConstraint("estado IN ('pendiente', 'confirmada', 'cancelada')", name="estado"),
        Index("ix_reserva_restaurante_fecha", "restaurante_id", "fecha"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    restaurante_id: Mapped[int] = mapped_column(ForeignKey("restaurante.id", ondelete="CASCADE"))
    mesa_id: Mapped[int] = mapped_column(ForeignKey("mesa.id", ondelete="CASCADE"), index=True)
    fecha: Mapped[date] = mapped_column(Date)
    hora: Mapped[time] = mapped_column(Time)
    personas: Mapped[int] = mapped_column(Integer)
    nombre: Mapped[str] = mapped_column(String(120))
    telefono: Mapped[str] = mapped_column(String(30))
    correo: Mapped[str] = mapped_column(String(160))
    notas: Mapped[str] = mapped_column(Text, default="", server_default="")
    estado: Mapped[str] = mapped_column(
        String(12), default=EstadoReserva.CONFIRMADA.value, server_default="confirmada"
    )
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_ahora_utc)

    @property
    def activa(self) -> bool:
        return self.estado != EstadoReserva.CANCELADA
