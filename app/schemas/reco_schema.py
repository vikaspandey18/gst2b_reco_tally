from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SessionSummaryResponse(BaseModel):
    id: int
    period_label: str
    created_at: datetime
    file_2b_name: Optional[str]
    file_book_name: Optional[str]
    total_invoices: int
    matched_count: int
    mismatched_count: int
    only_book_count: int
    only_2b_count: int
    duplicate_count: int = 0
    total_tax_diff: float
    download_url: str

    class Config:
        from_attributes = True

class GstSummaryItem(BaseModel):
    gstin: str
    book_taxable: float
    book_total_tax: float
    two_b_taxable: float
    two_b_total_tax: float
    diff_taxable: float
    diff_total_tax: float
    status: str

class ReconcileResponse(BaseModel):
    session: SessionSummaryResponse
    gst_summaries: List[GstSummaryItem]
