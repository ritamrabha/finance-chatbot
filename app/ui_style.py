"""Visual styling and small formatting helpers for the Streamlit UI."""
from __future__ import annotations

import html

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

:root {
  --navy: #0B1F33; --navy-2: #13304D; --teal: #0F766E; --teal-soft: #E6F3F1;
  --ink: #0B1F33; --muted: #5B6B79; --line: #E3E8EE; --bg: #F7F8FA;
  --red: #B42318; --red-soft: #FEF3F2; --amber: #B54708; --amber-soft: #FFFAEB;
  --green: #067647; --green-soft: #ECFDF3;
}
html, body, [class*="css"], .stMarkdown, .stTextInput, button, input, textarea {
  font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif !important;
}
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; height: 0; }
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1200px; }

/* Header band */
.app-header {
  background: linear-gradient(120deg, var(--navy) 0%, var(--navy-2) 100%);
  color: #fff; border-radius: 14px; padding: 22px 26px; margin-bottom: 18px;
  display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
}
.app-header h1 { color: #fff; font-size: 1.45rem; font-weight: 700; margin: 0; letter-spacing: -0.01em; }
.app-header p { color: #B9C7D6; margin: 4px 0 0 0; font-size: 0.92rem; }
.app-header .badge {
  background: rgba(255,255,255,0.10); border: 1px solid rgba(255,255,255,0.18);
  color: #E5EDF5; padding: 6px 12px; border-radius: 999px; font-size: 0.8rem; white-space: nowrap;
}

/* KPI tiles */
.kpi-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin-bottom: 18px; }
@media (max-width: 760px) { .kpi-row { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.kpi { background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 14px 16px; }
.kpi .label { color: var(--muted); font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; }
.kpi .value { color: var(--ink); font-size: 1.45rem; font-weight: 700; margin-top: 4px; font-variant-numeric: tabular-nums; }
.kpi.alert .value { color: var(--red); }

/* Cards */
.card { background: #fff; border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; margin-bottom: 12px; }
.card h4 { margin: 0 0 10px 0; font-size: 1rem; color: var(--ink); }
.field-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px 18px; }
@media (max-width: 760px) { .field-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
.field .k { color: var(--muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 600; }
.field .v { color: var(--ink); font-size: 0.98rem; font-weight: 600; margin-top: 2px; font-variant-numeric: tabular-nums; word-break: break-word; }

.dup-card { border-left: 4px solid var(--red); background: var(--red-soft); }
.dup-card.possible { border-left-color: var(--amber); background: var(--amber-soft); }
.ok-card { border-left: 4px solid var(--green); background: var(--green-soft); }
.pill { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
.pill.red { background: #FEE4E2; color: var(--red); }
.pill.amber { background: #FEF0C7; color: var(--amber); }
.pill.green { background: #D1FADF; color: var(--green); }
.pill.grey { background: #EEF2F6; color: var(--muted); }
.reasons { margin: 8px 0 0 0; padding-left: 18px; color: var(--ink); font-size: 0.9rem; }
.scorebar { height: 8px; background: #E9EEF3; border-radius: 6px; overflow: hidden; margin-top: 6px; }
.scorebar > div { height: 100%; background: var(--red); }

/* Sidebar */
section[data-testid="stSidebar"] { background: #fff; border-right: 1px solid var(--line); }
.svc { display: flex; justify-content: space-between; align-items: center; padding: 7px 0;
       border-bottom: 1px dashed var(--line); font-size: 0.86rem; }
.svc .name { color: var(--ink); font-weight: 500; }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
.dot.on { background: #12B76A; } .dot.off { background: #98A2B3; }
.svc .mode { color: var(--muted); font-size: 0.78rem; }

/* Chat */
.sql-ok { color: var(--green); font-size: 0.8rem; font-weight: 600; }
.sql-blocked { color: var(--red); font-size: 0.85rem; font-weight: 600; }
[data-testid="stChatMessage"] { background: #fff; border: 1px solid var(--line); border-radius: 12px; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { font-weight: 600; padding: 10px 16px; }

/* Login */
.login-wrap { max-width: 420px; margin: 7vh auto 0 auto; }
.login-brand { text-align: center; margin-bottom: 18px; }
.login-brand .logo { width: 52px; height: 52px; border-radius: 14px; background: var(--navy); color: #fff;
  display: inline-flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.2rem; }
.login-brand h2 { margin: 12px 0 2px 0; color: var(--ink); font-size: 1.35rem; }
.login-brand p { color: var(--muted); margin: 0; font-size: 0.9rem; }
.stButton > button[kind="primary"], .stFormSubmitButton > button { background: var(--teal); border-color: var(--teal); }
</style>
"""


def esc(x) -> str:
    return html.escape("" if x is None else str(x))


def fmt_inr(x: float | None) -> str:
    """Indian digit grouping: 1234567.5 -> '₹12,34,567.50'."""
    if x is None:
        return "-"
    neg = x < 0
    x = abs(float(x))
    whole, frac = f"{x:.2f}".split(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    return f"{'-' if neg else ''}₹{whole}.{frac}"


def fmt_money(x: float | None, currency: str) -> str:
    if x is None:
        return "-"
    if currency == "INR":
        return fmt_inr(x)
    sym = {"GBP": "£", "USD": "$", "EUR": "€"}.get(currency, currency + " ")
    return f"{sym}{float(x):,.2f}"


def fmt_compact_inr(x: float) -> str:
    if x >= 1e7:
        return f"₹{x / 1e7:.2f} Cr"
    if x >= 1e5:
        return f"₹{x / 1e5:.2f} L"
    return fmt_inr(x)


def pill(label: str) -> str:
    cls = {"Likely duplicate": "red", "Confirmed duplicate": "red", "Possible duplicate": "amber",
           "Clean": "green", "Not a duplicate": "green"}.get(label, "grey")
    return f'<span class="pill {cls}">{esc(label)}</span>'
