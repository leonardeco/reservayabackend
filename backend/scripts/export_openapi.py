"""Escribe el contrato OpenAPI en docs/api/openapi.json: python -m scripts.export_openapi."""

import json
from pathlib import Path

from app.main import create_app

DESTINO = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi.json"


def generar_openapi() -> str:
    return json.dumps(create_app().openapi(), ensure_ascii=False, indent=2) + "\n"


def main() -> None:
    DESTINO.write_text(generar_openapi(), encoding="utf-8", newline="\n")
    print(f"OpenAPI escrito en {DESTINO}")


if __name__ == "__main__":
    main()
