"""Database layer. Works with local SQLite or Azure SQL Database.

Two kinds of connection:
  * WRITER  - used by the app itself to save invoices (parameterised queries only).
  * READER  - used ONLY by the chatbot. It is read-only at the database level:
                SQLite    -> opened with mode=ro + PRAGMA query_only + an
                             authorizer callback that only allows reading
                             the approved tables.
                Azure SQL -> a separate login that has SELECT permission only
                             (see infra/sql/create_readonly_user.sql).
    So even if a malicious query slipped past the SQL validator, the
    database itself would refuse to change anything.
"""
from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone

import pandas as pd

from app.config import FX_TO_INR, settings

# Tables the chatbot is allowed to read. Anything else is rejected.
CHAT_TABLES = ("invoices", "line_items", "duplicate_flags")

SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS invoices (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name       TEXT NOT NULL,
    invoice_number    TEXT NOT NULL,
    invoice_date      TEXT,              -- ISO 'YYYY-MM-DD'
    currency          TEXT NOT NULL,     -- 'INR' or 'GBP'
    subtotal          REAL,
    tax               REAL,
    total             REAL NOT NULL,
    total_inr         REAL,              -- total converted to INR (demo FX rate)
    tax_type          TEXT,              -- 'GST (IGST)', 'GST (CGST+SGST)', 'VAT'
    status            TEXT NOT NULL DEFAULT 'Clean',
    source_file       TEXT,
    blob_path         TEXT,
    file_sha256       TEXT,
    extraction_method TEXT,
    confidence        REAL,
    uploaded_by       TEXT,
    uploaded_at       TEXT
);
CREATE TABLE IF NOT EXISTS line_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id  INTEGER NOT NULL REFERENCES invoices(id),
    description TEXT,
    quantity    REAL,
    unit_price  REAL,
    amount      REAL
);
CREATE TABLE IF NOT EXISTS duplicate_flags (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id         INTEGER NOT NULL REFERENCES invoices(id),
    matched_invoice_id INTEGER NOT NULL REFERENCES invoices(id),
    score              REAL NOT NULL,
    label              TEXT NOT NULL,
    reasons            TEXT,
    review_status      TEXT NOT NULL DEFAULT 'Open',
    created_at         TEXT
);
CREATE INDEX IF NOT EXISTS ix_inv_vendor ON invoices(vendor_name);
CREATE INDEX IF NOT EXISTS ix_inv_hash ON invoices(file_sha256);
"""

SCHEMA_TSQL = [
    """IF OBJECT_ID('dbo.invoices') IS NULL CREATE TABLE dbo.invoices (
        id INT IDENTITY(1,1) PRIMARY KEY,
        vendor_name NVARCHAR(200) NOT NULL,
        invoice_number NVARCHAR(100) NOT NULL,
        invoice_date DATE NULL,
        currency NVARCHAR(3) NOT NULL,
        subtotal DECIMAL(18,2) NULL,
        tax DECIMAL(18,2) NULL,
        total DECIMAL(18,2) NOT NULL,
        total_inr DECIMAL(18,2) NULL,
        tax_type NVARCHAR(50) NULL,
        status NVARCHAR(30) NOT NULL DEFAULT 'Clean',
        source_file NVARCHAR(260) NULL,
        blob_path NVARCHAR(500) NULL,
        file_sha256 CHAR(64) NULL,
        extraction_method NVARCHAR(50) NULL,
        confidence FLOAT NULL,
        uploaded_by NVARCHAR(100) NULL,
        uploaded_at DATETIME2 NULL)""",
    """IF OBJECT_ID('dbo.line_items') IS NULL CREATE TABLE dbo.line_items (
        id INT IDENTITY(1,1) PRIMARY KEY,
        invoice_id INT NOT NULL REFERENCES dbo.invoices(id),
        description NVARCHAR(500) NULL,
        quantity DECIMAL(18,3) NULL,
        unit_price DECIMAL(18,2) NULL,
        amount DECIMAL(18,2) NULL)""",
    """IF OBJECT_ID('dbo.duplicate_flags') IS NULL CREATE TABLE dbo.duplicate_flags (
        id INT IDENTITY(1,1) PRIMARY KEY,
        invoice_id INT NOT NULL REFERENCES dbo.invoices(id),
        matched_invoice_id INT NOT NULL REFERENCES dbo.invoices(id),
        score FLOAT NOT NULL,
        label NVARCHAR(30) NOT NULL,
        reasons NVARCHAR(1000) NULL,
        review_status NVARCHAR(30) NOT NULL DEFAULT 'Open',
        created_at DATETIME2 NULL)""",
]

DIALECT = "tsql" if settings.use_azure_sql else "sqlite"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# --------------------------------------------------------------------------
# Connections
# --------------------------------------------------------------------------
def _odbc_conn_str(user: str, password: str) -> str:
    return (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{settings.sql_server},1433;Database={settings.sql_database};"
        f"Uid={user};Pwd={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )


@contextmanager
def writer():
    """Read-write connection for the app's own (parameterised) queries."""
    if settings.use_azure_sql:
        import pyodbc
        conn = pyodbc.connect(_odbc_conn_str(settings.sql_writer_user, settings.sql_writer_password))
    else:
        settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(settings.sqlite_path)
        conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _sqlite_readonly_authorizer(action, arg1, arg2, db_name, trigger):
    """Called by SQLite for every operation a query wants to perform.
    Only plain reads of the approved tables (and safe functions) are allowed."""
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ:
        # arg1 = table name. CTEs / subqueries have no table name.
        if arg1 in CHAT_TABLES or arg1 is None or arg1 == "":
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION:
        if (arg2 or "").lower() in {"load_extension", "readfile", "writefile", "edit", "fts3_tokenizer"}:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY   # INSERT, UPDATE, DELETE, PRAGMA, ATTACH, ... all denied


