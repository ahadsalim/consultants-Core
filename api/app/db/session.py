from typing import Generator
from app.db.base import SessionLocal


def get_db() -> Generator:
    """
    Database dependency for FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
