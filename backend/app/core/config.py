from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SECRET_KEY_DEV = "solo-para-desarrollo-local-no-usar-en-produccion"  # noqa: S105


def normalize_database_url(url: str) -> str:
    """Neon/Render entregan postgres:// o postgresql://; SQLAlchemy necesita el driver psycopg."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix) :]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: Literal["dev", "test", "prod"] = "dev"
    database_url: str = "sqlite:///./reservaya.db"
    # Firma los tokens del panel. En producción se define en Render (SECRET_KEY).
    secret_key: str = SECRET_KEY_DEV
    token_horas: int = 8
    # Orígenes extra permitidos por CORS, separados por coma. Vacío: solo mismo origen
    # (Netlify reenvía /api/* a Render, así que normalmente no hace falta).
    cors_origins: str = ""

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        return normalize_database_url(value)

    @model_validator(mode="after")
    def _exigir_secreto_en_produccion(self) -> "Settings":
        if self.env == "prod" and (self.secret_key == SECRET_KEY_DEV or len(self.secret_key) < 32):
            raise ValueError("SECRET_KEY debe definirse (mínimo 32 caracteres) en producción")
        return self

    @property
    def lista_cors(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
