from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from app.db.session import get_db
from app.deps import verify_bridge_token
from app.models.official import OfficialDocument, LegalUnit
from app.models.qa import QAEntry
from app.models.sync import SyncWatermark
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class LegalUnitData(BaseModel):
    unit_type: str
    num_label: Optional[str] = None
    heading: Optional[str] = None
    text_plain: Optional[str] = None
    order_index: Optional[int] = None


class DocumentData(BaseModel):
    id: uuid.UUID
    title: str
    doc_type: str
    jurisdiction: Optional[str] = None
    authority: Optional[str] = None
    effective_date: Optional[date] = None
    amended_date: Optional[date] = None
    source_url: Optional[str] = None
    file_s3: Optional[str] = None
    text_normalized: Optional[str] = None
    legal_units: Optional[List[LegalUnitData]] = []


class QAData(BaseModel):
    id: uuid.UUID
    question: str
    answer: str
    topic_tags: List[str] = []
    source_url: Optional[str] = None
    author: Optional[str] = None
    org: Optional[str] = None
    answered_at: Optional[date] = None
    quality_score: Optional[float] = None
    licensing: str = "allowed"
    pii_status: str = "clean"
    moderation_status: str = "published"


class SyncImportRequest(BaseModel):
    documents: List[DocumentData] = []
    qa_entries: List[QAData] = []
    batch_ts: str = Field(..., description="RFC3339 timestamp")


@router.post("/import")
async def sync_import(
    request: SyncImportRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_bridge_token)
):
    """
    Internal sync endpoint for importing data from Bridge service
    Secured by X-Bridge-Token header
    """
    try:
        imported_docs = 0
        imported_qa = 0
        
        # Import documents
        for doc_data in request.documents:
            # Upsert document
            stmt = insert(OfficialDocument).values(
                id=doc_data.id,
                title=doc_data.title,
                doc_type=doc_data.doc_type,
                jurisdiction=doc_data.jurisdiction,
                authority=doc_data.authority,
                effective_date=doc_data.effective_date,
                amended_date=doc_data.amended_date,
                source_url=doc_data.source_url,
                file_s3=doc_data.file_s3,
                status='published',
                updated_at=datetime.utcnow()
            )
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_=dict(
                    title=stmt.excluded.title,
                    doc_type=stmt.excluded.doc_type,
                    jurisdiction=stmt.excluded.jurisdiction,
                    authority=stmt.excluded.authority,
                    effective_date=stmt.excluded.effective_date,
                    amended_date=stmt.excluded.amended_date,
                    source_url=stmt.excluded.source_url,
                    file_s3=stmt.excluded.file_s3,
                    status=stmt.excluded.status,
                    updated_at=stmt.excluded.updated_at
                )
            )
            
            db.execute(stmt)
            imported_docs += 1
            
            # Import legal units if provided
            if doc_data.legal_units:
                # Delete existing legal units for this document
                db.query(LegalUnit).filter(LegalUnit.document_id == doc_data.id).delete()
                
                # Insert new legal units
                for unit_data in doc_data.legal_units:
                    legal_unit = LegalUnit(
                        document_id=doc_data.id,
                        unit_type=unit_data.unit_type,
                        num_label=unit_data.num_label,
                        heading=unit_data.heading,
                        text_plain=unit_data.text_plain,
                        order_index=unit_data.order_index
                    )
                    db.add(legal_unit)
        
        # Import Q&A entries
        for qa_data in request.qa_entries:
            stmt = insert(QAEntry).values(
                id=qa_data.id,
                question=qa_data.question,
                answer=qa_data.answer,
                topic_tags=qa_data.topic_tags,
                source_url=qa_data.source_url,
                author=qa_data.author,
                org=qa_data.org,
                answered_at=qa_data.answered_at,
                quality_score=qa_data.quality_score,
                licensing=qa_data.licensing,
                pii_status=qa_data.pii_status,
                moderation_status=qa_data.moderation_status,
                updated_at=datetime.utcnow()
            )
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['id'],
                set_=dict(
                    question=stmt.excluded.question,
                    answer=stmt.excluded.answer,
                    topic_tags=stmt.excluded.topic_tags,
                    source_url=stmt.excluded.source_url,
                    author=stmt.excluded.author,
                    org=stmt.excluded.org,
                    answered_at=stmt.excluded.answered_at,
                    quality_score=stmt.excluded.quality_score,
                    licensing=stmt.excluded.licensing,
                    pii_status=stmt.excluded.pii_status,
                    moderation_status=stmt.excluded.moderation_status,
                    updated_at=stmt.excluded.updated_at
                )
            )
            
            db.execute(stmt)
            imported_qa += 1
        
        # Update sync watermark
        watermark = db.query(SyncWatermark).first()
        if watermark:
            watermark.last_imported_at = datetime.utcnow()
        else:
            watermark = SyncWatermark(last_imported_at=datetime.utcnow())
            db.add(watermark)
        
        db.commit()
        
        logger.info(f"Sync import completed: {imported_docs} documents, {imported_qa} Q&A entries")
        
        return {
            "status": "success",
            "imported": {
                "documents": imported_docs,
                "qa_entries": imported_qa
            },
            "batch_ts": request.batch_ts
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Sync import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")
