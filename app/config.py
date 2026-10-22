import os
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

STORAGE_DIR = BASE_DIR / "storage"
DB_DIR = STORAGE_DIR / "db"
EXPORTS_DIR = STORAGE_DIR / "exports"

# Create directories if they do not exist
DB_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "reco_offline.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Rounding tolerance for matching taxes (in INR)
TAX_ROUNDING_TOLERANCE = 1.50
