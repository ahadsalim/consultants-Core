from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import get_db
from app.models.official import OfficialDocument
from app.models.qa import QAEntry

router = APIRouter()


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Get system statistics
    Returns counts of official documents and Q&A entries
    """
    # Count official documents
    official_docs_count = db.query(func.count(OfficialDocument.id)).scalar()
    
    # Count Q&A entries
    qa_entries_count = db.query(func.count(QAEntry.id)).scalar()
    
    # Additional stats by status for official documents
    official_docs_by_status = db.query(
        OfficialDocument.status,
        func.count(OfficialDocument.id)
    ).group_by(OfficialDocument.status).all()
    
    # Additional stats by doc_type for official documents
    official_docs_by_type = db.query(
        OfficialDocument.doc_type,
        func.count(OfficialDocument.id)
    ).group_by(OfficialDocument.doc_type).all()
    
    return {
        "official_documents": {
            "total": official_docs_count,
            "by_status": {status: count for status, count in official_docs_by_status},
            "by_type": {doc_type: count for doc_type, count in official_docs_by_type}
        },
        "qa_entries": {
            "total": qa_entries_count
        }
    }
