from sqlalchemy import Column, String, Text, Date, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
import uuid


class OfficialDocument(Base):
    __tablename__ = "official_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False, index=True)
    doc_type = Column(
        ENUM('law', 'regulation', 'circular', 'guideline', name='doc_type_enum'),
        nullable=False
    )
    jurisdiction = Column(String(255))
    authority = Column(String(255))
    effective_date = Column(Date)
    amended_date = Column(Date)
    source_url = Column(Text)
    file_s3 = Column(Text)  # "s3://advisor-docs/raw/{uuid}/{filename}"
    status = Column(
        ENUM('draft', 'in_review', 'approved', 'published', name='doc_status_enum'),
        default='published',
        index=True
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    legal_units = relationship("LegalUnit", back_populates="document", cascade="all, delete-orphan")


class LegalUnit(Base):
    __tablename__ = "legal_units"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("official_documents.id"), nullable=False)
    unit_type = Column(
        ENUM('part', 'chapter', 'section', 'article', 'paragraph', 'clause', 'item', 'note', 'annex', name='unit_type_enum'),
        nullable=False
    )
    num_label = Column(String(100))  # e.g., "ماده ۱۲" or "بند ب"
    heading = Column(Text)
    text_plain = Column(Text)
    order_index = Column(Integer)

    # Relationship
    document = relationship("OfficialDocument", back_populates="legal_units")
