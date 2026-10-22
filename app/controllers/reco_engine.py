import re
from collections import Counter
from typing import List, Dict, Any, Tuple
from app.config import TAX_ROUNDING_TOLERANCE

def normalize_inv_str(s: str) -> str:
    """Strips punctuation, spaces, and year variations for fuzzy invoice matching."""
    if not s:
        return ""
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", s).upper()
    return cleaned.replace("202526", "2526").replace("202425", "2425")

def filter_duplicates(records: List[Dict[str, Any]], source_name: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Separates duplicate invoice numbers from unique ones.
    Returns (unique_records, duplicate_records).
    """
    key_counts = Counter(r["reco_key"] for r in records)
    seen_keys = set()
    unique_list = []
    duplicate_list = []

    for r in records:
        k = r["reco_key"]
        r["source"] = source_name
        if k in seen_keys:
            # Duplicate entry
            dup_item = dict(r)
            dup_item["duplicate_count"] = key_counts[k]
            dup_item["remark"] = f"Duplicate invoice in {source_name} (appears {key_counts[k]} times)"
            duplicate_list.append(dup_item)
        else:
            seen_keys.add(k)
            unique_list.append(r)

    return unique_list, duplicate_list

def run_reconciliation(raw_book_records: List[Dict[str, Any]], raw_two_b_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Core reconciliation engine:
    1. Extracts duplicate invoices into a dedicated list and retains unique records for reco.
    2. Uses PAN as party identifier so GSTIN and PAN match seamlessly.
    3. Executes the 6 reconciliation matching rules.
    """
    # 1. Separate duplicate invoices from unique ones
    book_records, book_duplicates = filter_duplicates(raw_book_records, "Book")
    two_b_records, two_b_duplicates = filter_duplicates(raw_two_b_records, "GSTR-2B")
    all_duplicates = book_duplicates + two_b_duplicates

    # 2. Aggregate by PAN for Sheet 4
    all_pans = sorted(list(set(
        [r["pan"] for r in book_records if r.get("pan")] +
        [r["pan"] for r in two_b_records if r.get("pan")]
    )))

    gst_wise_summary = []
    gst_wise_status_map = {}

    for pan in all_pans:
        b_recs = [r for r in book_records if r["pan"] == pan]
        t_recs = [r for r in two_b_records if r["pan"] == pan]

        b_taxable = round(sum(r["taxable_value"] for r in b_recs), 2)
        b_igst = round(sum(r["igst"] for r in b_recs), 2)
        b_cgst = round(sum(r["cgst"] for r in b_recs), 2)
        b_sgst = round(sum(r["sgst"] for r in b_recs), 2)
        b_cess = round(sum(r["cess"] for r in b_recs), 2)
        b_total_tax = round(b_igst + b_cgst + b_sgst + b_cess, 2)

        t_taxable = round(sum(r["taxable_value"] for r in t_recs), 2)
        t_igst = round(sum(r["igst"] for r in t_recs), 2)
        t_cgst = round(sum(r["cgst"] for r in t_recs), 2)
        t_sgst = round(sum(r["sgst"] for r in t_recs), 2)
        t_cess = round(sum(r["cess"] for r in t_recs), 2)
        t_total_tax = round(t_igst + t_cgst + t_sgst + t_cess, 2)

        diff_taxable = round(b_taxable - t_taxable, 2)
        diff_total_tax = round(b_total_tax - t_total_tax, 2)

        if len(b_recs) == 0 and len(t_recs) > 0:
            status = "Only for the 2B "
        elif len(t_recs) == 0 and len(b_recs) > 0:
            status = "Only for the book "
        elif abs(diff_total_tax) <= TAX_ROUNDING_TOLERANCE and (abs(diff_taxable) <= 10.0 or abs(b_taxable) == 0):
            status = "Book And 2B Match"
        else:
            status = "Book And 2B Mis-Match"

        gst_wise_status_map[pan] = status

        gst_wise_summary.append({
            "gstin": pan,
            "pan": pan,
            "book_taxable": b_taxable,
            "book_igst": b_igst,
            "book_cgst": b_cgst,
            "book_sgst": b_sgst,
            "book_cess": b_cess,
            "book_total_tax": b_total_tax,
            "two_b_taxable": t_taxable,
            "two_b_igst": t_igst,
            "two_b_cgst": t_cgst,
            "two_b_sgst": t_sgst,
            "two_b_cess": t_cess,
            "two_b_total_tax": t_total_tax,
            "diff_taxable": diff_taxable,
            "diff_igst": round(b_igst - t_igst, 2),
            "diff_cgst": round(b_cgst - t_cgst, 2),
            "diff_sgst": round(b_sgst - t_sgst, 2),
            "diff_cess": round(b_cess - t_cess, 2),
            "diff_total_tax": diff_total_tax,
            "status": status
        })

    # 3. Invoice Level Aggregation (Key = PAN_InvoiceNo)
    book_by_key = {r["reco_key"]: r for r in book_records}
    two_b_by_key = {r["reco_key"]: r for r in two_b_records}

    all_keys = sorted(list(set(list(book_by_key.keys()) + list(two_b_by_key.keys()))))
    key_data = {}

    for k in all_keys:
        b_r = book_by_key.get(k, {})
        t_r = two_b_by_key.get(k, {})

        pan = b_r.get("pan") or t_r.get("pan") or (k.split("_", 1)[0] if "_" in k else "")
        inv_no = b_r.get("invoice_no") or t_r.get("invoice_no") or (k.split("_", 1)[1] if "_" in k else "")

        b_taxable = b_r.get("taxable_value", 0.0)
        b_igst = b_r.get("igst", 0.0)
        b_cgst = b_r.get("cgst", 0.0)
        b_sgst = b_r.get("sgst", 0.0)
        b_cess = b_r.get("cess", 0.0)
        b_total_tax = b_r.get("total_tax", 0.0)

        t_taxable = t_r.get("taxable_value", 0.0)
        t_igst = t_r.get("igst", 0.0)
        t_cgst = t_r.get("cgst", 0.0)
        t_sgst = t_r.get("sgst", 0.0)
        t_cess = t_r.get("cess", 0.0)
        t_total_tax = t_r.get("total_tax", 0.0)

        key_data[k] = {
            "gstin": pan,
            "pan": pan,
            "inv_no": inv_no,
            "reco_key": k,
            "b_taxable": b_taxable,
            "b_igst": b_igst,
            "b_cgst": b_cgst,
            "b_sgst": b_sgst,
            "b_cess": b_cess,
            "b_total_tax": b_total_tax,
            "t_taxable": t_taxable,
            "t_igst": t_igst,
            "t_cgst": t_cgst,
            "t_sgst": t_sgst,
            "t_cess": t_cess,
            "t_total_tax": t_total_tax,
            "diff_taxable": round(b_taxable - t_taxable, 2),
            "diff_igst": round(b_igst - t_igst, 2),
            "diff_cgst": round(b_cgst - t_cgst, 2),
            "diff_sgst": round(b_sgst - t_sgst, 2),
            "diff_cess": round(b_cess - t_cess, 2),
            "status_x": None,
            "final_remarks": None
        }

    # Rule: 2B Netting (Invoices & Credit Notes canceling out in 2B)
    for pan in all_pans:
        pan_keys = [k for k in all_keys if key_data[k]["pan"] == pan]
        zero_b = [k for k in pan_keys if key_data[k]["b_taxable"] == 0 and key_data[k]["t_taxable"] != 0]
        if any(key_data[k]["t_taxable"] > 0 for k in zero_b) and any(key_data[k]["t_taxable"] < 0 for k in zero_b):
            if abs(sum(key_data[k]["t_taxable"] for k in zero_b)) <= TAX_ROUNDING_TOLERANCE:
                for k in zero_b:
                    key_data[k]["status_x"] = "Vendor are show in 2B - Tax Invoices and CN"
                    key_data[k]["final_remarks"] = "Vendor are show in 2B - Tax Invoices and CN"

    # Rule: Exact Matches
    for k in all_keys:
        d = key_data[k]
        if d["status_x"] is not None:
            continue
        if d["b_taxable"] > 0 and d["t_taxable"] > 0:
            if abs(d["b_total_tax"] - d["t_total_tax"]) <= TAX_ROUNDING_TOLERANCE and abs(d["diff_taxable"]) <= 5.0:
                d["status_x"] = "Book And 2B Match"
                d["final_remarks"] = "Book And 2B Match"
            else:
                d["status_x"] = "Book And 2B Mis-Match"
                d["final_remarks"] = "Book And 2B Mis-Match"

    # Rule: Typo / Format Mismatch under same PAN
    for pan in all_pans:
        pan_status = gst_wise_status_map.get(pan, "")
        b_unmatched = [k for k in all_keys if key_data[k]["pan"] == pan and key_data[k]["status_x"] is None and key_data[k]["b_taxable"] != 0]
        t_unmatched = [k for k in all_keys if key_data[k]["pan"] == pan and key_data[k]["status_x"] is None and key_data[k]["t_taxable"] != 0]

        matched_t = set()
        for bk in b_unmatched:
            b_norm = normalize_inv_str(key_data[bk]["inv_no"])
            b_amt = key_data[bk]["b_taxable"]
            for tk in t_unmatched:
                if tk in matched_t:
                    continue
                t_norm = normalize_inv_str(key_data[tk]["inv_no"])
                t_amt = key_data[tk]["t_taxable"]
                if (b_norm == t_norm and len(b_norm) > 2) or abs(b_amt - t_amt) <= TAX_ROUNDING_TOLERANCE:
                    matched_t.add(tk)
                    key_data[bk]["status_x"] = "Book And 2B Match-Invocies No Mis-Match"
                    key_data[tk]["status_x"] = "Book And 2B Match-Invocies No Mis-Match"
                    resolved = "Book And 2B Match" if pan_status == "Book And 2B Match" else "Book And 2B Match-Invocies No Mis-Match"
                    key_data[bk]["final_remarks"] = resolved
                    key_data[tk]["final_remarks"] = resolved
                    break

    # Rule: Remaining unclassified
    for k in all_keys:
        d = key_data[k]
        if d["status_x"] is None:
            if d["b_taxable"] != 0 and d["t_taxable"] == 0:
                d["status_x"] = "Only for the book "
                d["final_remarks"] = "Only for the book "
            elif d["t_taxable"] != 0 and d["b_taxable"] == 0:
                d["status_x"] = "Only for the 2B "
                d["final_remarks"] = "Only for the 2B "
            else:
                d["status_x"] = "Book And 2B Mis-Match"
                d["final_remarks"] = "Book And 2B Mis-Match"

    invoice_reco_items = []
    final_remarks_lookup = {}
    for k in all_keys:
        d = key_data[k]
        d["gst_wise_status"] = gst_wise_status_map.get(d["pan"], "")
        invoice_reco_items.append(d)
        final_remarks_lookup[k] = d["status_x"]

    # Assign final remarks to raw records
    for r in two_b_records:
        r["final_remarks"] = final_remarks_lookup.get(r["reco_key"], "")
    for r in book_records:
        r["final_report"] = final_remarks_lookup.get(r["reco_key"], "")

    stats = {
        "total_invoices": len(invoice_reco_items),
        "matched_count": sum(1 for d in invoice_reco_items if "Match" in (d["final_remarks"] or "") and "Mis-Match" not in (d["final_remarks"] or "")),
        "mismatched_count": sum(1 for d in invoice_reco_items if "Mis-Match" in (d["final_remarks"] or "")),
        "only_book_count": sum(1 for d in invoice_reco_items if "Only for the book" in (d["final_remarks"] or "")),
        "only_2b_count": sum(1 for d in invoice_reco_items if "Only for the 2B" in (d["final_remarks"] or "")),
        "duplicate_count": len(all_duplicates),
        "total_tax_diff": round(sum(d["diff_igst"] + d["diff_cgst"] + d["diff_sgst"] + d["diff_cess"] for d in invoice_reco_items), 2)
    }

    return {
        "gst_wise_summary": gst_wise_summary,
        "invoice_reco_items": invoice_reco_items,
        "two_b_records": two_b_records,
        "book_records": book_records,
        "duplicate_invoices": all_duplicates,
        "stats": stats
    }
