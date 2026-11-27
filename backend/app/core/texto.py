import re
import unicodedata


def normalizar_texto(texto: str) -> str:
    """Minúsculas, sin tildes y con espacios simples: base de las búsquedas portables."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return " ".join(sin_tildes.lower().split())


def slugify(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalizar_texto(texto)).strip("-")