@contextmanager
def reader():
    """READ-ONLY connection used by the chatbot."""
    if settings.use_azure_sql:
        import pyodbc
        conn = pyodbc.connect(_odbc_conn_str(settings.sql_reader_user, settings.sql_reader_password),
                              readonly=True)
        conn.timeout = 10  # seconds per query
    else:
        uri = f"file:{settings.sqlite_path.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("PRAGMA query_only = ON")
        conn.set_authorizer(_sqlite_readonly_authorizer)
        deadline = time.monotonic() + 10
        # Abort runaway queries after 10 seconds
        conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 10_000)
    try:
        yield conn
    finally:
        conn.close()


def run_readonly_query(sql: str, max_rows: int = 500) -> pd.DataFrame:
    """Execute an already-validated SELECT on the read-only connection."""
    with reader() as conn:
        cur = conn.cursor()
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchmany(max_rows)
    return pd.DataFrame.from_records([tuple(r) for r in rows], columns=cols)


# --------------------------------------------------------------------------
# Schema + writes (always parameterised: values never get pasted into SQL)
# --------------------------------------------------------------------------
def init_schema() -> None:
    with writer() as conn:
        if DIALECT == "sqlite":
            conn.executescript(SCHEMA_SQLITE)
        else:
            cur = conn.cursor()
            for stmt in SCHEMA_TSQL:
                cur.execute(stmt)


def _insert(conn, sql: str, params: tuple) -> int:
    cur = conn.cursor()
    if DIALECT == "sqlite":
        cur.execute(sql, params)
        return int(cur.lastrowid)
    # T-SQL: return the new id with OUTPUT INSERTED.id
    sql = sql.replace(") VALUES", ") OUTPUT INSERTED.id VALUES", 1)
    cur.execute(sql, params)
    return int(cur.fetchone()[0])


