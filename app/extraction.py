"""Invoice field extraction.

Primary engine: Azure AI Document Intelligence, "prebuilt-invoice" model.
It is a pre-trained model: no training needed. It reads PDFs and photos and
returns named fields (VendorName, InvoiceId, InvoiceTotal, Items...), each
with a confidence score.

Offline fallback: our generated sample PDFs carry their data as JSON in the
PDF metadata. If Azure isn't configured, we read that instead, so the demo
still works without internet. Real-world files (photos, other PDFs) need Azure.
"""
from __future__ import annotations

import io
import json
import re
from datetime import date

from app.config import settings


class ExtractionError(Exception):
    pass


REQUIRED = ("vendor_name", "invoice_number", "total", "currency")


def extract_invoice(data: bytes, filename: str) -> dict:
    if settings.use_docintel:
        inv = _extract_azure(data)
    else:
        inv = _extract_local_demo(data, filename)
    missing = [k for k in REQUIRED if inv.get(k) in (None, "")]
    if missing:
        raise ExtractionError(f"Could not read: {', '.join(missing)}. Please check the document.")
    return inv


# --------------------------------------------------------------------------
# Azure AI Document Intelligence
# --------------------------------------------------------------------------
def _num(field) -> float | None:
    if field is None:
        return None
    if field.value_currency is not None:
        return float(field.value_currency.amount)
    if field.value_number is not None:
        return float(field.value_number)
    return _parse_amount(field.content)


def _parse_amount(text: str | None) -> float | None:
    if not text:
        return None
    m = re.search(r"-?\d[\d,]*\.?\d*", text.replace(" ", ""))
    return float(m.group(0).replace(",", "")) if m else None


def _str(field) -> str | None:
    if field is None:
        return None
    return (field.value_string or field.content or "").strip() or None


def _guess_currency(fields, content: str) -> str:
    for key in ("InvoiceTotal", "SubTotal", "AmountDue"):
        f = fields.get(key)
        if f is not None and f.value_currency is not None and f.value_currency.currency_code:
            return f.value_currency.currency_code.upper()
    if "£" in content or "GBP" in content or re.search(r"\bVAT\b", content):
        return "GBP"
    return "INR"


def _guess_tax_type(content: str) -> str | None:
    if "IGST" in content:
        return "GST (IGST)"
    if "CGST" in content or "SGST" in content:
        return "GST (CGST+SGST)"
    if re.search(r"\bVAT\b", content):
        return "VAT"
    if "GST" in content:
        return "GST"
    return None


def _extract_azure(data: bytes) -> dict:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.core.credentials import AzureKeyCredential

    client = DocumentIntelligenceClient(settings.docintel_endpoint, AzureKeyCredential(settings.docintel_key))
    poller = client.begin_analyze_document("prebuilt-invoice", io.BytesIO(data),
                                           content_type="application/octet-stream")
    result = poller.result()
    if not result.documents:
        raise ExtractionError("No invoice found in the document.")
    doc = result.documents[0]
    f = doc.fields or {}
    content = result.content or ""

    inv_date = f.get("InvoiceDate")
    items = []
    items_field = f.get("Items")
    for it in (items_field.value_array or []) if items_field else []:
        o = it.value_object or {}
        items.append(dict(description=_str(o.get("Description")),
                          quantity=_num(o.get("Quantity")),
                          unit_price=_num(o.get("UnitPrice")),
                          amount=_num(o.get("Amount"))))

    total = _num(f.get("InvoiceTotal")) or _num(f.get("AmountDue"))
    subtotal = _num(f.get("SubTotal"))
    tax = _num(f.get("TotalTax"))
    if tax is None and total is not None and subtotal is not None:
        tax = round(total - subtotal, 2)

    confidences = [x.confidence for k, x in f.items()
                   if k in ("VendorName", "InvoiceId", "InvoiceDate", "InvoiceTotal") and x and x.confidence]
    return dict(
        vendor_name=_str(f.get("VendorName")),
        invoice_number=_str(f.get("InvoiceId")),
        invoice_date=(inv_date.value_date.isoformat() if inv_date and inv_date.value_date else None),
        currency=_guess_currency(f, content),
        subtotal=subtotal, tax=tax, total=total,
        tax_type=_guess_tax_type(content),
        line_items=items,
        confidence=round(min(confidences), 3) if confidences else None,
        field_confidence={k: round(x.confidence, 3) for k, x in f.items() if x and x.confidence},
        method="Azure AI Document Intelligence (prebuilt-invoice)",
    )


# --------------------------------------------------------------------------
# Offline demo extractor
# --------------------------------------------------------------------------
def _extract_local_demo(data: bytes, filename: str) -> dict:
    if not filename.lower().endswith(".pdf"):
        raise ExtractionError("Photos need Azure Document Intelligence. Configure AZURE_DOCINTEL_* in .env.")
    from pypdf import PdfReader

    try:
        meta = PdfReader(io.BytesIO(data)).metadata or {}
        payload = json.loads(meta.get("/Subject") or "")
    except Exception:
        raise ExtractionError("This PDF isn't one of the demo samples. Configure Azure Document "
                              "Intelligence to read real-world invoices.")
    date.fromisoformat(payload["invoice_date"])  # sanity check
    payload["confidence"] = 1.0
    payload["field_confidence"] = {}
    payload["method"] = "Local demo extractor (offline)"
    return payload
