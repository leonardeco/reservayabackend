import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.deps import DbSession

logger = logging.getLogger(__name__)

router = APIRouter(tags=["salud"])


@router.get("/health")
def health(db: DbSession) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.exception("health_db_check_failed")
        raise HTTPException(
            status_code=503, detail={"status": "error", "db": "unavailable"}
        ) from exc
    return {"status": "ok", "db": "ok"}
