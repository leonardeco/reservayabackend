import pytest
from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table, insert
from sqlalchemy.exc import IntegrityError


def test_sqlite_activa_fk_y_savepoints(engine):
    if engine.dialect.name != "sqlite":
        pytest.skip("receta específica de SQLite")
    metadata = MetaData()
    padre = Table("t_padre", metadata, Column("id", Integer, primary_key=True))
    hijo = Table(
        "t_hijo",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("padre_id", Integer, ForeignKey("t_padre.id")),
    )
    metadata.create_all(engine)
    try:
        with engine.connect() as conn:
            assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(insert(padre).values(id=1))
                with pytest.raises(IntegrityError):
                    with conn.begin_nested():
                        conn.execute(insert(hijo).values(id=1, padre_id=99))
                conn.execute(insert(hijo).values(id=2, padre_id=1))
            assert conn.exec_driver_sql("SELECT count(*) FROM t_hijo").scalar() == 1
    finally:
        metadata.drop_all(engine)
