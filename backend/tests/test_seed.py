from datetime import date

from sqlalchemy import func, select

from app.core.seguridad import HashContrasena
from app.models import Administrador, HorarioTurno, Mesa, Reserva, Restaurante
from seeds.seed import ADMIN_DEMO, MESAS, RESERVAS_HOY, sembrar

HOY = date(2026, 11, 11)  # miércoles


def _contar(db, modelo):
    return db.scalar(select(func.count()).select_from(modelo))


def test_seed_crea_mesas_y_turnos_sin_duplicar(db_session):
    sembrar(db_session, hoy=HOY)
    mesas, turnos = _contar(db_session, Mesa), _contar(db_session, HorarioTurno)
    reservas = _contar(db_session, Reserva)
    assert mesas == 5 * len(MESAS)
    assert turnos > 0
    sembrar(db_session, hoy=HOY)
    assert _contar(db_session, Mesa) == mesas
    assert _contar(db_session, HorarioTurno) == turnos
    assert _contar(db_session, Restaurante) == 5
    assert _contar(db_session, Administrador) == 1
    assert _contar(db_session, Reserva) == reservas


def test_seed_respeta_dias_de_hogarenos(db_session):
    sembrar(db_session, hoy=HOY)
    hogarenos = db_session.scalar(
        select(Restaurante).where(Restaurante.slug == "hogarenos-comida-saludable")
    )
    dias = sorted(
        db_session.scalars(
            select(HorarioTurno.dia_semana).where(HorarioTurno.restaurante_id == hogarenos.id)
        )
    )
    assert dias == [0, 1, 2, 3, 4]


def test_seed_crea_admin_de_la_terraza(db_session):
    sembrar(db_session, hoy=HOY)
    admin = db_session.scalar(select(Administrador))
    terraza = db_session.get(Restaurante, admin.restaurante_id)
    assert admin.usuario == ADMIN_DEMO["usuario"] and terraza.slug == "la-terraza"
    assert HashContrasena.verificar(ADMIN_DEMO["password"], admin.password_hash)


def test_seed_reservas_demo_para_el_panel(db_session):
    sembrar(db_session, hoy=HOY)
    de_hoy = db_session.scalars(select(Reserva).where(Reserva.fecha == HOY)).all()
    assert len(de_hoy) == len(RESERVAS_HOY)
    fechas = set(db_session.scalars(select(Reserva.fecha)))
    assert min(fechas) == date(2026, 11, 1)
    assert max(fechas) == date(2026, 11, 15)  # hasta el domingo de esta semana


def test_seed_no_pisa_el_perfil_editado(db_session):
    sembrar(db_session, hoy=HOY)
    terraza = db_session.scalar(select(Restaurante).where(Restaurante.slug == "la-terraza"))
    terraza.nombre = "La Terraza Gourmet"
    db_session.commit()
    sembrar(db_session, hoy=HOY)
    db_session.expire_all()
    assert db_session.get(Restaurante, terraza.id).nombre == "La Terraza Gourmet"
