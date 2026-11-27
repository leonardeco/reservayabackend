"""Siembra idempotente del catálogo inicial: python -m seeds.seed (desde backend/)."""

from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import HorarioTurno, Mesa, Restaurante
from app.services.restaurantes import actualizar_texto_busqueda

RESTAURANTES: list[dict] = [
    {
        "slug": "la-terraza",
        "nombre": "La Terraza",
        "descripcion": (
            "Pasta artesanal y ambiente acogedor en el corazón de la ciudad. "
            "Especialidad en risottos y carpaccios familiares."
        ),
        "ubicacion": "El Poblado, Medellín",
        "imagen_url": "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/05/c3/48/bb/cacio-pepe.jpg",
        "imagen_comida_url": "https://media.timeout.com/images/106123641/1024/576/image.webp",
        "rating": 4.8,
        "precio_nivel": 2,
        "categoria": "Italiana",
        "horario_resumen": "Lun-Vie 12:00-23:00 · Sáb-Dom 12:00-00:00",
        "telefono": "+57 604 234 5678",
        "pagina": "laterraza.com.co",
        "popular": True,
    },
    {
        "slug": "casa-del-mar",
        "nombre": "Casa del Mar",
        "descripcion": (
            "Mariscos frescos traídos diariamente. "
            "Ceviche y cazuelas son la especialidad de la casa."
        ),
        "ubicacion": "Envigado, Medellín",
        "imagen_url": "https://media.timeout.com/images/106152291/1024/576/image.webp",
        "imagen_comida_url": "https://media.timeout.com/images/106251281/1024/576/image.webp",
        "rating": 4.7,
        "precio_nivel": 2,
        "categoria": "Mariscos",
        "horario_resumen": "Lun-Sáb 12:00-23:00 · Dom 12:00-21:00",
        "telefono": "+57 604 777 3344",
        "pagina": "casadelmar.com",
        "popular": True,
    },
    {
        "slug": "hogarenos-comida-saludable",
        "nombre": "Hogareños: Comida saludable",
        "descripcion": (
            "Platos saludables y frescos para cuidar tu cuerpo. Es como sentirte en casa"
        ),
        "ubicacion": "Belén, Medellín",
        "imagen_url": (
            "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/07/5e/d9/57/"
            "jalisco-comida-mexicana.jpg?w=1000&h=-1&s=1"
        ),
        "imagen_comida_url": (
            "https://img.asmedia.epimg.net/resizer/v2/CRXKYYTDDFBZ3K6KBZWJ6FA7ME.png"
            "?auth=79f4814226afa19861a4d18cf9b98c35532df69ec9a534b9d8e0f388f4117867"
            "&width=360&height=203&smart=true"
        ),
        "rating": 4.5,
        "precio_nivel": 1,
        "categoria": "Colombiana",
        "horario_resumen": "Lun-Vie 08:00-15:00",
        "telefono": "+57 316 996 3103",
        "pagina": "hogarenos.com",
        "popular": True,
    },
    {
        "slug": "sushi-osaka",
        "nombre": "Sushi Osaka",
        "descripcion": (
            "Sushi fresco y rolls creativos en ambiente minimalista. "
            "Omakase disponible con reserva previa."
        ),
        "ubicacion": "Laureles, Medellín",
        "imagen_url": "https://media.timeout.com/images/106080189/1024/576/image.webp",
        "imagen_comida_url": (
            "https://images.unsplash.com/photo-1681270507609-e2a5f21969b0?crop=entropy"
            "&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzdXNoaSUy"
            "MGphcGFuZXNlJTIwb21ha2FzZSUyMHJlc3RhdXJhbnR8ZW58MXx8fHwxNzc4NTQ3NTUyfDA"
            "&ixlib=rb-4.1.0&q=80&w=300"
        ),
        "rating": 4.3,
        "precio_nivel": 3,
        "categoria": "Japonesa",
        "horario_resumen": "Lun-Sáb 12:00-23:00 · Dom 12:00-18:00",
        "telefono": "+57 604 998 7765",
        "pagina": "sushiosaka.com",
        "popular": False,
    },
    {
        "slug": "el-fogon-paisa",
        "nombre": "El Fogón Paisa",
        "descripcion": (
            "Sabores tradicionales en un ambiente familiar y auténtico. "
            "Bandeja paisa y sopas del día incluidas."
        ),
        "ubicacion": "Centro, Medellín",
        "imagen_url": "https://distritoch.com/wp-content/uploads/2025/01/IMG-20250408-WA0037-768x1024.webp",
        "imagen_comida_url": "https://vecinavegetariana.com/wp-content/uploads/2022/04/Bandeja-Paisa-4.jpeg",
        "rating": 4.1,
        "precio_nivel": 1,
        "categoria": "Colombiana",
        "horario_resumen": "Lun-Dom 11:00-22:00",
        "telefono": "+57 604 321 9876",
        "pagina": "elfogonpaisa.com.co",
        "popular": False,
    },
]


