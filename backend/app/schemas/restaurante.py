from pydantic import BaseModel, ConfigDict


class RestauranteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    nombre: str
    descripcion: str
    ubicacion: str
    imagen_url: str
    imagen_comida_url: str
    rating: float
    precio_nivel: int
    categoria: str
    horario_resumen: str
    telefono: str
    pagina: str
    popular: bool
