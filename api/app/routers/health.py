from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.deps import get_minio_client
from app.core.settings import settings
from minio import Minio
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check(
    db: Session = Depends(get_db),
    minio_client: Minio = Depends(get_minio_client)
):
    """
    Health check endpoint
    Returns system status including database and MinIO connectivity
    """
    health_status = {
        "status": "ok",
        "env": settings.ENV,
        "db": False,
        "minio": False
    }
    
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status["db"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["db"] = False
        health_status["status"] = "degraded"
    
    # Check MinIO connectivity
    try:
        minio_client.bucket_exists(settings.S3_BUCKET)
        health_status["minio"] = True
    except Exception as e:
        logger.error(f"MinIO health check failed: {e}")
        health_status["minio"] = False
        health_status["status"] = "degraded"
    
    return health_status
