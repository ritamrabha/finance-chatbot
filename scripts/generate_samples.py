"""Generate ~40 realistic sample invoice PDFs from 10 fictional vendors.

- 6 Indian vendors (INR, GST: CGST+SGST for same-state, IGST for inter-state)
- 4 UK vendors (GBP, 20% VAT)
- 5 deliberate near-duplicates (small differences in vendor spelling,
  invoice-number formatting, a 1-rupee rounding gap, a few days' date shift)
- 2 "traps": vendors who bill the SAME amount every month. These are NOT
  duplicates and the matcher must not flag them (tests check this).

Output:
  samples/invoices/      -> 38 PDFs loaded into the database by seed.py
  samples/demo_upload/   -> 2 PDFs kept aside to upload live in the demo
                            (one near-duplicate, one clean new invoice)
  samples/manifest.json  -> ground truth (which files are duplicates of which)

Every PDF also carries its structured data as JSON in the PDF "Subject"
metadata field. That lets the app run fully offline (local demo extractor);
with Azure configured, Document Intelligence reads the visible page instead.

All companies, GSTINs and VAT numbers are fictional.
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
OUT_MAIN = ROOT / "samples" / "invoices"
OUT_DEMO = ROOT / "samples" / "demo_upload"

BUYER_IN = ("Nimbus Finance Solutions Pvt Ltd", "4th Floor, Phoenix House, Lower Parel, Mumbai 400013",
            "GSTIN: 27AAACN0000X1Z5")
BUYER_UK = ("Nimbus Finance Solutions (UK) Ltd", "22 Bishopsgate, London EC2N 4AJ", "VAT No: GB 000 1111 22")

VENDORS = [
    # key, name, address, tax id, country, state-code-same-as-buyer?, prefix, catalogue
    dict(key="abc", name="ABC Traders Pvt Ltd", addr="12 Kalbadevi Road, Mumbai 400002",
         taxid="GSTIN: 27AABCA1234F1Z2", country="IN", same_state=True, gst=18, prefix="ABC/2026/",
         items=[("A4 copier paper (box of 5 reams)", 1450), ("Ball pens, blue (pack of 50)", 420),
                ("Box files, lever arch", 95), ("Whiteboard markers (set of 10)", 380),
                ("Desk organiser trays", 650)]),
    dict(key="sgl", name="Shree Ganesh Logistics", addr="Plot 44, Chakan MIDC, Pune 410501",
         taxid="GSTIN: 27AFJPS5678K1Z9", country="IN", same_state=True, gst=18, prefix="SGL-",
         items=[("Full truck load Pune - Mumbai", 18500), ("Part load handling charges", 3200),
                ("Warehouse storage (per pallet-week)", 450), ("Loading / unloading labour", 2500)]),
    dict(key="info", name="Infosphere IT Solutions Pvt Ltd", addr="Tower B, Manyata Tech Park, Bengaluru 560045",
         taxid="GSTIN: 29AADCI4321P1Z1", country="IN", same_state=False, gst=18, prefix="ISIT/26-27/",
         items=[("Managed IT support - monthly retainer", 85000), ("Laptop re-imaging (per device)", 1200),
                ("Microsoft 365 licence setup", 15000), ("On-site engineer visit (per day)", 9500)]),
    dict(key="kav", name="Kaveri Packaging Industries", addr="SIDCO Industrial Estate, Ambattur, Chennai 600098",
         taxid="GSTIN: 33AAHFK8765Q1Z4", country="IN", same_state=False, gst=12, prefix="KPI/",
         items=[("Corrugated boxes 5-ply (per 100)", 2850), ("Bubble wrap roll 1m x 100m", 1650),
                ("BOPP tape 48mm (carton of 72)", 3100), ("Stretch film roll", 780)]),
    dict(key="dph", name="Delhi Print House LLP", addr="B-27 Okhla Industrial Area Phase II, New Delhi 110020",
         taxid="GSTIN: 07AAKFD2468M1Z7", country="IN", same_state=False, gst=18, prefix="DPH-",
         items=[("Annual report printing (per copy)", 340), ("Business cards (box of 100)", 450),
                ("Letterheads (ream)", 1800), ("Branded envelopes (per 500)", 2600)]),
    dict(key="osf", name="Om Sai Facility Services", addr="Road No. 2, Banjara Hills, Hyderabad 500034",
         taxid="GSTIN: 36ABOPS1357L1Z3", country="IN", same_state=False, gst=18, prefix="OSF/2026/",
         items=[("Housekeeping services - monthly contract", 64000)]),
    dict(key="tos", name="Thames Office Supplies Ltd", addr="Unit 7, Riverside Trading Estate, London SE16 2XB",
         taxid="VAT No: GB 284 5521 90", country="UK", gst=20, prefix="TOS-",
         items=[("Ergonomic office chair", 189.00), ("Monitor arm, dual", 74.50),
                ("A4 paper, 2500 sheets", 22.40), ("Toner cartridge, black", 96.00)]),
    dict(key="nbc", name="Northbridge Consulting Ltd", addr="3 Hardman Square, Spinningfields, Manchester M3 3EB",
         taxid="VAT No: GB 391 0045 27", country="UK", gst=20, prefix="NBC-2026-",
         items=[("Finance process review (consultant day)", 950.00), ("Workshop facilitation", 1400.00),
                ("Controls documentation", 2200.00)]),
    dict(key="bch", name="Bristol Cloud Hosting Ltd", addr="Temple Quay House, Bristol BS1 6EG",
         taxid="VAT No: GB 450 7782 13", country="UK", gst=20, prefix="BCH",
         items=[("Managed cloud hosting - monthly plan", 1250.00)]),
    dict(key="hcc", name="Highland Catering Co.", addr="18 Rose Street, Edinburgh EH2 2PR",
         taxid="VAT No: GB 512 3398 64", country="UK", gst=20, prefix="HCC-",
         items=[("Board lunch (per head)", 24.50), ("Coffee & pastries (per head)", 8.75),
                ("Event staff (per hour)", 18.00)]),
]
V = {v["key"]: v for v in VENDORS}


def build_invoice(vendor, number, inv_date, items, name_override=None):
    """Return a structured invoice dict with correctly computed tax."""
    lines = []
    for desc, unit, qty in items:
        amount = round(unit * qty, 2)
        lines.append(dict(description=desc, quantity=qty, unit_price=unit, amount=amount))
    subtotal = round(sum(l["amount"] for l in lines), 2)
    rate = vendor["gst"] / 100
    tax = round(subtotal * rate, 2)
    if vendor["country"] == "IN":
        currency = "INR"
        if vendor.get("same_state"):
            tax_breakup = [(f"CGST @ {vendor['gst'] / 2:g}%", round(tax / 2, 2)),
                           (f"SGST @ {vendor['gst'] / 2:g}%", round(tax / 2, 2))]
            tax_type = "GST (CGST+SGST)"
        else:
            tax_breakup = [(f"IGST @ {vendor['gst']:g}%", tax)]
            tax_type = "GST (IGST)"
    else:
        currency = "GBP"
        tax_breakup = [(f"VAT @ {vendor['gst']:g}%", tax)]
        tax_type = "VAT"
    return dict(vendor_name=name_override or vendor["name"], vendor_address=vendor["addr"],
                vendor_tax_id=vendor["taxid"], invoice_number=number, invoice_date=inv_date.isoformat(),
                currency=currency, tax_type=tax_type, line_items=lines, subtotal=subtotal,
                tax=tax, tax_breakup=tax_breakup, total=round(subtotal + tax, 2), country=vendor["country"])


def money(x, currency):
    sym = "Rs." if currency == "INR" else "GBP"
    return f"{sym} {x:,.2f}"


def render_pdf(inv, path: Path):
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    meta = {k: v for k, v in inv.items() if k != "tax_breakup"}
    c.setTitle(f"Invoice {inv['invoice_number']}")
    c.setAuthor(inv["vendor_name"])
    c.setSubject(json.dumps(meta))  # machine-readable copy for the offline extractor

    # Header band
    c.setFillColor(colors.HexColor("#0B1F33"))
    c.rect(0, h - 38 * mm, w, 38 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(18 * mm, h - 16 * mm, inv["vendor_name"])
    c.setFont("Helvetica", 9)
    c.drawString(18 * mm, h - 23 * mm, inv["vendor_address"])
    c.drawString(18 * mm, h - 29 * mm, inv["vendor_tax_id"])
    c.setFont("Helvetica-Bold", 14)
    title = "TAX INVOICE" if inv["country"] == "IN" else "VAT INVOICE"
    c.drawRightString(w - 18 * mm, h - 16 * mm, title)

    # Invoice meta + bill to
    buyer = BUYER_IN if inv["country"] == "IN" else BUYER_UK
    c.setFillColor(colors.black)
    y = h - 52 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(18 * mm, y, "Bill To:")
    c.setFont("Helvetica", 9.5)
    for i, line in enumerate(buyer):
        c.drawString(18 * mm, y - (5 + 4.5 * i) * mm, line)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(120 * mm, y, "Invoice No:")
    c.drawString(120 * mm, y - 6 * mm, "Invoice Date:")
    c.drawString(120 * mm, y - 12 * mm, "Due Date:")
    c.setFont("Helvetica", 10)
    d = date.fromisoformat(inv["invoice_date"])
    c.drawString(148 * mm, y, inv["invoice_number"])
    c.drawString(148 * mm, y - 6 * mm, d.strftime("%d %b %Y"))
    c.drawString(148 * mm, y - 12 * mm, (d + timedelta(days=30)).strftime("%d %b %Y"))

    # Line items table
    y = h - 85 * mm
    c.setFillColor(colors.HexColor("#E8EEF3"))
    c.rect(18 * mm, y - 2 * mm, w - 36 * mm, 8 * mm, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9.5)
    c.drawString(20 * mm, y + 0.5 * mm, "Description")
    c.drawRightString(125 * mm, y + 0.5 * mm, "Qty")
    c.drawRightString(155 * mm, y + 0.5 * mm, "Unit Price")
    c.drawRightString(w - 20 * mm, y + 0.5 * mm, "Amount")
    c.setFont("Helvetica", 9.5)
    for li in inv["line_items"]:
        y -= 8 * mm
        c.drawString(20 * mm, y, li["description"])
        c.drawRightString(125 * mm, y, f"{li['quantity']:g}")
        c.drawRightString(155 * mm, y, f"{li['unit_price']:,.2f}")
        c.drawRightString(w - 20 * mm, y, f"{li['amount']:,.2f}")
    y -= 5 * mm
    c.setStrokeColor(colors.HexColor("#B8C4CE"))
    c.line(18 * mm, y, w - 18 * mm, y)

    # Totals
    def total_row(label, value, bold=False):
        nonlocal y
        y -= 7 * mm
        c.setFont("Helvetica-Bold" if bold else "Helvetica", 10)
        c.drawRightString(155 * mm, y, label)
        c.drawRightString(w - 20 * mm, y, money(value, inv["currency"]))

    total_row("Subtotal", inv["subtotal"])
    for label, val in inv["tax_breakup"]:
        total_row(label, val)
    total_row("Total Amount Due", inv["total"], bold=True)

    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.HexColor("#5B6B79"))
    c.drawString(18 * mm, 20 * mm, "Payment terms: 30 days. This is a computer-generated invoice for demonstration purposes only.")
    c.drawString(18 * mm, 15 * mm, "All companies and tax registration numbers shown are fictional.")
    c.save()


def pick_items(rng, vendor, n_min=1, n_max=3):
    cat = vendor["items"]
    chosen = rng.sample(cat, k=min(len(cat), rng.randint(n_min, n_max)))
    out = []
    for desc, unit in chosen:
        if vendor["country"] == "UK":
            qty = rng.choice([1, 2, 3]) if unit >= 500 else rng.choice([2, 4, 6, 10, 12, 20])
        else:
            qty = 1 if unit > 5000 else rng.choice([2, 4, 5, 10, 12, 20, 25])
        out.append((desc, unit, qty))
    return out


def main():
    rng = random.Random(42)
    OUT_MAIN.mkdir(parents=True, exist_ok=True)
    OUT_DEMO.mkdir(parents=True, exist_ok=True)
    for old in list(OUT_MAIN.glob("*.pdf")) + list(OUT_DEMO.glob("*.pdf")):
        old.unlink()

    invoices = []  # (filename, invoice_dict, folder, duplicate_of)
    start = date(2026, 4, 1)

    # Regular vendors: 3-4 invoices each spread over Apr-Oct 2026
    plan = {"abc": 3, "sgl": 4, "info": 3, "kav": 2, "dph": 3, "tos": 2, "nbc": 2, "hcc": 3}
    counters = {k: rng.randint(100, 500) for k in V}
    for key, n in plan.items():
        v = V[key]
        for _ in range(n):
            counters[key] += rng.randint(3, 40)
            d = start + timedelta(days=rng.randint(0, 198))
            num = f"{v['prefix']}{counters[key]:04d}"
            invoices.append([None, build_invoice(v, num, d, pick_items(rng, v)), "main", None])

    # Recurring monthly "traps": same amount every month, different invoice numbers
    for key, months in (("osf", range(6, 10)), ("bch", range(7, 10))):
        v = V[key]
        for m in months:
            num = f"{v['prefix']}{m:02d}" if key == "osf" else f"{v['prefix']}{2026}{m:02d}01"
            desc, unit = v["items"][0]
            invoices.append([None, build_invoice(v, num, date(2026, m, 5), [(desc, unit, 1)]), "main", None])

    # Make sure "this quarter" (Oct 2026) has data for the chatbot demo
    for key, day in (("abc", 3), ("info", 7), ("tos", 9), ("sgl", 14)):
        v = V[key]
        counters[key] += 11
        num = f"{v['prefix']}{counters[key]:04d}"
        invoices.append([None, build_invoice(v, num, date(2026, 10, day), pick_items(rng, v)), "main", None])

    for i, row in enumerate(invoices, 1):
        row[0] = f"INV_{i:03d}_{row[1]['vendor_name'].split()[0].replace('.', '')}.pdf"

    def find(key, idx=0):
        rows = [r for r in invoices if r[1]["vendor_name"] == V[key]["name"]]
        return rows[idx]

    def near_dup(key, idx, *, name=None, number=None, days=0, amount_delta=0.0, folder="main"):
        """Copy an existing invoice with small, realistic differences."""
        orig = find(key, idx)
        o = orig[1]
        items = [(li["description"], li["unit_price"], li["quantity"]) for li in o["line_items"]]
        new = build_invoice(V[key], number or o["invoice_number"],
                            date.fromisoformat(o["invoice_date"]) + timedelta(days=days), items, name_override=name)
        if amount_delta:
            new["total"] = round(new["total"] + amount_delta, 2)
            new["tax"] = round(new["tax"] + amount_delta, 2)
            new["tax_breakup"] = [(new["tax_breakup"][0][0], round(new["tax_breakup"][0][1] + amount_delta, 2))] + new["tax_breakup"][1:]
        fname = f"INV_{len(invoices) + 1:03d}_{key.upper()}_resend.pdf"
        invoices.append([fname, new, folder, orig[0]])

    abc_num = find("abc", 1)[1]["invoice_number"]           # e.g. ABC/2026/0142
    tos_num = find("tos", 0)[1]["invoice_number"]           # e.g. TOS-0531
    kav_num = find("kav", 0)[1]["invoice_number"]           # e.g. KPI/0889

    # 1. Different spelling + punctuation in name, invoice no. with dashes, posted 2 days later (DEMO UPLOAD)
    near_dup("abc", 1, name="A.B.C. Traders Private Limited", number=abc_num.replace("/", "-"), days=2, folder="demo")
    # 2. Same invoice, 1 rupee rounding difference in tax
    near_dup("info", 0, amount_delta=1.0)
    # 3. Missing "Ltd", invoice number without dash
    near_dup("tos", 0, name="Thames Office Supplies", number=tos_num.replace("-", ""))
    # 4. Vendor re-sent the same invoice 5 days later with different casing
    near_dup("nbc", 1, name="NorthBridge Consulting Limited", days=5)
    # 5. Abbreviated name, leading zero dropped from invoice number
    near_dup("kav", 0, name="Kaveri Packaging Inds.", number=kav_num.replace("/0", "/"), days=1)

    # A clean, brand-new invoice for the live demo (should NOT be flagged)
    v = V["hcc"]
    invoices.append(["INV_NEW_Highland_Catering.pdf",
                     build_invoice(v, "HCC-0999", date(2026, 10, 16),
                                   [("Board lunch (per head)", 24.50, 14), ("Coffee & pastries (per head)", 8.75, 20)]),
                     "demo", None])

    manifest = []
    for fname, inv, folder, dup_of in invoices:
        out = (OUT_DEMO if folder == "demo" else OUT_MAIN) / fname
        render_pdf(inv, out)
        manifest.append(dict(file=fname, folder=folder, duplicate_of=dup_of, vendor=inv["vendor_name"],
                             invoice_number=inv["invoice_number"], date=inv["invoice_date"],
                             total=inv["total"], currency=inv["currency"]))

    (ROOT / "samples" / "manifest.json").write_text(json.dumps(manifest, indent=2))
    n_main = sum(1 for m in manifest if m["folder"] == "main")
    print(f"Generated {len(manifest)} invoices: {n_main} in samples/invoices, "
          f"{len(manifest) - n_main} in samples/demo_upload, "
          f"{sum(1 for m in manifest if m['duplicate_of'])} deliberate near-duplicates.")


if __name__ == "__main__":
    main()
