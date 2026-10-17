import json
from itertools import combinations
from pathlib import Path

import pytest

from app.duplicates import (LIKELY_THRESHOLD, POSSIBLE_THRESHOLD, amount_similarity, compare,
                            date_similarity, find_duplicates, invoice_number_similarity,
                            normalize_invoice_number, normalize_vendor, resolve_vendor)

MANIFEST = Path(__file__).resolve().parent.parent / "samples" / "manifest.json"


def inv(vendor, number, total, d="2026-05-01", currency="INR", id=None):
    return dict(id=id, vendor_name=vendor, invoice_number=number, total=total, invoice_date=d, currency=currency)


# ---------- normalisation -------------------------------------------------
@pytest.mark.parametrize("raw,expected", [
    ("ABC Traders Pvt Ltd", "abc traders"),
    ("A.B.C. Traders Private Limited", "abc traders"),
    ("NorthBridge Consulting Limited", "northbridge consulting"),
    ("Kaveri Packaging Inds.", "kaveri packaging"),
    ("Smith & Sons Ltd", "smith sons"),
])
def test_normalize_vendor(raw, expected):
    assert normalize_vendor(raw) == expected


@pytest.mark.parametrize("a,b", [
    ("ABC/2026/0142", "ABC-2026-142"),
    ("TOS-0234", "TOS0234"),
    ("kpi/0496", "KPI/496"),
])
def test_invoice_number_formatting_ignored(a, b):
    assert normalize_invoice_number(a) == normalize_invoice_number(b)
    assert invoice_number_similarity(a, b) == 1.0


def test_different_digits_capped():
    # Monthly invoices: text is ~95% alike but they're different invoices
    assert invoice_number_similarity("OSF/2026/07", "OSF/2026/08") <= 0.5


# ---------- individual signals ----------------------------------------------
def test_amount_similarity():
    assert amount_similarity(118000, 118001) == 1.0      # rounding difference
    assert amount_similarity(100, 110) == 0.0            # 10% apart
    assert 0 < amount_similarity(100, 102) < 1


def test_date_similarity():
    assert date_similarity("2026-05-01", "2026-05-01") == 1.0
    assert date_similarity("2026-05-01", "2026-06-15") == 0.0
    assert date_similarity(None, "2026-05-01") == 0.5


# ---------- whole-invoice decisions -----------------------------------------
def test_near_duplicate_flagged_as_likely():
    a = inv("ABC Traders Pvt Ltd", "ABC/2026/0499", 3068.0, "2026-09-02")
    b = inv("A.B.C. Traders Private Limited", "ABC-2026-0499", 3068.0, "2026-09-04")
    r = compare(a, b)
    assert r.score >= LIKELY_THRESHOLD and r.label == "Likely duplicate"
    assert "Same invoice number (different formatting)" in r.reasons


def test_recurring_monthly_bill_not_flagged():
    a = inv("Om Sai Facility Services", "OSF/2026/07", 75520.0, "2026-07-05")
    b = inv("Om Sai Facility Services", "OSF/2026/08", 75520.0, "2026-08-05")
    assert compare(a, b).score < POSSIBLE_THRESHOLD


def test_different_vendor_same_number_not_flagged():
    a = inv("ABC Traders Pvt Ltd", "INV-100", 5000)
    b = inv("Delhi Print House LLP", "INV-100", 5000)
    r = compare(a, b)
    assert r.score == 0.0 and "Different vendor" in r.reasons


def test_different_currency_not_flagged():
    a = inv("Thames Office Supplies Ltd", "TOS-1", 100, currency="GBP")
    b = inv("Thames Office Supplies Ltd", "TOS-1", 100, currency="INR")
    assert compare(a, b).score == 0.0


def test_same_number_different_amount_still_reviewed():
    # Business rule: same vendor + same invoice number always goes to review
    a = inv("Infosphere IT Solutions", "ISIT/1", 100000, "2026-05-01")
    b = inv("Infosphere IT Solutions", "ISIT/1", 130000, "2026-07-01")
    r = compare(a, b)
    assert r.label == "Possible duplicate"
    assert any("revised invoice" in x for x in r.reasons)


def test_find_duplicates_skips_self_and_sorts():
    base = inv("ABC Traders", "A-1", 1000, id=1)
    others = [base, inv("ABC Traders", "A-1", 1000, "2026-05-10", id=2), inv("ABC Traders", "A-1", 1000, id=3)]
    hits = find_duplicates(base, others)
    assert [h[0]["id"] for h in hits] == [3, 2]


def test_resolve_vendor_merges_spelling_variants():
    known = ["Northbridge Consulting Ltd", "Thames Office Supplies Ltd"]
    assert resolve_vendor("NorthBridge Consulting Limited", known) == "Northbridge Consulting Ltd"
    assert resolve_vendor("Brand New Vendor Ltd", known) == "Brand New Vendor Ltd"


# ---------- precision / recall on the full sample set -----------------------
def test_sample_set_precision_and_recall():
    """Every planted duplicate is found, and nothing else is flagged."""
    rows = json.loads(MANIFEST.read_text())
    truth = {frozenset((r["file"], r["duplicate_of"])) for r in rows if r["duplicate_of"]}
    invs = {r["file"]: inv(r["vendor"], r["invoice_number"], r["total"], r["date"], r["currency"]) for r in rows}
    flagged = {frozenset((a, b)) for a, b in combinations(invs, 2) if compare(invs[a], invs[b]).is_flagged}
    true_pos = flagged & truth
    assert len(truth) == 5
    assert true_pos == truth, f"missed: {truth - flagged}"          # recall = 100%
    assert flagged == truth, f"false alarms: {flagged - truth}"     # precision = 100%
