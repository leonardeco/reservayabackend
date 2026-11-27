from datetime import date, time

import pytest

from app.core.reloj import get_ahora
from app.models import Mesa, Restaurante
from tests.datos import AHORA, CLAVE, LUNES, MARTES, crear_admin, crear_reserva, crear_restaurante

BASE = "/api/v1/admin"


@pytest.fixture
def restaurante(db_session):
    return crear_restaurante(db_session, slug="la-terraza", nombre="La Terraza")


@pytest.fixture
def otro(db_session):
    return crear_restaurante(db_session, slug="otro", nombre="Otro")


@pytest.fixture
def panel(client, restaurante, db_session):
    """Cliente con sesión iniciada como administrador de La Terraza."""
    crear_admin(db_session, restaurante, usuario="laterraza")
    client.app.dependency_overrides[get_ahora] = lambda: AHORA
    token = client.post(
        "/api/v1/auth/login", json={"usuario": "La Terraza", "password": CLAVE}
    ).json()["token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


# --- HU04: reservas del día ---------------------------------------------------------------


def test_reservas_del_dia_y_resumen(panel, restaurante, otro, db_session):
    crear_reserva(db_session, restaurante, "M2", hora=time(20, 30), nombre="María López")
    crear_reserva(db_session, restaurante, "M1", hora=time(19, 0), estado="pendiente")
    crear_reserva(db_session, restaurante, "M1", hora=time(20, 30), estado="cancelada")
    crear_reserva(db_session, otro, "M1")  # de otro restaurante: no se ve

    cuerpo = panel.get(f"{BASE}/reservas", params={"fecha": MARTES.isoformat()}).json()
    assert cuerpo["fecha"] == "2026-11-10"
    assert cuerpo["resumen"] == {
        "reservas_hoy": 2,
        "mesas_totales": 2,
        "mesas_disponibles": 0,
        "ocupacion": 100,
        "pendientes": 1,
    }
    filas = [(r["hora"], r["mesa"], r["estado"]) for r in cuerpo["reservas"]]
    assert filas == [
        ("19:00", "M1", "Pendiente"),
        ("20:30", "M2", "Confirmada"),
        ("20:30", "M1", "Cancelada"),
    ]
    assert set(cuerpo["reservas"][1]) == {
        "id",
        "codigo",
        "cliente",
        "telefono",
        "correo",
        "hora",
        "personas",
        "mesa",
        "estado",
        "notas",
    }
    assert cuerpo["reservas"][1]["cliente"] == "María López"


def test_sin_fecha_usa_hoy(panel, restaurante, db_session):
    crear_reserva(db_session, restaurante, "M1", fecha=LUNES, hora=time(19, 0))
    cuerpo = panel.get(f"{BASE}/reservas").json()
    assert cuerpo["fecha"] == "2026-11-09"
    assert cuerpo["resumen"]["reservas_hoy"] == 1
    assert cuerpo["resumen"]["ocupacion"] == 50


def test_confirmar_y_cancelar(panel, restaurante, db_session):
    reserva = crear_reserva(db_session, restaurante, estado="pendiente")
    url = f"{BASE}/reservas/{reserva.id}"

    r = panel.patch(url, json={"estado": "Confirmada"})
    assert r.status_code == 200 and r.json()["estado"] == "Confirmada"
    assert panel.patch(url, json={"estado": "Cancelada"}).json()["estado"] == "Cancelada"

    r = panel.patch(url, json={"estado": "Confirmada"})
    assert r.status_code == 409 and r.json() == {"detail": "cambio_de_estado_invalido"}
    assert panel.patch(url, json={"estado": "Pendiente"}).status_code == 422


def test_no_toca_reservas_ajenas(panel, otro, db_session):
    ajena = crear_reserva(db_session, otro)
    r = panel.patch(f"{BASE}/reservas/{ajena.id}", json={"estado": "Cancelada"})
    assert r.status_code == 404 and r.json() == {"detail": "reserva_no_encontrada"}
    assert panel.patch(f"{BASE}/reservas/999", json={"estado": "Cancelada"}).status_code == 404


# --- HU04: estadísticas -------------------------------------------------------------------


def test_estadisticas(panel, restaurante, db_session):
    # Semana del lunes 9 al domingo 15 de noviembre de 2026.
    crear_reserva(db_session, restaurante, "M1", fecha=LUNES, hora=time(19, 0))
    crear_reserva(db_session, restaurante, "M1", fecha=MARTES, hora=time(19, 0))
    crear_reserva(db_session, restaurante, "M2", fecha=MARTES, hora=time(20, 30))
    crear_reserva(db_session, restaurante, "M2", fecha=MARTES, estado="cancelada")
    crear_reserva(db_session, restaurante, "M1", fecha=date(2026, 11, 30), hora=time(20, 30))
    crear_reserva(db_session, restaurante, "M1", fecha=date(2026, 12, 1))  # otro mes

    cuerpo = panel.get(f"{BASE}/estadisticas").json()
    assert cuerpo["reservas_mes"] == 4
    assert cuerpo["calificacion"] == 4.5
    assert cuerpo["ocupacion_semanal"] == [
        {"dia": "Lun", "porcentaje": 50},
        {"dia": "Mar", "porcentaje": 100},
        {"dia": "Mié", "porcentaje": 0},
        {"dia": "Jue", "porcentaje": 0},
        {"dia": "Vie", "porcentaje": 0},
        {"dia": "Sáb", "porcentaje": 0},
        {"dia": "Dom", "porcentaje": 0},
    ]
    assert cuerpo["ocupacion_promedio"] == 21
    assert cuerpo["franjas"] == [
        {"hora": "19:00", "reservas": 2},
        {"hora": "20:30", "reservas": 2},
    ]


def test_estadisticas_sin_mesas_no_divide_por_cero(panel, restaurante, db_session):
    for m in db_session.query(Mesa).filter_by(restaurante_id=restaurante.id):
        m.activa = False
    db_session.commit()
    cuerpo = panel.get(f"{BASE}/estadisticas").json()
    assert cuerpo["ocupacion_promedio"] == 0 and cuerpo["franjas"] == []


# --- HU05: perfil del restaurante ---------------------------------------------------------

PERFIL_NUEVO = {
    "nombre": "La Terraza Gourmet",
    "categoria": "Italiana",
    "descripcion": "Nueva carta de temporada.",
    "direccion": "Laureles, Medellín",
    "telefono": "+57 604 111 2233",
    "web": "laterraza.co",
    "horario": "Lun-Dom 12:00-23:00",
    "capacidad": 99,
    "precio": "$$$",
    "imagen": "https://ejemplo.com/nueva.jpg",
}


def test_ver_perfil(panel):
    assert panel.get(f"{BASE}/restaurante").json() == {
        "nombre": "La Terraza",
        "categoria": "Italiana",
        "descripcion": "d",
        "direccion": "El Poblado, Medellín",
        "telefono": "t",
        "web": "p",
        "horario": "h",
        "capacidad": 2,
        "precio": "$$",
        "imagen": "https://ejemplo.com/a.jpg",
    }


def test_guardar_perfil_persiste(panel, restaurante, db_session):
    r = panel.put(f"{BASE}/restaurante", json=PERFIL_NUEVO)
    assert r.status_code == 200
    assert r.json() == PERFIL_NUEVO | {"capacidad": 2}  # la capacidad no se edita aquí

    db_session.expire_all()
    guardado = db_session.get(Restaurante, restaurante.id)
    assert guardado.nombre == "La Terraza Gourmet"
    assert guardado.precio_nivel == 3
    assert guardado.slug == "la-terraza"

    # El cambio se ve en el catálogo público y en la búsqueda.
    publico = panel.get("/api/v1/restaurantes/la-terraza").json()
    assert publico["nombre"] == "La Terraza Gourmet" and publico["ubicacion"].startswith("Laureles")
    encontrados = panel.get("/api/v1/restaurantes", params={"q": "gourmet"}).json()
    assert [e["slug"] for e in encontrados] == ["la-terraza"]


@pytest.mark.parametrize(
    "cambio",
    [
        {"precio": "$$$$"},
        {"imagen": "no-es-url"},
        {"nombre": " "},
        {"descripcion": "x" * 1001},
    ],
)
def test_perfil_valida_datos(panel, cambio):
    assert panel.put(f"{BASE}/restaurante", json=PERFIL_NUEVO | cambio).status_code == 422
