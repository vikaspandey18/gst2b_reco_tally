# GST 2B & Tally Book Reconciliation System

An automated GST Reconciliation platform built with **FastAPI**, **SQLite**, and **openpyxl**.

---

## ✨ Features

- **Automated Matching**:
  - Matches transactions between GSTR-2B and Tally Purchase Register.
  - Handles **Exact Matches**, **Invoice Typo / Formatting Mismatches**, **Vendor Netting Entries (Tax Invoices + Credit Notes)**, **Only in Book**, **Only in 2B**, and **Amount Mismatches**.
- **PAN-Based Matching & Fallback**:
  - Automatically extracts 10-character PAN from 15-character GSTIN.
  - Matches records seamlessly even if one file has PAN and the other has GSTIN.
- **Duplicate Invoices Detection (5th Sheet)**:
  - Identifies duplicate invoice numbers under the same vendor.
  - Keeps unique records for reconciliation and writes all duplicates into a dedicated **`Duplicate Invoices`** sheet with reasons and counts.
- **Dynamic 5-Sheet Excel Output**:
  - **`GST + Invocie No`**: Line-item reconciliation with live `=SUMIF`, `=VLOOKUP`, `=SUBTOTAL`, and `=SUM` formulas.
  - **`GSTR-2B`**: Input 2B records with concatenated helper keys and remarks.
  - **`Book`**: Input Tally records with concatenated helper keys and remarks.
  - **`GST Wise Reco`**: Vendor GSTIN/PAN level summary with match statuses.
  - **`Duplicate Invoices`**: Complete list of duplicate invoice entries.
- **Offline SQLite Storage**:
  - Stores all reconciliation runs and past reports locally.
  - Re-download reports from 1–2 months ago anytime without re-uploading.

---

## 🚀 Quick Start (Local)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python run.py
```
*(Or on Windows, simply double-click `start_app.bat`)*

### 3. Open in Browser
Visit: **`http://localhost:8000`**

---

## 🌐 Deploy Online (e.g. Render.com)

1. Connect your repository `vikaspandey18/gst2b_reco_tally` to **Render** as a **Web Service**.
2. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Click **Create Web Service** — your app will be live with a public HTTPS link!
