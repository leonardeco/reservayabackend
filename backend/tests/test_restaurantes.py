import pytest

from seeds.seed import sembrar


@pytest.fixture
def catalogo(db_session):
    sembrar(db_session)


def slugs(response):
    assert response.status_code == 200
    return [r["slug"] for r in response.json()]


def test_lista_los_cinco_ordenados(client, catalogo):
    assert slugs(client.get("/api/v1/restaurantes")) == [
        "la-terraza",
        "casa-del-mar",
        "hogarenos-comida-saludable",
        "sushi-osaka",
        "el-fogon-paisa",
    ]


def test_filtro_categoria_multiple(client, catalogo):
    r = client.get(
        "/api/v1/restaurantes", params=[("categoria", "Colombiana"), ("categoria", "Japonesa")]
    )
    assert slugs(r) == ["hogarenos-comida-saludable", "sushi-osaka", "el-fogon-paisa"]


def test_busqueda_insensible_a_tildes_y_mayusculas(client, catalogo):
    assert slugs(client.get("/api/v1/restaurantes", params={"q": "FOGON"})) == ["el-fogon-paisa"]
    assert slugs(client.get("/api/v1/restaurantes", params={"zona": "belén"})) == [
        "hogarenos-comida-saludable"
    ]


def test_filtros_combinados(client, catalogo):
    r = client.get(
        "/api/v1/restaurantes",
        params={"categoria": "Colombiana", "precio": 1, "q": "saludable"},
    )
    assert slugs(r) == ["hogarenos-comida-saludable"]


def test_precio_y_rating_minimo(client, catalogo):
    assert slugs(client.get("/api/v1/restaurantes", params={"precio": 3})) == ["sushi-osaka"]
    assert slugs(client.get("/api/v1/restaurantes", params={"rating_min": 4.6})) == [
        "la-terraza",
        "casa-del-mar",
    ]


def test_comodines_like_se_escapan(client, catalogo):
    assert slugs(client.get("/api/v1/restaurantes", params={"q": "%"})) == []


def test_parametros_invalidos_422(client, catalogo):
    assert client.get("/api/v1/restaurantes", params={"precio": 4}).status_code == 422
    assert client.get("/api/v1/restaurantes", params={"rating_min": 6}).status_code == 422


def test_detalle_por_slug(client, catalogo):
    r = client.get("/api/v1/restaurantes/hogarenos-comida-saludable")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["nombre"] == "Hogareños: Comida saludable"
    assert cuerpo["horario_resumen"] == "Lun-Vie 08:00-15:00"
    assert "texto_busqueda" not in cuerpo


def test_detalle_inexistente_404(client, catalogo):
    r = client.get("/api/v1/restaurantes/no-existe")
    assert r.status_code == 404
    assert r.json() == {"detail": "restaurante_no_encontrado"}


def test_slug_invalido_422(client, catalogo):
    assert client.get("/api/v1/restaurantes/La_Terraza").status_code == 422


def test_seed_idempotente(db_session):
    assert sembrar(db_session) == 5
    assert sembrar(db_session) == 5
    from sqlalchemy import func, select

    from app.models import Restaurante

    assert db_session.scalar(select(func.count()).select_from(Restaurante)) == 5


def test_zona_filtra_solo_por_ubicacion(client, catalogo):
    assert slugs(client.get("/api/v1/restaurantes", params={"zona": "pasta"})) == []
    assert slugs(client.get("/api/v1/restaurantes", params={"zona": "poblado"})) == ["la-terraza"]


def test_indice_se_recalcula_al_editar(client, catalogo, db_session):
    from sqlalchemy import select

    from app.models import Restaurante

    r = db_session.scalar(select(Restaurante).where(Restaurante.slug == "sushi-osaka"))
    r.nombre = "Ramen Kioto"
    r.ubicacion = "Envigado, Medellín"
    db_session.commit()
    assert slugs(client.get("/api/v1/restaurantes", params={"q": "kioto"})) == ["sushi-osaka"]
    assert "sushi-osaka" in slugs(client.get("/api/v1/restaurantes", params={"zona": "envigado"}))


def test_rechaza_caracteres_de_control_y_categorias_largas(client, catalogo):
    assert client.get("/api/v1/restaurantes", params={"q": "a\x00b"}).status_code == 422
    assert client.get("/api/v1/restaurantes", params={"categoria": "x" * 41}).status_code == 422
