from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base

class GstWiseSummary(Base):
    __tablename__ = "gst_wise_summaries"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("reconciliation_sessions.id", ondelete="CASCADE"), nullable=False)
    gstin = Column(String(20), nullable=False)
    
    book_taxable = Column(Float, default=0.0)
    book_igst = Column(Float, default=0.0)
    book_cgst = Column(Float, default=0.0)
    book_sgst = Column(Float, default=0.0)
    book_cess = Column(Float, default=0.0)

    two_b_taxable = Column(Float, default=0.0)
    two_b_igst = Column(Float, default=0.0)
    two_b_cgst = Column(Float, default=0.0)
    two_b_sgst = Column(Float, default=0.0)
    two_b_cess = Column(Float, default=0.0)

    diff_taxable = Column(Float, default=0.0)
    diff_igst = Column(Float, default=0.0)
    diff_cgst = Column(Float, default=0.0)
    diff_sgst = Column(Float, default=0.0)
    diff_cess = Column(Float, default=0.0)

    status = Column(String(50), default="Book And 2B Match")

    session = relationship("ReconciliationSession", back_populates="summaries")
