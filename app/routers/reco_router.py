import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import EXPORTS_DIR
from app.database.session import get_db
from app.controllers.parser import parse_excel_records
from app.controllers.reco_engine import run_reconciliation
from app.controllers.excel_generator import generate_reco_excel
from app.models.session_model import ReconciliationSession
from app.models.summary_model import GstWiseSummary
from app.models.invoice_model import InvoiceRecoRecord
from app.schemas.reco_schema import ReconcileResponse, SessionSummaryResponse, GstSummaryItem

router = APIRouter(prefix="/api", tags=["Reconciliation"])

@router.post("/reconcile", response_model=ReconcileResponse)
async def reconcile_files(
    period_label: str = Form(...),
    file_2b: UploadFile = File(...),
    file_book: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        content_2b = await file_2b.read()
        content_book = await file_book.read()

        # Parse records
        two_b_records = parse_excel_records(content_2b, preferred_sheet_keywords=["2B", "GSTR-2B", "B2B"])
        book_records = parse_excel_records(content_book, preferred_sheet_keywords=["Book", "Purchase", "Tally"])

        if not two_b_records and not book_records:
            raise HTTPException(status_code=400, detail="No valid GST records found in the uploaded files.")

        # Run reconciliation
        reco_result = run_reconciliation(book_records, two_b_records)
        stats = reco_result["stats"]

        # Export Excel file
        clean_period = period_label.strip().replace(" ", "_").replace("/", "-")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"GST_Reco_{clean_period}_{timestamp}.xlsx"
        export_filepath = EXPORTS_DIR / export_filename

        generate_reco_excel(reco_result, export_filepath)

        # Save session to SQLite database
        session_obj = ReconciliationSession(
            period_label=period_label.strip(),
            file_2b_name=file_2b.filename,
            file_book_name=file_book.filename,
            generated_excel_path=str(export_filepath),
            total_invoices=stats["total_invoices"],
            matched_count=stats["matched_count"],
            mismatched_count=stats["mismatched_count"],
            only_book_count=stats["only_book_count"],
            only_2b_count=stats["only_2b_count"],
            duplicate_count=stats.get("duplicate_count", 0),
            total_tax_diff=stats["total_tax_diff"]
        )
        db.add(session_obj)
        db.commit()
        db.refresh(session_obj)

        # Save GST Summaries to database
        for g in reco_result["gst_wise_summary"]:
            db.add(GstWiseSummary(
                session_id=session_obj.id,
                gstin=g["gstin"],
                book_taxable=g["book_taxable"],
                book_igst=g["book_igst"],
                book_cgst=g["book_cgst"],
                book_sgst=g["book_sgst"],
                book_cess=g["book_cess"],
                two_b_taxable=g["two_b_taxable"],
                two_b_igst=g["two_b_igst"],
                two_b_cgst=g["two_b_cgst"],
                two_b_sgst=g["two_b_sgst"],
                two_b_cess=g["two_b_cess"],
                diff_taxable=g["diff_taxable"],
                diff_igst=g["diff_igst"],
                diff_cgst=g["diff_cgst"],
                diff_sgst=g["diff_sgst"],
                diff_cess=g["diff_cess"],
                status=g["status"]
            ))

        # Save Invoice line items
        for inv in reco_result["invoice_reco_items"]:
            db.add(InvoiceRecoRecord(
                session_id=session_obj.id,
                gstin=inv["gstin"],
                reco_key=inv["reco_key"],
                book_taxable=inv["b_taxable"],
                book_igst=inv["b_igst"],
                book_cgst=inv["b_cgst"],
                book_sgst=inv["b_sgst"],
                book_cess=inv["b_cess"],
                two_b_taxable=inv["t_taxable"],
                two_b_igst=inv["t_igst"],
                two_b_cgst=inv["t_cgst"],
                two_b_sgst=inv["t_sgst"],
                two_b_cess=inv["t_cess"],
                diff_taxable=inv["diff_taxable"],
                diff_igst=inv["diff_igst"],
                diff_cgst=inv["diff_cgst"],
                diff_sgst=inv["diff_sgst"],
                diff_cess=inv["diff_cess"],
                gst_wise_status=inv["gst_wise_status"],
                status_x=inv["status_x"],
                final_remarks=inv["final_remarks"]
            ))

        db.commit()

        # Format Response
        gst_items_resp = [
            GstSummaryItem(
                gstin=g["gstin"],
                book_taxable=g["book_taxable"],
                book_total_tax=g["book_total_tax"],
                two_b_taxable=g["two_b_taxable"],
                two_b_total_tax=g["two_b_total_tax"],
                diff_taxable=g["diff_taxable"],
                diff_total_tax=g["diff_total_tax"],
                status=g["status"]
            )
            for g in reco_result["gst_wise_summary"]
        ]

        session_resp = SessionSummaryResponse(
            id=session_obj.id,
            period_label=session_obj.period_label,
            created_at=session_obj.created_at,
            file_2b_name=session_obj.file_2b_name,
            file_book_name=session_obj.file_book_name,
            total_invoices=session_obj.total_invoices,
            matched_count=session_obj.matched_count,
            mismatched_count=session_obj.mismatched_count,
            only_book_count=session_obj.only_book_count,
            only_2b_count=session_obj.only_2b_count,
            duplicate_count=session_obj.duplicate_count or 0,
            total_tax_diff=session_obj.total_tax_diff,
            download_url=f"/api/download/{session_obj.id}"
        )

        return ReconcileResponse(session=session_resp, gst_summaries=gst_items_resp)

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Reconciliation error: {str(e)}")

@router.get("/download/{session_id}")
def download_excel(session_id: int, db: Session = Depends(get_db)):
    session_obj = db.query(ReconciliationSession).filter(ReconciliationSession.id == session_id).first()
    if not session_obj or not session_obj.generated_excel_path:
        raise HTTPException(status_code=404, detail="Reconciliation session or file not found")

    file_path = Path(session_obj.generated_excel_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File has been moved or deleted from disk")

    download_name = file_path.name
    return FileResponse(
        path=str(file_path),
        filename=download_name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
