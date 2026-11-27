from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext

from app.db.base import Base


def test_modelos_coinciden_con_migraciones(engine):
    with engine.connect() as connection:
        diferencias = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diferencias == []


def test_migraciones_suben_y_bajan(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    cfg = Config(str(backend / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend / "alembic"))
    cfg.attributes["url"] = f"sqlite:///{(tmp_path / 'ida_vuelta.db').as_posix()}"
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
