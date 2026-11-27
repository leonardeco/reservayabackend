"""Contraseñas y tokens del panel con la biblioteca estándar (sin dependencias extra).

- Contraseñas: PBKDF2-SHA256 con sal aleatoria; se guarda "pbkdf2_sha256$iteraciones$sal$hash".
- Tokens: datos en base64 + firma HMAC-SHA256. Llevan id del administrador, restaurante
  y vencimiento. Si alguien cambia un byte, la firma deja de coincidir.
"""

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta


class HashContrasena:
    ALGORITMO = "pbkdf2_sha256"
    ITERACIONES = 200_000

    @classmethod
    def generar(cls, contrasena: str) -> str:
        sal = secrets.token_hex(16)
        digest = cls._derivar(contrasena, sal, cls.ITERACIONES)
        return f"{cls.ALGORITMO}${cls.ITERACIONES}${sal}${digest}"

    @classmethod
    def verificar(cls, contrasena: str, guardado: str) -> bool:
        try:
            algoritmo, iteraciones, sal, digest = guardado.split("$")
        except ValueError:
            return False
        if algoritmo != cls.ALGORITMO:
            return False
        calculado = cls._derivar(contrasena, sal, int(iteraciones))
        return hmac.compare_digest(calculado, digest)

    @staticmethod
    def _derivar(contrasena: str, sal: str, iteraciones: int) -> str:
        return hashlib.pbkdf2_hmac("sha256", contrasena.encode(), sal.encode(), iteraciones).hex()


class TokenInvalido(Exception):
    pass


class FirmadorTokens:
    def __init__(self, secreto: str, horas: int = 8) -> None:
        self._secreto = secreto.encode()
        self._vigencia = timedelta(hours=horas)

    def emitir(self, admin_id: int, restaurante_id: int, ahora: datetime) -> str:
        datos = {
            "sub": admin_id,
            "rid": restaurante_id,
            "exp": int((ahora + self._vigencia).timestamp()),
        }
        cuerpo = _b64(json.dumps(datos, separators=(",", ":")).encode())
        return f"{cuerpo}.{self._firmar(cuerpo)}"

    def leer(self, token: str, ahora: datetime) -> dict:
        try:
            cuerpo, firma = token.split(".")
        except ValueError as exc:
            raise TokenInvalido("formato") from exc
        if not hmac.compare_digest(firma, self._firmar(cuerpo)):
            raise TokenInvalido("firma")
        try:
            datos = json.loads(_desde_b64(cuerpo))
        except ValueError as exc:
            raise TokenInvalido("contenido") from exc
        if datos.get("exp", 0) < ahora.timestamp():
            raise TokenInvalido("vencido")
        return datos

    def vence_en(self, ahora: datetime) -> datetime:
        return (ahora + self._vigencia).astimezone(UTC)

    def _firmar(self, cuerpo: str) -> str:
        return _b64(hmac.new(self._secreto, cuerpo.encode(), hashlib.sha256).digest())


def _b64(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).rstrip(b"=").decode()


def _desde_b64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))
