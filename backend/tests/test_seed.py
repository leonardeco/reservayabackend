from sqlalchemy import func, select

from app.models import HorarioTurno, Mesa, Restaurante
from seeds.seed import MESAS, sembrar


def _contar(db, modelo):
    return db.scalar(select(func.count()).select_from(modelo))


def test_seed_crea_mesas_y_turnos_sin_duplicar(db_session):
    sembrar(db_session)
    mesas, turnos = _contar(db_session, Mesa), _contar(db_session, HorarioTurno)
    assert mesas == 5 * len(MESAS)
    assert turnos > 0
    sembrar(db_session)
    assert _contar(db_session, Mesa) == mesas
    assert _contar(db_session, HorarioTurno) == turnos
    assert _contar(db_session, Restaurante) == 5


def test_seed_respeta_dias_de_hogarenos(db_session):
    sembrar(db_session)
    hogarenos = db_session.scalar(
        select(Restaurante).where(Restaurante.slug == "hogarenos-comida-saludable")
    )
    dias = sorted(
        db_session.scalars(
            select(HorarioTurno.dia_semana).where(HorarioTurno.restaurante_id == hogarenos.id)
        )
    )
    assert dias == [0, 1, 2, 3, 4]


def test_seed_no_pisa_el_perfil_editado(db_session):
    sembrar(db_session)
    terraza = db_session.scalar(select(Restaurante).where(Restaurante.slug == "la-terraza"))
    terraza.nombre = "La Terraza Gourmet"
    db_session.commit()
    sembrar(db_session)
    db_session.expire_all()
    assert db_session.get(Restaurante, terraza.id).nombre == "La Terraza Gourmet"
