"""Duplicate invoice detection with fuzzy matching.

How it works (the 30-second version):
  1. NORMALISE  - clean vendor names and invoice numbers so cosmetic
                  differences disappear ("A.B.C. Traders Pvt Ltd" -> "abc traders",
                  "ABC/2026/0142" -> "ABC20260142").
  2. BLOCK      - only compare invoices in the same currency whose vendor names
                  are already reasonably similar (cheap gate, avoids nonsense matches).
  3. SCORE      - four signals, each 0..1, combined with weights:
                    vendor name   35%
                    invoice no.   30%
                    amount        25%
                    date          10%
  4. DECIDE     - score >= 0.90 -> "Likely duplicate"
                  score >= 0.80 -> "Possible duplicate" (human review)
                  below 0.80    -> not flagged

Why these weights? Vendor + invoice number together identify an invoice
(65%). The amount confirms it. The date gets the least weight because
re-sent invoices often carry a new date.

Key precision rule: if two invoice numbers have DIFFERENT digits (e.g.
OSF/2026/07 vs OSF/2026/08), they are different invoices even if the text is
95% alike. So the invoice-number score is capped at 0.5. This is what stops
monthly recurring bills (same vendor, same amount) from being flagged.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from rapidfuzz import fuzz

# ---- Thresholds and weights (one place, easy to explain and tune) ----------
WEIGHTS = {"vendor": 0.35, "invoice_number": 0.30, "amount": 0.25, "date": 0.10}
LIKELY_THRESHOLD = 0.90
POSSIBLE_THRESHOLD = 0.80
VENDOR_GATE = 0.75          # below this vendor similarity we don't even compare
AMOUNT_EXACT_TOL = 0.005    # within 0.5% counts as the same amount (rounding)
AMOUNT_ZERO_AT = 0.05       # 5% or more apart -> amount score 0
DATE_ZERO_AT_DAYS = 30      # 30+ days apart -> date score 0

# Legal-form and filler words that don't help identify a vendor
_SUFFIXES = {
    "pvt", "private", "ltd", "limited", "llp", "llc", "inc", "incorporated", "plc",
    "co", "company", "corp", "corporation", "the", "and", "industries", "inds", "ind",
}


def normalize_vendor(name: str) -> str:
    """'A.B.C. Traders Private Limited' -> 'abc traders'."""
    s = (name or "").lower().replace("&", " and ")
    # Collapse dotted initials: "a.b.c." -> "abc"
    s = re.sub(r"\b(?:[a-z]\.){2,}", lambda m: m.group(0).replace(".", ""), s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    tokens = [t for t in s.split() if t not in _SUFFIXES]
    return " ".join(tokens)


def normalize_invoice_number(num: str) -> str:
    """'ABC/2026/0142' and 'abc-2026-142' both -> 'ABC2026142'."""
    s = (num or "").upper()
    parts = re.findall(r"[A-Z]+|\d+", s)
    return "".join(p.lstrip("0") or "0" if p.isdigit() else p for p in parts)


def _digits(num_norm: str) -> str:
    return "".join(ch for ch in num_norm if ch.isdigit())


def vendor_similarity(a: str, b: str) -> float:
    na, nb = normalize_vendor(a), normalize_vendor(b)
    if not na or not nb:
        return 0.0
    return fuzz.token_sort_ratio(na, nb) / 100


def invoice_number_similarity(a: str, b: str) -> float:
    na, nb = normalize_invoice_number(a), normalize_invoice_number(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    sim = fuzz.ratio(na, nb) / 100
    if _digits(na) != _digits(nb):
        sim = min(sim, 0.5)   # different numbers = different invoices
    return sim


def amount_similarity(a: float, b: float) -> float:
    if a is None or b is None:
        return 0.0
    hi = max(abs(a), abs(b))
    if hi == 0:
        return 1.0
    diff = abs(a - b) / hi
    if diff <= AMOUNT_EXACT_TOL:
        return 1.0
    if diff >= AMOUNT_ZERO_AT:
        return 0.0
    return 1 - (diff - AMOUNT_EXACT_TOL) / (AMOUNT_ZERO_AT - AMOUNT_EXACT_TOL)


def date_similarity(a: date | str | None, b: date | str | None) -> float:
    if not a or not b:
        return 0.5   # unknown date: neutral, neither helps nor hurts much
    da = a if isinstance(a, date) else date.fromisoformat(str(a)[:10])
    db = b if isinstance(b, date) else date.fromisoformat(str(b)[:10])
    days = abs((da - db).days)
    return max(0.0, 1 - days / DATE_ZERO_AT_DAYS)


@dataclass
class MatchResult:
    score: float
    label: str                       # "Likely duplicate" / "Possible duplicate" / "No match"
    parts: dict = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)

    @property
    def is_flagged(self) -> bool:
        return self.score >= POSSIBLE_THRESHOLD


def compare(inv_a: dict, inv_b: dict) -> MatchResult:
    """Compare two invoices (dicts with vendor_name, invoice_number, total,
    invoice_date, currency) and explain the result."""
    if (inv_a.get("currency") or "") != (inv_b.get("currency") or ""):
        return MatchResult(0.0, "No match", reasons=["Different currency"])

    v = vendor_similarity(inv_a["vendor_name"], inv_b["vendor_name"])
    if v < VENDOR_GATE:
        return MatchResult(0.0, "No match", {"vendor": round(v, 3)}, ["Different vendor"])

    parts = {
        "vendor": v,
        "invoice_number": invoice_number_similarity(inv_a["invoice_number"], inv_b["invoice_number"]),
        "amount": amount_similarity(inv_a.get("total"), inv_b.get("total")),
        "date": date_similarity(inv_a.get("invoice_date"), inv_b.get("invoice_date")),
    }
    score = sum(WEIGHTS[k] * parts[k] for k in WEIGHTS)

    reasons = []
    reasons.append("Same vendor" if v >= 0.97 else f"Vendor names {v:.0%} similar")
    if parts["invoice_number"] == 1.0:
        reasons.append("Same invoice number" + (
            "" if inv_a["invoice_number"] == inv_b["invoice_number"] else " (different formatting)"))
    elif parts["invoice_number"] <= 0.5:
        reasons.append("Different invoice number")
    if parts["amount"] == 1.0:
        diff = abs((inv_a.get("total") or 0) - (inv_b.get("total") or 0))
        reasons.append("Same amount" if diff < 0.01 else f"Amount differs by only {diff:,.2f}")
    days = None
    if inv_a.get("invoice_date") and inv_b.get("invoice_date"):
        days = abs((date.fromisoformat(str(inv_a["invoice_date"])[:10])
                    - date.fromisoformat(str(inv_b["invoice_date"])[:10])).days)
        reasons.append("Same date" if days == 0 else f"Dates {days} day(s) apart")

    if score >= LIKELY_THRESHOLD:
        label = "Likely duplicate"
    elif score >= POSSIBLE_THRESHOLD:
        label = "Possible duplicate"
    else:
        label = "No match"
    return MatchResult(round(score, 4), label, {k: round(x, 3) for k, x in parts.items()}, reasons)


def find_duplicates(new_inv: dict, existing: list[dict]) -> list[tuple[dict, MatchResult]]:
    """Return existing invoices that look like duplicates of new_inv, best first."""
    hits = []
    for other in existing:
        if other.get("id") is not None and other.get("id") == new_inv.get("id"):
            continue
        r = compare(new_inv, other)
        if r.is_flagged:
            hits.append((other, r))
    hits.sort(key=lambda h: h[1].score, reverse=True)
    return hits
