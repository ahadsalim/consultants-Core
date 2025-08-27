from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.settings import settings
from minio import Minio
from minio.error import S3Error
import logging

logger = logging.getLogger(__name__)


def get_minio_client() -> Minio:
    """
    Get MinIO client instance
    """
    try:
        client = Minio(
            settings.S3_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=settings.S3_ENDPOINT.startswith("https://")
        )
        
        # Ensure bucket exists
        if not client.bucket_exists(settings.S3_BUCKET):
            client.make_bucket(settings.S3_BUCKET)
            logger.info(f"Created bucket: {settings.S3_BUCKET}")
            
        return client
    except S3Error as e:
        logger.error(f"MinIO connection error: {e}")
        raise HTTPException(status_code=503, detail="MinIO service unavailable")


def verify_bridge_token(x_bridge_token: str = Header(...)) -> bool:
    """
    Verify the bridge token for internal sync API
    """
    if x_bridge_token != settings.BRIDGE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid bridge token")
    return True


def get_db_dependency() -> Session:
    """
    Database dependency wrapper
    """
    return Depends(get_db)
