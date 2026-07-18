import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.database import get_db

router = APIRouter()
logger = logging.getLogger("health")


@router.get("")
async def get_health(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Health check endpoint verifying system connectivity and database access.
    """
    health_status = {"status": "healthy", "env": settings.ENV, "database": "unknown"}

    try:
        # Run standard query to confirm connection
        await db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        logger.error(f"Health check database query failure: {str(e)}", exc_info=True)
        health_status["status"] = "unhealthy"
        health_status["database"] = "disconnected"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health_status
        ) from e

    return health_status
