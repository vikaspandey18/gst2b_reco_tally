import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onefile",
    "--name", "GST_Reconciliation",
    "--add-data", f"{BASE_DIR / 'app' / 'static'};app/static",
    "--hidden-import", "uvicorn.logging",
    "--hidden-import", "uvicorn.loops",
    "--hidden-import", "uvicorn.loops.auto",
    "--hidden-import", "uvicorn.protocols",
    "--hidden-import", "uvicorn.protocols.http",
    "--hidden-import", "uvicorn.protocols.http.auto",
    "--hidden-import", "uvicorn.protocols.websockets",
    "--hidden-import", "uvicorn.protocols.websockets.auto",
    "--hidden-import", "uvicorn.lifespans",
    "--hidden-import", "uvicorn.lifespans.on",
    "--hidden-import", "multipart",
    "--hidden-import", "python_multipart",
    "--hidden-import", "sqlalchemy.sql.default_comparator",
    "--hidden-import", "openpyxl",
    "--hidden-import", "pandas",
    str(BASE_DIR / "app_launcher.py")
]

print("Building Single Standalone EXE file...")
print("Command:", " ".join(cmd))
res = subprocess.run(cmd, cwd=str(BASE_DIR))
if res.returncode == 0:
    print("\n=======================================================")
    print(" SINGLE EXE BUILD SUCCESSFUL!")
    print(f" Standalone File: {BASE_DIR / 'dist' / 'GST_Reconciliation.exe'}")
    print("=======================================================")
else:
    print("Build failed with return code:", res.returncode)
