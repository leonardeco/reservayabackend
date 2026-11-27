"""Errores de negocio. Cada uno sabe qué código HTTP le corresponde.

Los routers no traducen excepciones una por una: `main.py` registra un único
manejador para `ErrorDeNegocio` y responde {"detail": codigo} con el status de la clase.
"""


class ErrorDeNegocio(Exception):
    status_code: int = 400
    codigo: str = "error"

    def __init__(self, detalle: str | None = None) -> None:
        super().__init__(detalle or self.codigo)


class RestauranteNoEncontrado(ErrorDeNegocio):
    status_code = 404
    codigo = "restaurante_no_encontrado"


class FueraDeHorario(ErrorDeNegocio):
    status_code = 409
    codigo = "fuera_de_horario"


class SinMesaDisponible(ErrorDeNegocio):
    status_code = 409
    codigo = "sin_mesa_disponible"


class CredencialesInvalidas(ErrorDeNegocio):
    status_code = 401
    codigo = "credenciales_invalidas"


class NoAutenticado(ErrorDeNegocio):
    status_code = 401
    codigo = "no_autenticado"


class ReservaNoEncontrada(ErrorDeNegocio):
    status_code = 404
    codigo = "reserva_no_encontrada"


class CambioDeEstadoInvalido(ErrorDeNegocio):
    status_code = 409
    codigo = "cambio_de_estado_invalido"
