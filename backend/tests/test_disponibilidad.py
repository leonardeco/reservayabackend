from datetime import UTC, date, datetime, time

import pytest

from app.core.reloj import get_ahora
from app.models import BloqueoFecha, HorarioTurno, Mesa, Restaurante
from app.services.disponibilidad import calcular_disponibilidad, generar_franjas

# Lunes 9 nov 2026, 10:00 en Bogotá (UTC-5).
AHORA = datetime(2026, 11, 9, 15, 0, tzinfo=UTC)
MARTES = date(2026, 11, 10)
URL = "/api/v1/restaurantes/prueba/disponibilidad"


@pytest.fixture
def restaurante(db_session):
    r = Restaurante(
        slug="prueba",
        nombre="Prueba",
        descripcion="d",
        ubicacion="u",
        imagen_url="i",
        imagen_comida_url="i",
        rating=4.0,
        precio_nivel=2,
        categoria="Italiana",
        horario_resumen="h",
        telefono="t",
        pagina="p",
        popular=False,
        zona_horaria="America/Bogota",
        duracion_franja_min=90,
        antelacion_max_dias=60,
        texto_busqueda="prueba",
    )
    db_session.add(r)
    db_session.flush()
    db_session.add_all(
        [
            HorarioTurno(
                restaurante_id=r.id, dia_semana=1, apertura=time(19, 0), ultima_franja=time(20, 30)
            ),
            Mesa(restaurante_id=r.id, etiqueta="M1", capacidad_min=1, capacidad_max=2, activa=True),
            Mesa(restaurante_id=r.id, etiqueta="M2", capacidad_min=2, capacidad_max=4, activa=True),
        ]
    )
    db_session.commit()
    return r


@pytest.fixture
def api(client):
    client.app.dependency_overrides[get_ahora] = lambda: AHORA
    return client


def consultar(api, fecha=MARTES, personas=2):
    return api.get(URL, params={"fecha": fecha.isoformat(), "personas": personas})


def test_franjas_libres(api, restaurante):
    r = consultar(api)
    assert r.status_code == 200
    assert r.json() == {
        "fecha": "2026-11-10",
        "personas": 2,
        "franjas": [{"hora": "19:00", "estado": "libre"}, {"hora": "20:30", "estado": "libre"}],
        "motivo": None,
        "mensaje": None,
    }


def test_dia_sin_turno_cerrado(api, restaurante):
    cuerpo = consultar(api, fecha=date(2026, 11, 11)).json()
    assert cuerpo["franjas"] == [] and cuerpo["motivo"] == "cerrado"


def test_bloqueo_dia_completo(api, restaurante, db_session):
    db_session.add(
        BloqueoFecha(restaurante_id=restaurante.id, fecha=MARTES, motivo="Evento privado")
    )
    db_session.commit()
    cuerpo = consultar(api).json()
    assert cuerpo["franjas"] == []
    assert cuerpo["motivo"] == "bloqueado" and cuerpo["mensaje"] == "Evento privado"


def test_bloqueo_parcial(api, restaurante, db_session):
    db_session.add(
        BloqueoFecha(
            restaurante_id=restaurante.id,
            fecha=MARTES,
            hora_desde=time(20, 0),
            hora_hasta=time(21, 0),
            motivo="Mantenimiento",
        )
    )
    db_session.commit()
    assert [f["hora"] for f in consultar(api).json()["franjas"]] == ["19:00"]


def test_fecha_pasada_o_lejana_422(api, restaurante):
    assert consultar(api, fecha=date(2026, 11, 8)).json() == {"detail": "fecha_fuera_de_rango"}
    assert consultar(api, fecha=date(2026, 11, 8)).status_code == 422
    assert consultar(api, fecha=date(2027, 1, 8)).status_code == 200
    assert consultar(api, fecha=date(2027, 1, 9)).status_code == 422


def test_hoy_omite_franjas_ya_iniciadas(client, restaurante):
    # Martes 10 nov 19:30 en Bogotá = 11 nov 00:30 UTC.
    client.app.dependency_overrides[get_ahora] = lambda: datetime(2026, 11, 11, 0, 30, tzinfo=UTC)
    horas = [f["hora"] for f in consultar(client).json()["franjas"]]
    assert horas == ["20:30"]


def test_grupo_grande_todo_agotado(api, restaurante):
    cuerpo = consultar(api, personas=5).json()
    assert cuerpo["motivo"] == "grupo_grande"
    assert {f["estado"] for f in cuerpo["franjas"]} == {"agotada"}


def test_validaciones(api, restaurante):
    assert consultar(api, personas=0).status_code == 422
    assert consultar(api, personas=21).status_code == 422
    r = api.get(
        "/api/v1/restaurantes/no-existe/disponibilidad",
        params={"fecha": "2026-11-10", "personas": 2},
    )
    assert r.status_code == 404


def test_listado_con_fecha_y_personas(api, restaurante):
    url = "/api/v1/restaurantes"
    martes = {"fecha": MARTES.isoformat(), "personas": 2}
    assert [r["slug"] for r in api.get(url, params=martes).json()] == ["prueba"]
    miercoles = {"fecha": "2026-11-11", "personas": 2}  # ese día no atiende
    assert api.get(url, params=miercoles).json() == []
    assert api.get(url, params={"personas": 2}).status_code == 422


def test_ocupadas_agotan_la_franja(db_session, restaurante):
    mesas = {
        m.etiqueta: m.id for m in db_session.query(Mesa).filter_by(restaurante_id=restaurante.id)
    }
    resultado = calcular_disponibilidad(
        db_session,
        restaurante,
        MARTES,
        2,
        AHORA,
        ocupadas={time(19, 0): {mesas["M1"], mesas["M2"]}, time(20, 30): {mesas["M1"]}},
    )
    assert [(f.hora, f.estado) for f in resultado.franjas] == [
        (time(19, 0), "agotada"),
        (time(20, 30), "libre"),
    ]


def test_generar_franjas_une_turnos():
    turnos = [
        HorarioTurno(dia_semana=0, apertura=time(12, 0), ultima_franja=time(14, 0)),
        HorarioTurno(dia_semana=0, apertura=time(19, 0), ultima_franja=time(19, 0)),
    ]
    assert generar_franjas(turnos, 60) == [time(12, 0), time(13, 0), time(14, 0), time(19, 0)]