# (etiqueta, capacidad_min, capacidad_max): mismas mesas para cada restaurante de ejemplo.
MESAS: list[tuple[str, int, int]] = [
    ("Mesa 1", 1, 2),
    ("Mesa 2", 1, 2),
    ("Mesa 3", 2, 4),
    ("Mesa 4", 2, 4),
    ("Mesa 5", 3, 6),
    ("Mesa 6", 5, 8),
]

# slug -> [(días 0=lunes..6=domingo, apertura, última franja)] según el horario publicado.
TURNOS: dict[str, list[tuple[list[int], str, str]]] = {
    "la-terraza": [([0, 1, 2, 3, 4], "12:00", "21:30"), ([5, 6], "12:00", "22:30")],
    "casa-del-mar": [([0, 1, 2, 3, 4, 5], "12:00", "21:30"), ([6], "12:00", "19:30")],
    "hogarenos-comida-saludable": [([0, 1, 2, 3, 4], "08:00", "13:30")],
    "sushi-osaka": [([0, 1, 2, 3, 4, 5], "12:00", "21:30"), ([6], "12:00", "16:30")],
    "el-fogon-paisa": [([0, 1, 2, 3, 4, 5, 6], "11:00", "20:30")],
}


def _sembrar_mesas_y_turnos(db: Session, restaurante: Restaurante) -> None:
    existentes = set(db.scalars(select(Mesa.etiqueta).where(Mesa.restaurante_id == restaurante.id)))
    for etiqueta, minimo, maximo in MESAS:
        if etiqueta not in existentes:
            db.add(
                Mesa(
                    restaurante_id=restaurante.id,
                    etiqueta=etiqueta,
                    capacidad_min=minimo,
                    capacidad_max=maximo,
                    activa=True,
                )
            )
    tiene_turnos = db.scalar(
        select(HorarioTurno.id).where(HorarioTurno.restaurante_id == restaurante.id).limit(1)
    )
    if tiene_turnos is None:
        for dias, apertura, ultima in TURNOS.get(restaurante.slug, []):
            for dia in dias:
                db.add(
                    HorarioTurno(
                        restaurante_id=restaurante.id,
                        dia_semana=dia,
                        apertura=time.fromisoformat(apertura),
                        ultima_franja=time.fromisoformat(ultima),
                    )
                )


def sembrar(db: Session) -> int:
    for datos in RESTAURANTES:
        slug = datos["slug"]
        restaurante = db.scalar(select(Restaurante).where(Restaurante.slug == slug))
        if restaurante is None:
            restaurante = Restaurante(slug=slug)
            db.add(restaurante)
            # Solo al crear: si el administrador ya editó el perfil, no se pisa.
            for campo, valor in datos.items():
                setattr(restaurante, campo, valor)
        actualizar_texto_busqueda(restaurante)
        db.flush()
        _sembrar_mesas_y_turnos(db, restaurante)
    db.commit()
    return len(RESTAURANTES)


def main() -> None:
    with SessionLocal() as db:
        total = sembrar(db)
    print(f"Catálogo sembrado: {total} restaurantes")


if __name__ == "__main__":
    main()
