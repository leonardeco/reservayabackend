from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    Integer,
    SmallInteger,
    String,
    Text,
    event,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.texto import normalizar_texto
from app.db.base import Base


class Restaurante(Base):
    __tablename__ = "restaurante"
    __table_args__ = (
        CheckConstraint("precio_nivel BETWEEN 1 AND 3", name="precio_nivel"),
        CheckConstraint("rating >= 0 AND rating <= 5", name="rating"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str] = mapped_column(Text)
    ubicacion: Mapped[str] = mapped_column(String(160))
    imagen_url: Mapped[str] = mapped_column(String(500))
    imagen_comida_url: Mapped[str] = mapped_column(String(500))
    rating: Mapped[float] = mapped_column(Float)
    precio_nivel: Mapped[int] = mapped_column(SmallInteger)
    categoria: Mapped[str] = mapped_column(String(40), index=True)
    horario_resumen: Mapped[str] = mapped_column(String(160))
    telefono: Mapped[str] = mapped_column(String(30))
    pagina: Mapped[str] = mapped_column(String(160))
    popular: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    zona_horaria: Mapped[str] = mapped_column(
        String(40), default="America/Bogota", server_default="America/Bogota"
    )
    duracion_franja_min: Mapped[int] = mapped_column(Integer, default=90, server_default="90")
    antelacion_max_dias: Mapped[int] = mapped_column(Integer, default=60, server_default="60")
    # Índices de búsqueda normalizados (sin tildes): se recalculan solos al insertar o editar.
    texto_busqueda: Mapped[str] = mapped_column(Text, server_default="")
    ubicacion_busqueda: Mapped[str] = mapped_column(String(160), server_default="")


def indexar_busqueda(restaurante: Restaurante) -> None:
    partes = [
        restaurante.nombre,
        restaurante.descripcion,
        restaurante.ubicacion,
        restaurante.categoria,
    ]
    restaurante.texto_busqueda = normalizar_texto(" ".join(p or "" for p in partes))
    restaurante.ubicacion_busqueda = normalizar_texto(restaurante.ubicacion or "")


@event.listens_for(Restaurante, "before_insert")
@event.listens_for(Restaurante, "before_update")
def _indexar_antes_de_guardar(_mapper, _connection, restaurante: Restaurante) -> None:
    indexar_busqueda(restaurante)
