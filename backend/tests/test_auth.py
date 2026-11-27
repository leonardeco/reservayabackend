from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.reloj import get_ahora
from app.core.seguridad import FirmadorTokens, HashContrasena, TokenInvalido
from app.deps import AdminActual
from app.services.auth import normalizar_usuario
from tests.datos import AHORA, CLAVE, crear_admin, crear_restaurante

LOGIN = "/api/v1/auth/login"
# Ruta de prueba protegida con AdminActual: así se revisa el token sin depender del panel.
PROTEGIDA = "/prueba/protegida"


@pytest.fixture
def restaurante(db_session):
    return crear_restaurante(db_session, slug="la-terraza", nombre="La Terraza")


@pytest.fixture
def api(client):
    client.app.dependency_overrides[get_ahora] = lambda: AHORA

    @client.app.get(PROTEGIDA)
    def _protegida(admin: AdminActual):
        return {"usuario": admin.usuario}

    return client


def entrar(api, usuario="La Terraza", password=CLAVE):
    return api.post(LOGIN, json={"usuario": usuario, "password": password})


def test_login_correcto_devuelve_token(api, restaurante, db_session):
    crear_admin(db_session, restaurante, usuario="laterraza")
    r = entrar(api)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["tipo"] == "Bearer" and cuerpo["token"].count(".") == 1
    assert cuerpo["usuario"] == "laterraza"
    assert cuerpo["restaurante"] == "La Terraza" and cuerpo["slug"] == "la-terraza"
    assert cuerpo["vence"].startswith("2026-11-09T23:00:00")  # 8 horas después


@pytest.mark.parametrize("usuario", ["La Terraza", "la terraza", "laterraza", " LaTerraza "])
def test_usuario_sin_importar_mayusculas_ni_espacios(api, restaurante, db_session, usuario):
    crear_admin(db_session, restaurante, usuario="laterraza")
    assert entrar(api, usuario=usuario).status_code == 200


def test_credenciales_incorrectas(api, restaurante, db_session):
    crear_admin(db_session, restaurante, usuario="laterraza")
    for usuario, clave in (("La Terraza", "otra"), ("nadie", CLAVE)):
        r = entrar(api, usuario, clave)
        assert r.status_code == 401
        assert r.json() == {"detail": "credenciales_invalidas"}


def test_administrador_inactivo_no_entra(api, restaurante, db_session):
    crear_admin(db_session, restaurante, usuario="laterraza", activo=False)
    assert entrar(api).status_code == 401


def test_login_valida_campos(api, restaurante):
    assert api.post(LOGIN, json={"usuario": "", "password": "x"}).status_code == 422
    assert api.post(LOGIN, json={"usuario": "x"}).status_code == 422


def test_ruta_protegida_exige_token(api, restaurante, db_session):
    crear_admin(db_session, restaurante, usuario="laterraza")
    assert api.get(PROTEGIDA).json() == {"detail": "no_autenticado"}
    assert api.get(PROTEGIDA).status_code == 401
    malo = {"Authorization": "Bearer basura"}
    assert api.get(PROTEGIDA, headers=malo).status_code == 401

    token = entrar(api).json()["token"]
    assert api.get(PROTEGIDA, headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_token_vencido_o_alterado(api, restaurante, db_session):
    crear_admin(db_session, restaurante, usuario="laterraza")
    token = entrar(api).json()["token"]
    cuerpo, firma = token.split(".")
    alterado = f"{cuerpo}x.{firma}"
    assert api.get(PROTEGIDA, headers={"Authorization": f"Bearer {alterado}"}).status_code == 401

    api.app.dependency_overrides[get_ahora] = lambda: AHORA + timedelta(hours=9)
    assert api.get(PROTEGIDA, headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_de_admin_desactivado(api, restaurante, db_session):
    admin = crear_admin(db_session, restaurante, usuario="laterraza")
    token = entrar(api).json()["token"]
    admin.activo = False
    db_session.commit()
    assert api.get(PROTEGIDA, headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_hash_de_contrasena():
    guardado = HashContrasena.generar("secreta")
    assert guardado.startswith("pbkdf2_sha256$200000$")
    assert HashContrasena.verificar("secreta", guardado)
    assert not HashContrasena.verificar("otra", guardado)
    assert guardado != HashContrasena.generar("secreta")  # sal distinta cada vez
    assert not HashContrasena.verificar("secreta", "mal-formado")
    assert not HashContrasena.verificar("secreta", "md5$1$a$b")


def test_firmador_rechaza_tokens_raros():
    firmador = FirmadorTokens("clave-de-prueba")
    otro = FirmadorTokens("otra-clave")
    token = firmador.emitir(1, 2, AHORA)
    assert firmador.leer(token, AHORA)["rid"] == 2
    for malo in ("sin-punto", otro.emitir(1, 2, AHORA)):
        with pytest.raises(TokenInvalido):
            firmador.leer(malo, AHORA)


def test_normalizar_usuario():
    assert normalizar_usuario("  Hogareños Saludable ") == "hogarenossaludable"


def test_produccion_exige_secret_key():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, env="prod")
    with pytest.raises(ValidationError):
        Settings(_env_file=None, env="prod", secret_key="corta")
    assert Settings(_env_file=None, env="prod", secret_key="x" * 32).env == "prod"
