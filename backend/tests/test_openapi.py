from scripts.export_openapi import DESTINO, generar_openapi


def test_contrato_openapi_actualizado():
    """Si falla: ejecuta `python -m scripts.export_openapi` desde backend/ y commitea."""
    assert DESTINO.read_text(encoding="utf-8") == generar_openapi()
