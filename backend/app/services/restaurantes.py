from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.texto import normalizar_texto
from app.models import Restaurante
from app.models.restaurante import indexar_busqueda


def actualizar_texto_busqueda(restaurante: Restaurante) -> None:
    """Recalcula los índices sin esperar al flush (el modelo también lo hace al guardar)."""
    indexar_busqueda(restaurante)


def listar_restaurantes(
    db: Session,
    *,
    q: str | None = None,
    zona: str | None = None,
    categorias: Sequence[str] = (),
    precio: int | None = None,
    rating_min: float | None = None,
) -> list[Restaurante]:
    stmt = select(Restaurante)
    for columna, termino in (
        (Restaurante.texto_busqueda, q),
        (Restaurante.ubicacion_busqueda, zona),
    ):
        normalizado = normalizar_texto(termino) if termino else ""
        if normalizado:
            stmt = stmt.where(columna.contains(normalizado, autoescape=True))
    if categorias:
        stmt = stmt.where(Restaurante.categoria.in_(list(categorias)))
    if precio is not None:
        stmt = stmt.where(Restaurante.precio_nivel == precio)
    if rating_min is not None:
        stmt = stmt.where(Restaurante.rating >= rating_min)
    stmt = stmt.order_by(
        Restaurante.popular.desc(), Restaurante.rating.desc(), Restaurante.id.asc()
    )
    return list(db.scalars(stmt))


def obtener_restaurante(db: Session, slug: str) -> Restaurante | None:
    return db.scalar(select(Restaurante).where(Restaurante.slug == slug))
