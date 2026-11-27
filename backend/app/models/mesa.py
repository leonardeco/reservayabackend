from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, UniqueConstraint, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Mesa(Base):
    __tablename__ = "mesa"
    __table_args__ = (
        UniqueConstraint("restaurante_id", "etiqueta", name="uq_mesa_restaurante_etiqueta"),
        CheckConstraint(
            "capacidad_min >= 1 AND capacidad_min <= capacidad_max AND capacidad_max <= 20",
            name="capacidad",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    restaurante_id: Mapped[int] = mapped_column(
        ForeignKey("restaurante.id", ondelete="CASCADE"), index=True
    )
    etiqueta: Mapped[str] = mapped_column(String(30))
    capacidad_min: Mapped[int] = mapped_column(Integer)
    capacidad_max: Mapped[int] = mapped_column(Integer)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
