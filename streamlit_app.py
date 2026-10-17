"""AI Invoice Assistant - Streamlit front end.

Run locally:   streamlit run streamlit_app.py
"""
from __future__ import annotations

import time

import altair as alt
import pandas as pd
import streamlit as st

from app import db
from app.chatbot import answer_question
from app.config import settings
from app.pipeline import process_upload
from app.security import check_login
from app.telemetry import log_event
from app.ui_style import CSS, esc, fmt_compact_inr, fmt_money, pill

st.set_page_config(page_title="AI Invoice Assistant", page_icon="🧾", layout="wide",
                   initial_sidebar_state="expanded")
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource
def _bootstrap():
    """Runs once per server start: make sure the tables exist."""
    db.init_schema()
    return True


@st.cache_resource
def _login_attempts() -> dict:
    """Failed login attempts shared across all browser sessions (brute-force protection)."""
    return {}


_bootstrap()

MAX_ATTEMPTS, LOCKOUT_SECONDS = 5, 300


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
def login_screen():
    st.markdown("""
      <div class="login-wrap"><div class="login-brand">
        <div class="logo">AI</div>
        <h2>AI Invoice Assistant</h2>
        <p>Sign in to review invoices and ask questions</p>
      </div></div>""", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        if not settings.app_password_hash:
            st.warning("Login isn't configured. Run `python scripts/hash_password.py` and put "
                       "APP_USERNAME and APP_PASSWORD_HASH in your .env (or App Service settings).")
            return
        attempts = _login_attempts()
        with st.form("login"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", width="stretch", type="primary")
        if submitted:
            key = user.strip().lower()
            recent = [t for t in attempts.get(key, []) if time.time() - t < LOCKOUT_SECONDS]
            if len(recent) >= MAX_ATTEMPTS:
                st.error("Too many failed attempts. Please wait 5 minutes and try again.")
                log_event("login_locked", user=key)
                return
            if check_login(user, pw):
                attempts.pop(key, None)
                st.session_state.user = user.strip()
                log_event("login_success", user=key)
                st.rerun()
            else:
                attempts[key] = recent + [time.time()]
                log_event("login_failed", user=key)
                st.error("Incorrect username or password.")
        st.caption("Access is restricted to authorised users. All activity is logged.")


if "user" not in st.session_state:
    login_screen()
    st.stop()

USER = st.session_state.user


# ---------------------------------------------------------------------------
# Sidebar: connected services + demo controls
# ---------------------------------------------------------------------------
def svc(name: str, on: bool, mode: str) -> str:
    return (f'<div class="svc"><span class="name"><span class="dot {"on" if on else "off"}"></span>{esc(name)}</span>'
            f'<span class="mode">{esc(mode)}</span></div>')


with st.sidebar:
    st.markdown("### 🧾 Invoice Assistant")
    st.caption(f"Signed in as **{USER}**")
    st.markdown("**Connected services**")
    st.markdown(
        svc("Document Intelligence", settings.use_docintel, "Azure" if settings.use_docintel else "Offline demo")
        + svc("File storage", settings.use_blob, "Azure Blob" if settings.use_blob else "Local folder")
        + svc("Database", settings.use_azure_sql, "Azure SQL" if settings.use_azure_sql else "SQLite (local)")
        + svc("Chat LLM", settings.llm_configured, settings.llm_model if settings.llm_configured else "Not set")
        + svc("Monitoring", bool(settings.appinsights_conn_str),
              "App Insights" if settings.appinsights_conn_str else "Console logs"),
        unsafe_allow_html=True)
    st.markdown("")
    st.markdown("**Security**")
    st.caption("🔒 Chatbot uses a read-only DB connection\n\n🛡️ Generated SQL is validated: SELECT-only, "
               "approved tables only\n\n📎 Uploads checked: type, size, file signature")
    st.divider()
    with st.expander("Demo controls"):
        if st.button("Reset to sample data", width="stretch"):
            with st.spinner("Reloading sample invoices..."):
                import scripts.seed as seed
                seed.main()
            st.session_state.pop("last_results", None)
            st.session_state.pop("chat", None)
            st.success("Sample data reloaded.")
            st.rerun()
    if st.button("Sign out", width="stretch"):
        log_event("logout", user=USER)
        st.session_state.clear()
        st.rerun()


# ---------------------------------------------------------------------------
# Header + KPIs
# ---------------------------------------------------------------------------
st.markdown("""
<div class="app-header">
  <div>
    <h1>AI Invoice Assistant</h1>
    <p>Upload invoices, catch duplicates before they're paid, and ask questions in plain English.</p>
  </div>
  <span class="badge">{badge}</span>
</div>""".replace("{badge}", "Powered by Azure AI Document Intelligence" if settings.use_docintel
                   else "Offline demo mode"), unsafe_allow_html=True)

s = db.stats()
st.markdown(f"""
<div class="kpi-row">
  <div class="kpi"><div class="label">Invoices processed</div><div class="value">{s['invoices']}</div></div>
  <div class="kpi"><div class="label">Total spend (INR equiv.)</div><div class="value">{fmt_compact_inr(s['spend_inr'])}</div></div>
  <div class="kpi"><div class="label">Vendors</div><div class="value">{s['vendors']}</div></div>
  <div class="kpi {'alert' if s['open_flags'] else ''}"><div class="label">Duplicates to review</div>
       <div class="value">{s['open_flags']}</div></div>
</div>""", unsafe_allow_html=True)

tab_upload, tab_chat = st.tabs(["📤  Upload & Review", "💬  Ask your invoices"])


# ---------------------------------------------------------------------------
# Upload & Review
# ---------------------------------------------------------------------------
def render_fields(inv: dict):
    conf = inv.get("confidence")
    conf_txt = f"{conf:.0%}" if isinstance(conf, (int, float)) else "-"
    fields = [
        ("Vendor", inv.get("vendor_name")), ("Invoice no.", inv.get("invoice_number")),
        ("Invoice date", inv.get("invoice_date")), ("Tax type", inv.get("tax_type") or "-"),
        ("Subtotal", fmt_money(inv.get("subtotal"), inv["currency"])),
        ("Tax", fmt_money(inv.get("tax"), inv["currency"])),
        ("Total", fmt_money(inv.get("total"), inv["currency"])), ("Confidence", conf_txt),
    ]
    cells = "".join(f'<div class="field"><div class="k">{esc(k)}</div><div class="v">{esc(v)}</div></div>'
                    for k, v in fields)
    st.markdown(f'<div class="card"><h4>Extracted fields</h4><div class="field-grid">{cells}</div>'
                f'<div style="margin-top:10px;color:#5B6B79;font-size:.8rem">Read by: {esc(inv.get("method"))}'
                f'</div></div>', unsafe_allow_html=True)
    items = inv.get("line_items") or []
    if items:
        df = pd.DataFrame(items)[["description", "quantity", "unit_price", "amount"]]
        df.columns = ["Description", "Qty", "Unit price", "Amount"]
        st.dataframe(df, hide_index=True, width="stretch",
                     column_config={"Unit price": st.column_config.NumberColumn(format="%.2f"),
                                    "Amount": st.column_config.NumberColumn(format="%.2f")})


def render_duplicate(new_inv: dict, other: dict, match):
    cls = "" if match.label == "Likely duplicate" else "possible"
    reasons = "".join(f"<li>{esc(r)}</li>" for r in match.reasons)
    st.markdown(f"""
    <div class="card dup-card {cls}">
      <h4>⚠️ {esc(match.label)}: matches invoice already in the system &nbsp;{pill(match.label)}</h4>
      <div class="field-grid">
        <div class="field"><div class="k">Existing vendor</div><div class="v">{esc(other['vendor_name'])}</div></div>
        <div class="field"><div class="k">Existing invoice no.</div><div class="v">{esc(other['invoice_number'])}</div></div>
        <div class="field"><div class="k">Existing date</div><div class="v">{esc(other['invoice_date'])}</div></div>
        <div class="field"><div class="k">Existing total</div><div class="v">{esc(fmt_money(other['total'], other['currency']))}</div></div>
      </div>
      <div style="margin-top:12px;font-size:.85rem;color:#5B6B79">Match score <b style="color:#0B1F33">{match.score:.0%}</b>
        <div class="scorebar"><div style="width:{match.score * 100:.0f}%"></div></div></div>
      <ul class="reasons">{reasons}</ul>
    </div>""", unsafe_allow_html=True)


with tab_upload:
    left, right = st.columns([1, 1.6], gap="large")
    with left:
        st.markdown("#### Upload invoices")
        st.caption(f"PDF, PNG or JPG · up to {settings.max_upload_mb} MB each")
        files = st.file_uploader("Invoice files", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True,
                                 label_visibility="collapsed")
        if st.button("Extract & check", type="primary", disabled=not files, width="stretch"):
            results = []
            for f in files:
                with st.spinner(f"Reading {f.name}..."):
                    started = time.perf_counter()
                    r = process_upload(f.name, f.getvalue(), USER)
                    results.append((f.name, r, time.perf_counter() - started))
            st.session_state.last_results = results
            st.rerun()

        with st.expander("How duplicate detection works"):
            st.markdown("""
Each new invoice is compared with every invoice from a **similar vendor in the same currency**:

| Signal | Weight | Example it catches |
|---|---|---|
| Vendor name (cleaned) | 35% | "A.B.C. Traders Pvt Ltd" = "ABC Traders Private Limited" |
| Invoice number (cleaned) | 30% | "ABC/2026/0142" = "ABC-2026-142" |
| Amount | 25% | ₹1,18,000 vs ₹1,18,001 (rounding) |
| Date | 10% | re-sent 5 days later |

**≥ 90%** → Likely duplicate · **80–90%** → Possible duplicate · below → not flagged.
Invoice numbers with different digits (e.g. monthly bills) are never treated as the same invoice.
""")

    with right:
        results = st.session_state.get("last_results", [])
        if not results:
            st.markdown('<div class="card"><h4>Results appear here</h4><div style="color:#5B6B79">'
                        'Upload an invoice to see the extracted fields and duplicate check. Try the files in '
                        '<code>samples/demo_upload/</code>.</div></div>', unsafe_allow_html=True)
        for name, r, secs in results:
            st.markdown(f"##### {esc(name)}")
            if not r.ok:
                (st.warning if r.exact_file_duplicate else st.error)(r.message)
                continue
            if r.duplicates:
                for other, match in r.duplicates[:2]:
                    render_duplicate(r.invoice, other, match)
            else:
                st.markdown(f'<div class="card ok-card">✅ <b>No duplicates found.</b> Saved and ready for '
                            f'approval. <span style="color:#5B6B79">Processed in {secs:.1f}s.</span></div>',
                            unsafe_allow_html=True)
            render_fields(r.invoice)
            if st.button("Undo this upload", key=f"undo_{r.invoice_id}"):
                db.delete_invoice(r.invoice_id)
                st.session_state.last_results = [x for x in results if x[1].invoice_id != r.invoice_id]
                st.rerun()

    st.divider()
    st.markdown("#### Duplicate review queue")
    flags = db.duplicate_flags()
    open_flags = flags[flags["review_status"] == "Open"] if not flags.empty else flags
    if open_flags.empty:
        st.caption("Nothing to review. 🎉")
    for _, f in open_flags.iterrows():
        c1, c2, c3 = st.columns([5, 1.1, 1.1])
        with c1:
            st.markdown(
                f'{pill(f["label"])} &nbsp;<b>{esc(f["vendor"])}</b> · {esc(f["invoice_number"])} · '
                f'{esc(fmt_money(f["total"], f["currency"]))} · {esc(f["invoice_date"])}'
                f'<br><span style="color:#5B6B79;font-size:.85rem">matches #{int(f["matched_id"])} '
                f'{esc(f["matched_vendor"])} · {esc(f["matched_number"])} · {esc(f["matched_date"])} — '
                f'score {f["score"]:.0%} — {esc(f["reasons"])}</span>', unsafe_allow_html=True)
        if c2.button("Confirm", key=f"c_{f['flag_id']}", width="stretch"):
            db.set_flag_review(int(f["flag_id"]), "Confirmed duplicate")
            log_event("duplicate_confirmed", user=USER, flag=int(f["flag_id"]))
            st.rerun()
        if c3.button("Dismiss", key=f"n_{f['flag_id']}", width="stretch"):
            db.set_flag_review(int(f["flag_id"]), "Not a duplicate")
            log_event("duplicate_dismissed", user=USER, flag=int(f["flag_id"]))
            st.rerun()

    st.markdown("#### All invoices")
    df = db.all_invoices()
    if not df.empty:
        view = df[["id", "vendor_name", "invoice_number", "invoice_date", "currency", "total", "total_inr",
                   "tax_type", "status"]].copy()
        q = st.text_input("Filter", placeholder="Search vendor or invoice number", label_visibility="collapsed")
        if q:
            mask = (view["vendor_name"].str.contains(q, case=False, regex=False)
                    | view["invoice_number"].str.contains(q, case=False, regex=False))
            view = view[mask]
        st.dataframe(view, hide_index=True, width="stretch", height=360,
                     column_config={"id": "ID", "vendor_name": "Vendor", "invoice_number": "Invoice no.",
                                    "invoice_date": "Date", "currency": "Cur.",
                                    "total": st.column_config.NumberColumn("Total", format="%.2f"),
                                    "total_inr": st.column_config.NumberColumn("Total (₹)", format="%.0f"),
                                    "tax_type": "Tax", "status": "Status"})


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
SUGGESTIONS = [
    "How much did we spend with each vendor this year?",
    "Which invoices are over 50,000 rupees?",
    "Show me possible duplicates",
    "What is our monthly spend trend?",
    "How much did we spend with Infosphere this quarter?",
    "What is the total GST vs VAT we paid?",
]


def render_answer(a):
    st.markdown(a.text)
    if a.blocked_reason:
        st.markdown(f'<div class="sql-blocked">🛡️ Blocked by SQL safety check: {esc(a.blocked_reason)}</div>',
                    unsafe_allow_html=True)
    if a.data is not None and not a.data.empty:
        chart = a.chart or {}
        if chart.get("type") in ("bar", "line"):
            x, y = chart["x"], chart["y"]
            data = a.data.copy()
            data[y] = pd.to_numeric(data[y], errors="coerce")
            base = alt.Chart(data).encode(
                x=alt.X(f"{x}:N" if chart["type"] == "bar" else f"{x}:O", sort=None if chart["type"] == "line" else "-y",
                        title=None, axis=alt.Axis(labelAngle=-30, labelLimit=180)),
                y=alt.Y(f"{y}:Q", title=y.replace("_", " ")), tooltip=list(data.columns))
            mark = base.mark_bar(color="#0F766E", cornerRadiusEnd=4) if chart["type"] == "bar" \
                else base.mark_line(color="#0F766E", point=True, strokeWidth=2.5)
            st.altair_chart(mark.properties(height=280), width="stretch")
        if len(a.data) > 1 or len(a.data.columns) > 1:
            st.dataframe(a.data, hide_index=True, width="stretch")
    if a.sql:
        with st.expander("How I got this answer"):
            st.code(a.sql, language="sql")
            if not a.blocked_reason:
                st.markdown('<span class="sql-ok">✔ Passed safety check (SELECT-only, approved tables) · '
                            'ran on a read-only connection</span>', unsafe_allow_html=True)


with tab_chat:
    if "chat" not in st.session_state:
        st.session_state.chat = []
    if not settings.llm_configured:
        st.info("Set LLM_BASE_URL, LLM_MODEL and LLM_API_KEY to enable the chatbot.")

    if not st.session_state.chat:
        st.markdown("##### Try asking")
        cols = st.columns(3)
        for i, sug in enumerate(SUGGESTIONS):
            if cols[i % 3].button(sug, key=f"sug_{i}", width="stretch"):
                st.session_state.pending = sug
                st.rerun()

    for turn in st.session_state.chat:
        with st.chat_message("user"):
            st.markdown(turn["question"])
        with st.chat_message("assistant", avatar="🧾"):
            render_answer(turn["answer"])

    question = st.chat_input("Ask about your invoices, e.g. 'Top 3 vendors by spend'")
    question = question or st.session_state.pop("pending", None)
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant", avatar="🧾"):
            with st.spinner("Thinking..."):
                history = [{"question": t["question"], "sql": t["answer"].sql} for t in st.session_state.chat]
                ans = answer_question(question, history, user=USER)
            render_answer(ans)
        st.session_state.chat.append({"question": question, "answer": ans})

    if st.session_state.chat and st.button("Clear conversation"):
        st.session_state.chat = []
        st.rerun()
