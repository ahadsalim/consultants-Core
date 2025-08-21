from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    PROJECT_NAME: str = "advisor-core"
    ENV: str = "dev"
    
    # Database
    SQLALCHEMY_DATABASE_URI: str
    
    # MinIO/S3
    S3_ENDPOINT: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "advisor-docs"
    
    # Security
    JWT_SECRET: str = "change_me_in_production"
    BRIDGE_TOKEN: str = "secure_bridge_token_change_me"
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://admin-frontend:5173"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated string to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
