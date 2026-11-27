import re
from datetime import UTC, datetime, time

import pytest

from app.core.reloj import get_ahora
from app.models import BloqueoFecha, Reserva
from app.services import reservas as servicio_reservas
from tests.datos import AHORA, MARTES, MIERCOLES, crear_reserva, crear_restaurante

URL = "/api/v1/restaurantes/prueba/reservas"


@pytest.fixture
def restaurante(db_session):
    return crear_restaurante(db_session)


@pytest.fixture
def api(client):
    client.app.dependency_overrides[get_ahora] = lambda: AHORA
    return client


def reservar(api, **cambios):
    datos = {
        "fecha": MARTES.isoformat(),
        "hora": "19:00",
        "personas": 2,
        "nombre": "Juan García",
        "telefono": "+57 300 000 0001",
        "correo": "juan@correo.com",
        "notas": "Cumpleaños",
    }
    datos.update(cambios)
    return api.post(URL, json=datos)


def test_crea_reserva_con_codigo_y_mesa(api, restaurante, db_session):
    r = reservar(api)
    assert r.status_code == 201
    cuerpo = r.json()
    assert re.fullmatch(r"RY-20261110-\d{4}", cuerpo["codigo"])
    assert cuerpo | {"codigo": None} == {
        "codigo": None,
        "restaurante": "Prueba",
        "slug": "prueba",
        "ubicacion": "El Poblado, Medellín",
        "fecha": "2026-11-10",
        "hora": "19:00",
        "personas": 2,
        "mesa": "M1",
        "estado": "Confirmada",
        "nombre": "Juan García",
        "correo": "juan@correo.com",
    }
    guardada = db_session.query(Reserva).one()
    assert guardada.notas == "Cumpleaños" and guardada.estado == "confirmada"


def test_acepta_horas_del_front_dentro_del_horario(api, restaurante):
    # El front ofrece 19:30 aunque las franjas sean de 90 min: vale si está en el horario.
    assert reservar(api, hora="19:30").status_code == 201


def test_fuera_de_horario_o_dia_cerrado(api, restaurante):
    for cambios in ({"hora": "18:00"}, {"hora": "21:00"}, {"fecha": MIERCOLES.isoformat()}):
        r = reservar(api, **cambios)
        assert r.status_code == 409
        assert r.json() == {"detail": "fuera_de_horario"}


def test_hora_ya_pasada_hoy(client, restaurante):
    # Martes 10 nov 19:30 en Bogotá.
    client.app.dependency_overrides[get_ahora] = lambda: datetime(2026, 11, 11, 0, 30, tzinfo=UTC)
    assert reservar(client, hora="19:00").json() == {"detail": "fuera_de_horario"}
    assert reservar(client, hora="20:30").status_code == 201


def test_fecha_fuera_de_rango(api, restaurante):
    r = reservar(api, fecha="2026-11-08")
    assert r.status_code == 422 and r.json() == {"detail": "fecha_fuera_de_rango"}


def test_bloqueo_impide_reservar(api, restaurante, db_session):
    db_session.add(BloqueoFecha(restaurante_id=restaurante.id, fecha=MARTES, motivo="Evento"))
    db_session.commit()
    assert reservar(api).json() == {"detail": "fuera_de_horario"}


def test_sin_mesas_libres_409(api, restaurante):
    assert reservar(api).json()["mesa"] == "M1"
    assert reservar(api).json()["mesa"] == "M2"
    r = reservar(api)
    assert r.status_code == 409 and r.json() == {"detail": "sin_mesa_disponible"}
    # 20:00 se cruza con las de 19:00 (duran 90 min); 20:30 ya no.
    assert reservar(api, hora="20:00").status_code == 409
    assert reservar(api, hora="20:30").status_code == 201


def test_grupo_que_no_cabe(api, restaurante):
    assert reservar(api, personas=6).json() == {"detail": "sin_mesa_disponible"}


def test_reserva_cancelada_libera_la_mesa(api, restaurante, db_session):
    crear_reserva(db_session, restaurante, "M1", estado="cancelada")
    assert reservar(api).json()["mesa"] == "M1"


def test_validaciones_del_formulario(api, restaurante):
    malos = [
        {"personas": 0},
        {"personas": 21},
        {"nombre": "  "},
        {"telefono": "abc"},
        {"correo": "sin-arroba"},
        {"hora": "25:00"},
        {"extra": "no permitido"},
    ]
    for cambios in malos:
        assert reservar(api, **cambios).status_code == 422, cambios


def test_restaurante_inexistente(api, restaurante):
    datos = {
        "fecha": MARTES.isoformat(),
        "hora": "19:00",
        "personas": 2,
        "nombre": "Juan García",
        "telefono": "3000000001",
        "correo": "juan@correo.com",
    }
    r = api.post("/api/v1/restaurantes/no-existe/reservas", json=datos)
    assert r.status_code == 404 and r.json() == {"detail": "restaurante_no_encontrado"}


def test_disponibilidad_descuenta_reservas(api, restaurante, db_session):
    crear_reserva(db_session, restaurante, "M1")
    crear_reserva(db_session, restaurante, "M2")
    franjas = api.get(
        "/api/v1/restaurantes/prueba/disponibilidad",
        params={"fecha": MARTES.isoformat(), "personas": 2},
    ).json()["franjas"]
    assert franjas == [
        {"hora": "19:00", "estado": "agotada"},
        {"hora": "20:30", "estado": "libre"},
    ]


def test_listado_oculta_restaurantes_sin_disponibilidad(api, restaurante, db_session):
    crear_restaurante(db_session, slug="cerrado-martes", nombre="Cerrado", dias=(0,))
    todos = api.get("/api/v1/restaurantes").json()
    assert {r["slug"] for r in todos} == {"prueba", "cerrado-martes"}

    params = {"fecha": MARTES.isoformat(), "personas": 2}
    disponibles = api.get("/api/v1/restaurantes", params=params).json()
    assert [r["slug"] for r in disponibles] == ["prueba"]

    assert api.get("/api/v1/restaurantes", params={"personas": 2}).status_code == 422
    r = api.get("/api/v1/restaurantes", params={"fecha": "2026-11-01", "personas": 2})
    assert r.json() == {"detail": "fecha_fuera_de_rango"}


def test_codigo_repetido_se_vuelve_a_generar(db_session, restaurante, monkeypatch):
    crear_reserva(db_session, restaurante, codigo="RY-20261110-1000")
    valores = iter([0, 0, 1])
    monkeypatch.setattr(servicio_reservas.secrets, "randbelow", lambda _n: next(valores))
    servicio = servicio_reservas.ReservaService(db_session, AHORA)
    assert servicio._generar_codigo(MARTES) == "RY-20261110-1001"


def test_codigo_imposible_falla(db_session, restaurante, monkeypatch):
    crear_reserva(db_session, restaurante, codigo="RY-20261110-1000")
    monkeypatch.setattr(servicio_reservas.secrets, "randbelow", lambda _n: 0)
    servicio = servicio_reservas.ReservaService(db_session, AHORA)
    with pytest.raises(RuntimeError):
        servicio._generar_codigo(MARTES)


def test_hora_con_segundos_se_guarda_en_minutos(api, restaurante, db_session):
    assert reservar(api, hora="19:00:45").status_code == 201
    assert db_session.query(Reserva).one().hora == time(19, 0)
