from minio import Minio
from minio.error import S3Error
from app.core.settings import settings
import logging

logger = logging.getLogger(__name__)


class MinIOHelper:
    """Helper class for MinIO operations"""
    
    def __init__(self):
        self.client = Minio(
            settings.S3_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            secure=settings.S3_ENDPOINT.startswith("https://")
        )
        self.bucket_name = settings.S3_BUCKET
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if not"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise
    
    def upload_file(self, file_path: str, object_name: str, content_type: str = "application/octet-stream"):
        """Upload a file to MinIO"""
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path,
                content_type=content_type
            )
            return f"s3://{self.bucket_name}/{object_name}"
        except S3Error as e:
            logger.error(f"Error uploading file {file_path}: {e}")
            raise
    
    def download_file(self, object_name: str, file_path: str):
        """Download a file from MinIO"""
        try:
            self.client.fget_object(self.bucket_name, object_name, file_path)
        except S3Error as e:
            logger.error(f"Error downloading file {object_name}: {e}")
            raise
    
    def delete_file(self, object_name: str):
        """Delete a file from MinIO"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            logger.error(f"Error deleting file {object_name}: {e}")
            raise
    
    def list_files(self, prefix: str = ""):
        """List files in the bucket"""
        try:
            objects = self.client.list_objects(self.bucket_name, prefix=prefix, recursive=True)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"Error listing files: {e}")
            raise
    
    def get_file_url(self, object_name: str, expires_in_seconds: int = 3600):
        """Get a presigned URL for file access"""
        try:
            return self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires_in_seconds
            )
        except S3Error as e:
            logger.error(f"Error generating presigned URL for {object_name}: {e}")
            raise
