import pytest

from app.core.reloj import get_ahora
from app.models import Restaurante
from tests.datos import AHORA, CLAVE, crear_admin, crear_restaurante

BASE = "/api/v1/admin"


@pytest.fixture
def restaurante(db_session):
    return crear_restaurante(db_session, slug="la-terraza", nombre="La Terraza")


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
