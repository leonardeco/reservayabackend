from app.core.config import Settings, normalize_database_url


def test_normaliza_postgres_url():
    assert normalize_database_url("postgres://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert (
        normalize_database_url("postgresql://u:p@h/db?sslmode=require")
        == "postgresql+psycopg://u:p@h/db?sslmode=require"
    )


def test_respeta_urls_ya_normalizadas_y_sqlite():
    assert normalize_database_url("postgresql+psycopg://u@h/db") == "postgresql+psycopg://u@h/db"
    assert normalize_database_url("sqlite:///./x.db") == "sqlite:///./x.db"


def test_settings_aplica_normalizacion(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    assert Settings().database_url == "postgresql+psycopg://u:p@h/db"


def test_settings_por_defecto_usa_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert Settings(_env_file=None).database_url == "sqlite:///./reservaya.db"


def test_lista_cors():
    ajustes = Settings(_env_file=None, cors_origins=" https://a.app , ,https://b.app")
    assert ajustes.lista_cors == ["https://a.app", "https://b.app"]
