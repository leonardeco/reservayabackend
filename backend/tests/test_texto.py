from app.core.texto import normalizar_texto, slugify


def test_normalizar_quita_tildes_y_mayusculas():
    assert normalizar_texto("  El Fogón   PAISA ") == "el fogon paisa"
    assert normalizar_texto("Belén, Medellín") == "belen, medellin"


def test_slugify():
    assert slugify("Hogareños: Comida saludable") == "hogarenos-comida-saludable"
    assert slugify("La Terraza") == "la-terraza"
