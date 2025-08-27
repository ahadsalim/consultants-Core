from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class SyncWatermark(Base):
    __tablename__ = "sync_watermarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_imported_at = Column(DateTime(timezone=True), server_default=func.now())
