import os
from collections.abc import Iterator
from pathlib import Path

# Antes de importar app: el engine global nunca debe apuntar a la BD de desarrollo (.env).
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or "sqlite://"

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.core.config import normalize_database_url
from app.db.base import Base
from app.db.session import build_engine
from app.deps import get_db
from app.main import create_app

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _es_postgres() -> bool:
    return os.environ.get("TEST_DATABASE_URL", "").startswith("postgres")


def pytest_collection_modifyitems(config, items):
    if _es_postgres():
        return
    skip = pytest.mark.skip(reason="requiere TEST_DATABASE_URL de PostgreSQL")
    for item in items:
        if "postgres" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def database_url(tmp_path_factory) -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        # La limpieza borra todas las filas: solo se permite contra una BD de pruebas.
        nombre = make_url(normalize_database_url(url)).database or ""
        assert nombre.endswith("_test"), (
            f"TEST_DATABASE_URL debe apuntar a una BD *_test, no {nombre!r}"
        )
        return normalize_database_url(url)
    return f"sqlite:///{(tmp_path_factory.mktemp('db') / 'test.db').as_posix()}"


@pytest.fixture(scope="session")
def engine(database_url: str) -> Iterator[Engine]:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.attributes["url"] = database_url
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")
    eng = build_engine(database_url)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _limpiar_tablas(engine: Engine) -> Iterator[None]:
    """Deja la BD vacía tras cada test, aunque el test use el engine directamente (hilos)."""
    yield
    tablas = list(reversed(Base.metadata.sorted_tables))
    if not tablas:
        return
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            nombres = ", ".join(f'"{t.name}"' for t in tablas)
            conn.execute(text(f"TRUNCATE {nombres} RESTART IDENTITY CASCADE"))
        else:
            for table in tablas:
                conn.execute(table.delete())


@pytest.fixture
def db_session(session_factory: sessionmaker) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session, session_factory: sessionmaker) -> Iterator[TestClient]:
    def _get_db() -> Iterator[Session]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as test_client:
        yield test_client
