from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.database.session import init_db
from app.routers import reco_router, history_router

app = FastAPI(
    title="GST 2B & Tally Book Reconciliation",
    description="Automated offline GST Reconciliation system with SQLite persistence and multi-sheet Excel generation",
    version="2.0.0"
)

# Initialize offline SQLite database tables
init_db()

@app.on_event("startup")
def on_startup():
    init_db()

# Include API Routers
app.include_router(reco_router.router)
app.include_router(history_router.router)

import sys

# Mount Static assets
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    STATIC_DIR = Path(sys._MEIPASS) / "app" / "static"
else:
    STATIC_DIR = Path(__file__).resolve().parent / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

from fastapi.responses import Response

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/")
def serve_index():
    return FileResponse(STATIC_DIR / "index.html")
