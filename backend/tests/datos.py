"""Datos de prueba compartidos por los tests de reservas y del panel."""

from datetime import UTC, date, datetime, time

from app.core.seguridad import HashContrasena
from app.models import Administrador, HorarioTurno, Mesa, Reserva, Restaurante

# Lunes 9 nov 2026, 10:00 en Bogotá (UTC-5).
AHORA = datetime(2026, 11, 9, 15, 0, tzinfo=UTC)
LUNES = date(2026, 11, 9)
MARTES = date(2026, 11, 10)
MIERCOLES = date(2026, 11, 11)
CLAVE = "terraza123"


def crear_restaurante(db, slug="prueba", nombre="Prueba", dias=(0, 1)) -> Restaurante:
    """Atiende los días indicados de 19:00 a 20:30, con dos mesas: M1 (1-2) y M2 (2-4)."""
    r = Restaurante(
        slug=slug,
        nombre=nombre,
        descripcion="d",
        ubicacion="El Poblado, Medellín",
        imagen_url="https://ejemplo.com/a.jpg",
        imagen_comida_url="https://ejemplo.com/b.jpg",
        rating=4.5,
        precio_nivel=2,
        categoria="Italiana",
        horario_resumen="h",
        telefono="t",
        pagina="p",
        popular=False,
    )
    db.add(r)
    db.flush()
    for dia in dias:
        db.add(
            HorarioTurno(
                restaurante_id=r.id,
                dia_semana=dia,
                apertura=time(19, 0),
                ultima_franja=time(20, 30),
            )
        )
    db.add_all(
        [
            Mesa(restaurante_id=r.id, etiqueta="M1", capacidad_min=1, capacidad_max=2, activa=True),
            Mesa(restaurante_id=r.id, etiqueta="M2", capacidad_min=2, capacidad_max=4, activa=True),
        ]
    )
    db.commit()
    return r


def crear_admin(db, restaurante, usuario="prueba", clave=CLAVE, activo=True) -> Administrador:
    admin = Administrador(
        usuario=usuario,
        password_hash=HashContrasena.generar(clave),
        restaurante_id=restaurante.id,
        activo=activo,
    )
    db.add(admin)
    db.commit()
    return admin


def mesa(db, restaurante, etiqueta) -> Mesa:
    return db.query(Mesa).filter_by(restaurante_id=restaurante.id, etiqueta=etiqueta).one()


def crear_reserva(
    db, restaurante, etiqueta="M1", fecha=MARTES, hora=time(19, 0), estado="confirmada", **extra
) -> Reserva:
    datos = {
        "codigo": f"RY-{fecha:%Y%m%d}-{1000 + db.query(Reserva).count()}",
        "restaurante_id": restaurante.id,
        "mesa_id": mesa(db, restaurante, etiqueta).id,
        "fecha": fecha,
        "hora": hora,
        "personas": 2,
        "nombre": "Juan García",
        "telefono": "+57 300 000 0001",
        "correo": "juan@correo.com",
        "estado": estado,
    }
    datos.update(extra)
    reserva = Reserva(**datos)
    db.add(reserva)
    db.commit()
    return reserva
