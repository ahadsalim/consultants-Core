from sqlalchemy import Column, String, Text, Date, DateTime, Float, ARRAY
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.sql import func
from app.db.base import Base
import uuid


class QAEntry(Base):
    __tablename__ = "qa_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False, index=True)
    answer = Column(Text, nullable=False, index=True)
    topic_tags = Column(ARRAY(String), default=[], index=True)
    source_url = Column(Text)
    author = Column(String(255))
    org = Column(String(255))
    answered_at = Column(Date)
    quality_score = Column(Float)
    licensing = Column(
        ENUM('allowed', 'restricted', name='licensing_enum'),
        default='allowed'
    )
    pii_status = Column(
        ENUM('clean', 'contains', name='pii_status_enum'),
        default='clean'
    )
    moderation_status = Column(String(50), default='published', index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
