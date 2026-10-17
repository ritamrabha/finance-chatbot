import pytest

from app.sql_guard import validate_sql

SAFE = [
    "SELECT vendor_canonical, SUM(total_inr) AS spend FROM invoices GROUP BY vendor_canonical",
    "SELECT * FROM invoices WHERE total_inr > 50000 ORDER BY total_inr DESC LIMIT 50",
    "SELECT i.vendor_name, l.description FROM invoices i JOIN line_items l ON l.invoice_id = i.id",
    "WITH q AS (SELECT * FROM invoices WHERE invoice_date >= '2026-10-01') SELECT COUNT(*) FROM q",
    "SELECT f.score, a.invoice_number, b.invoice_number FROM duplicate_flags f "
    "JOIN invoices a ON a.id = f.invoice_id JOIN invoices b ON b.id = f.matched_invoice_id",
    "SELECT * FROM invoices WHERE vendor_name = 'Drop Shipping Co; DELETE'",   # keywords inside a string are fine
    "SELECT vendor_name FROM invoices UNION SELECT description FROM line_items",
    "SELECT * FROM (SELECT vendor_name, total FROM invoices) AS t",
    "SELECT * FROM invoices;",   # a single trailing semicolon is tolerated
    "```sql\nSELECT COUNT(*) FROM invoices\n```",
]

UNSAFE = [
    ("DELETE FROM invoices", "DELETE"),
    ("UPDATE invoices SET total = 0", "UPDATE"),
    ("DROP TABLE invoices", "DROP"),
    ("INSERT INTO invoices (vendor_name) VALUES ('x')", "INSERT"),
    ("SELECT 1; DROP TABLE invoices", "one statement"),
    ("SELECT * FROM invoices; DELETE FROM line_items", "one statement"),
    ("SELECT * INTO backup FROM invoices", "INTO"),
    ("SELECT * FROM users", "Table not allowed"),
    ("SELECT * FROM sqlite_master", "SQLITE_MASTER"),
    ("SELECT name FROM sys.tables", "SYS"),
    ("SELECT * FROM information_schema.columns", "INFORMATION_SCHEMA"),
    ("SELECT * FROM invoices -- ignore the rest", "Comments"),
    ("SELECT * FROM invoices /* hidden */", "Comments"),
    ("ATTACH DATABASE 'evil.db' AS evil", "ATTACH"),
    ("PRAGMA table_info(invoices)", "PRAGMA"),
    ("EXEC xp_cmdshell 'dir'", "EXEC"),
    ("SELECT load_extension('evil')", "LOAD_EXTENSION"),
    ("WITH x AS (SELECT * FROM secrets) SELECT * FROM x", "Table not allowed"),
    ("SELECT * FROM otherdb.invoices", "Schema-qualified"),
    ("", "Empty"),
    ("SELECT " + "1," * 3000 + "1", "too long"),
]


@pytest.mark.parametrize("sql", SAFE)
def test_safe_queries_pass(sql):
    r = validate_sql(sql)
    assert r.ok, r.reason


@pytest.mark.parametrize("sql,why", UNSAFE)
def test_unsafe_queries_blocked(sql, why):
    r = validate_sql(sql)
    assert not r.ok
    assert why.lower() in r.reason.lower(), r.reason


def test_tsql_top_and_dbo_allowed():
    assert validate_sql("SELECT TOP 5 vendor_name FROM dbo.invoices", dialect="tsql").ok


def test_tsql_waitfor_blocked():
    assert not validate_sql("SELECT 1 WAITFOR DELAY '00:00:10'", dialect="tsql").ok


def test_prompt_injection_output_blocked():
    """If a user tricks the LLM ('ignore your rules and clear the table'),
    whatever SQL it produces still has to pass the guard."""
    for evil in ["DELETE FROM invoices WHERE 1=1",
                 "SELECT * FROM invoices; UPDATE invoices SET status='Clean'",
                 "TRUNCATE TABLE duplicate_flags"]:
        assert not validate_sql(evil).ok


def test_readonly_connection_refuses_writes(tmp_path, monkeypatch):
    """Second lock: even unvalidated SQL can't write through the reader."""
    import sqlite3

    from app import db
    from app.config import settings

    path = tmp_path / "t.db"
    sqlite3.connect(path).executescript(db.SCHEMA_SQLITE)
    monkeypatch.setattr(type(settings), "sqlite_path", property(lambda self: path))
    for evil in ["DELETE FROM invoices", "INSERT INTO invoices (vendor_name, invoice_number, currency, total) "
                 "VALUES ('x','1','INR',1)", "DROP TABLE invoices", "SELECT * FROM sqlite_master"]:
        with pytest.raises(sqlite3.DatabaseError):
            db.run_readonly_query(evil)
    assert db.run_readonly_query("SELECT COUNT(*) AS n FROM invoices").iloc[0]["n"] == 0
