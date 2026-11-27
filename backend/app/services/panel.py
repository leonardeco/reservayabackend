from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Mesa, Restaurante
from app.schemas.panel import Perfil, PerfilActualizar


class PanelService:
    """Todo lo que ve y cambia el administrador, siempre limitado a su restaurante."""

    def __init__(self, db: Session, restaurante: Restaurante) -> None:
        self.db = db
        self.restaurante = restaurante

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
