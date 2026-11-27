from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings


def build_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False})

        @event.listens_for(engine, "connect")
        def _sqlite_on_connect(dbapi_connection, _connection_record):
            # pysqlite gestiona mal BEGIN/SAVEPOINT: SQLAlchemy emite BEGIN explícito
            # (receta oficial) y se activan las claves foráneas.
            dbapi_connection.isolation_level = None
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        @event.listens_for(engine, "begin")
        def _sqlite_on_begin(connection):
            connection.exec_driver_sql("BEGIN")

        return engine
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_recycle=300,
        # Neon puede tardar en despertar: sin timeout /health quedaría colgado.
        connect_args={"connect_timeout": 5},
    )


engine = build_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
