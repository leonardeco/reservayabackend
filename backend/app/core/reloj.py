from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends


def get_ahora() -> datetime:
    """Reloj inyectable: las pruebas lo reemplazan para congelar el tiempo."""
    return datetime.now(UTC)


Ahora = Annotated[datetime, Depends(get_ahora)]
