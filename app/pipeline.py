"""The upload pipeline: validate -> extract -> check duplicates -> store file -> save."""
from __future__ import annotations

from dataclasses import dataclass, field

from app import db
from app.duplicates import find_duplicates, resolve_vendor
from app.extraction import ExtractionError, extract_invoice
from app.security import validate_upload
from app.storage import save_file
from app.telemetry import log_event


@dataclass
class ProcessResult:
    ok: bool
    message: str
    invoice_id: int | None = None
    invoice: dict = field(default_factory=dict)
    duplicates: list = field(default_factory=list)   # [(existing_row_dict, MatchResult)]
    exact_file_duplicate: bool = False


def process_upload(filename: str, data: bytes, user: str, force_local: bool = False) -> ProcessResult:
    check = validate_upload(filename, data)
    if not check.ok:
        log_event("upload_rejected", reason=check.reason, user=user)
        return ProcessResult(False, check.reason)

    same_file = db.invoice_by_hash(check.sha256)
    if not same_file.empty:
        r = same_file.iloc[0]
        log_event("upload_exact_duplicate", user=user)
        return ProcessResult(False, f"This exact file was already uploaded as invoice "
                                    f"{r['invoice_number']} from {r['vendor_name']}.",
                             exact_file_duplicate=True)

    try:
        inv = extract_invoice(data, check.safe_name, force_local=force_local)
    except ExtractionError as e:
        log_event("extraction_failed", reason=str(e), user=user)
        return ProcessResult(False, str(e))
    except Exception as e:  # e.g. Azure unreachable
        log_event("extraction_error", error=type(e).__name__, user=user)
        return ProcessResult(False, f"Extraction service error ({type(e).__name__}). Please try again.")

    inv["vendor_canonical"] = resolve_vendor(inv["vendor_name"], db.canonical_vendors())
    existing = db.all_invoices().to_dict("records")
    dups = find_duplicates(inv, existing)
    status = dups[0][1].label if dups else "Clean"

    blob_path = save_file(data, check.sha256, check.ext)
    inv_id = db.insert_invoice(inv, source_file=check.safe_name, blob_path=blob_path,
                               file_sha256=check.sha256, extraction_method=inv["method"],
                               uploaded_by=user, status=status)
    for other, match in dups:
        db.insert_duplicate_flag(inv_id, int(other["id"]), match.score, match.label, "; ".join(match.reasons))

    log_event("invoice_processed", user=user, vendor=inv["vendor_name"], total=inv["total"],
              currency=inv["currency"], duplicates=len(dups), method=inv["method"])
    msg = f"Extracted invoice {inv['invoice_number']} from {inv['vendor_name']}."
    return ProcessResult(True, msg, inv_id, inv, dups)
