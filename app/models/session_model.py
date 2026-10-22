from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base

class ReconciliationSession(Base):
    __tablename__ = "reconciliation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    period_label = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    file_2b_name = Column(String(255), nullable=True)
    file_book_name = Column(String(255), nullable=True)
    generated_excel_path = Column(String(500), nullable=True)
    
    total_invoices = Column(Integer, default=0)
    matched_count = Column(Integer, default=0)
    mismatched_count = Column(Integer, default=0)
    only_book_count = Column(Integer, default=0)
    only_2b_count = Column(Integer, default=0)
    duplicate_count = Column(Integer, default=0)
    total_tax_diff = Column(Float, default=0.0)

    summaries = relationship("GstWiseSummary", back_populates="session", cascade="all, delete-orphan")
    invoices = relationship("InvoiceRecoRecord", back_populates="session", cascade="all, delete-orphan")
