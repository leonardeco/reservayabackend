from sqlalchemy import Boolean, ForeignKey, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Administrador(Base):
    """Usuario del panel. Cada restaurante tiene un administrador."""

    __tablename__ = "administrador"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario: Mapped[str] = mapped_column(String(60), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    restaurante_id: Mapped[int] = mapped_column(
        ForeignKey("restaurante.id", ondelete="CASCADE"), unique=True
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
