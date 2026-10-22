from typing import List
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.session import get_db
from app.models.session_model import ReconciliationSession
from app.schemas.reco_schema import SessionSummaryResponse

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("", response_model=List[SessionSummaryResponse])
def get_all_history(db: Session = Depends(get_db)):
    """
    Returns all previous reconciliation sessions (e.g. 1-2 months old) for offline review and download.
    """
    sessions = db.query(ReconciliationSession).order_by(desc(ReconciliationSession.created_at)).all()
    results = []
    for s in sessions:
        results.append(SessionSummaryResponse(
            id=s.id,
            period_label=s.period_label,
            created_at=s.created_at,
            file_2b_name=s.file_2b_name,
            file_book_name=s.file_book_name,
            total_invoices=s.total_invoices,
            matched_count=s.matched_count,
            mismatched_count=s.mismatched_count,
            only_book_count=s.only_book_count,
            only_2b_count=s.only_2b_count,
            duplicate_count=s.duplicate_count or 0,
            total_tax_diff=s.total_tax_diff,
            download_url=f"/api/download/{s.id}"
        ))
    return results

@router.delete("/{session_id}")
def delete_history_session(session_id: int, db: Session = Depends(get_db)):
    session_obj = db.query(ReconciliationSession).filter(ReconciliationSession.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    if session_obj.generated_excel_path:
        f = Path(session_obj.generated_excel_path)
        if f.exists():
            try:
                f.unlink()
            except Exception:
                pass

    db.delete(session_obj)
    db.commit()
    return {"message": "Session deleted successfully"}