def insert_invoice(inv: dict, *, source_file: str, blob_path: str, file_sha256: str,
                   extraction_method: str, uploaded_by: str, status: str = "Clean") -> int:
    total_inr = round(float(inv["total"]) * FX_TO_INR.get(inv["currency"], 1.0), 2)
    with writer() as conn:
        inv_id = _insert(conn, """
            INSERT INTO invoices (vendor_name, invoice_number, invoice_date, currency, subtotal, tax,
                total, total_inr, tax_type, status, source_file, blob_path, file_sha256,
                extraction_method, confidence, uploaded_by, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (inv["vendor_name"], inv["invoice_number"], inv.get("invoice_date"), inv["currency"],
             inv.get("subtotal"), inv.get("tax"), inv["total"], total_inr, inv.get("tax_type"),
             status, source_file, blob_path, file_sha256, extraction_method,
             inv.get("confidence"), uploaded_by, _now()))
        cur = conn.cursor()
        for li in inv.get("line_items", []):
            cur.execute(
                "INSERT INTO line_items (invoice_id, description, quantity, unit_price, amount) VALUES (?, ?, ?, ?, ?)",
                (inv_id, li.get("description"), li.get("quantity"), li.get("unit_price"), li.get("amount")))
    return inv_id


def insert_duplicate_flag(invoice_id: int, matched_id: int, score: float, label: str, reasons: str) -> None:
    with writer() as conn:
        conn.cursor().execute(
            "INSERT INTO duplicate_flags (invoice_id, matched_invoice_id, score, label, reasons, review_status, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'Open', ?)",
            (invoice_id, matched_id, score, label, reasons, _now()))


def set_invoice_status(invoice_id: int, status: str) -> None:
    with writer() as conn:
        conn.cursor().execute("UPDATE invoices SET status = ? WHERE id = ?", (status, invoice_id))


def set_flag_review(flag_id: int, review_status: str) -> None:
    with writer() as conn:
        cur = conn.cursor()
        cur.execute("UPDATE duplicate_flags SET review_status = ? WHERE id = ?", (review_status, flag_id))
        if review_status == "Not a duplicate":
            cur.execute("UPDATE invoices SET status = 'Clean' WHERE id = "
                        "(SELECT invoice_id FROM duplicate_flags WHERE id = ?)", (flag_id,))
        elif review_status == "Confirmed duplicate":
            cur.execute("UPDATE invoices SET status = 'Confirmed duplicate' WHERE id = "
                        "(SELECT invoice_id FROM duplicate_flags WHERE id = ?)", (flag_id,))


def delete_invoice(invoice_id: int) -> None:
    """Remove an invoice (used to undo a demo upload)."""
    with writer() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM duplicate_flags WHERE invoice_id = ? OR matched_invoice_id = ?", (invoice_id, invoice_id))
        cur.execute("DELETE FROM line_items WHERE invoice_id = ?", (invoice_id,))
        cur.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))


def reset_all() -> None:
    with writer() as conn:
        cur = conn.cursor()
        for t in ("duplicate_flags", "line_items", "invoices"):
            cur.execute(f"DELETE FROM {t}")  # fixed table names, no user input


# --------------------------------------------------------------------------
# Reads used by the app UI
# --------------------------------------------------------------------------
def _df(sql: str, params: tuple = ()) -> pd.DataFrame:
    with writer() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return pd.DataFrame.from_records([tuple(r) for r in cur.fetchall()], columns=cols)


def all_invoices() -> pd.DataFrame:
    return _df("SELECT * FROM invoices ORDER BY invoice_date DESC, id DESC")


def invoice_by_hash(sha: str) -> pd.DataFrame:
    return _df("SELECT id, vendor_name, invoice_number FROM invoices WHERE file_sha256 = ?", (sha,))


def line_items_for(invoice_id: int) -> pd.DataFrame:
    return _df("SELECT description, quantity, unit_price, amount FROM line_items WHERE invoice_id = ?",
               (invoice_id,))


def duplicate_flags() -> pd.DataFrame:
    return _df("""
        SELECT f.id AS flag_id, f.label, f.score, f.reasons, f.review_status,
               a.id AS invoice_id, a.vendor_name AS vendor, a.invoice_number, a.invoice_date,
               a.total, a.currency,
               b.id AS matched_id, b.vendor_name AS matched_vendor,
               b.invoice_number AS matched_number, b.invoice_date AS matched_date, b.total AS matched_total
        FROM duplicate_flags f
        JOIN invoices a ON a.id = f.invoice_id
        JOIN invoices b ON b.id = f.matched_invoice_id
        ORDER BY f.score DESC""")


def stats() -> dict:
    df = _df("""SELECT COUNT(*) AS n, COALESCE(SUM(total_inr), 0) AS spend_inr,
                       COUNT(DISTINCT vendor_name) AS vendors FROM invoices""")
    flags = _df("SELECT COUNT(*) AS n FROM duplicate_flags WHERE review_status = 'Open'")
    row = df.iloc[0]
    return dict(invoices=int(row["n"]), spend_inr=float(row["spend_inr"]),
                vendors=int(row["vendors"]), open_flags=int(flags.iloc[0]["n"]))
