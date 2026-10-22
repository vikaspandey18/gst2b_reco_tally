from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL
from app.database.base import Base

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from sqlalchemy import inspect, text
    from app.models.session_model import ReconciliationSession
    from app.models.summary_model import GstWiseSummary
    from app.models.invoice_model import InvoiceRecoRecord
    Base.metadata.create_all(bind=engine)
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        if "reconciliation_sessions" in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns("reconciliation_sessions")]
            if "duplicate_count" not in cols:
                conn.execute(text("ALTER TABLE reconciliation_sessions ADD COLUMN duplicate_count INTEGER DEFAULT 0"))
                conn.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
