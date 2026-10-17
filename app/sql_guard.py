"""SQL safety check for chatbot-generated queries.

The LLM writes SQL from a user's question. We never trust that SQL. Before it
runs, it must pass ALL of these checks:

  1. Size limit and a single statement only (no "SELECT ...; DROP TABLE ...").
  2. No SQL comments (a common trick to hide part of a query).
  3. No dangerous keywords anywhere outside string literals
     (INSERT, UPDATE, DELETE, DROP, EXEC, ATTACH, PRAGMA, INTO, ...).
  4. Parsed into a syntax tree with sqlglot: the top-level statement must be
     a SELECT (or a UNION of SELECTs, optionally with a WITH clause), and no
     node anywhere in the tree may be a write or DDL operation.
  5. Every table referenced must be on the allow-list
     (invoices, line_items, duplicate_flags). No system tables.

Even if something got past all five, the query then runs on a READ-ONLY
database connection (see db.py). That is "defence in depth": two separate
locks, so one mistake is not enough for an attacker.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import sqlglot
from sqlglot import exp

from app.db import CHAT_TABLES

MAX_SQL_CHARS = 4000

FORBIDDEN_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "create", "truncate", "merge", "upsert",
    "grant", "revoke", "deny", "exec", "execute", "attach", "detach", "pragma", "vacuum",
    "reindex", "into", "openrowset", "opendatasource", "openquery", "bulk", "waitfor",
    "shutdown", "backup", "restore", "dbcc", "kill", "load_extension", "readfile", "writefile",
    "sys", "sqlite_master", "sqlite_schema", "sqlite_temp_master", "information_schema",
]
_KEYWORD_RE = re.compile(r"\b(" + "|".join(FORBIDDEN_KEYWORDS) + r")\b|\b(xp_|sp_)\w*", re.IGNORECASE)
_STRING_RE = re.compile(r"'(?:[^']|'')*'")


def _node_types(*names: str) -> tuple[type, ...]:
    """Resolve sqlglot expression classes by name (tolerates version differences)."""
    return tuple(getattr(exp, n) for n in names if hasattr(exp, n))


WRITE_NODES = _node_types(
    "Insert", "Update", "Delete", "Drop", "Create", "Alter", "AlterTable", "Merge", "Into",
    "TruncateTable", "Command", "Pragma", "Attach", "Detach", "Grant", "Set", "Use",
    "Transaction", "Commit", "Rollback", "Copy", "LoadData",
)
ALLOWED_ROOTS = _node_types("Select", "Union", "Intersect", "Except", "SetOperation", "Subquery")


@dataclass
class GuardResult:
    ok: bool
    reason: str
    sql: str = ""


def validate_sql(sql: str, dialect: str = "sqlite", allowed_tables=CHAT_TABLES) -> GuardResult:
    if not sql or not sql.strip():
        return GuardResult(False, "Empty query")
    sql = sql.strip()
    # Strip a markdown code fence if the model added one
    sql = re.sub(r"^```(?:sql)?\s*|\s*```$", "", sql, flags=re.IGNORECASE).strip()
    sql = sql.rstrip(";").strip()

    if len(sql) > MAX_SQL_CHARS:
        return GuardResult(False, "Query is too long")
    if "--" in sql or "/*" in sql or "*/" in sql or "#" in _STRING_RE.sub("''", sql):
        return GuardResult(False, "Comments are not allowed in queries")

    without_strings = _STRING_RE.sub("''", sql)
    if ";" in without_strings:
        return GuardResult(False, "Only one statement is allowed")
    m = _KEYWORD_RE.search(without_strings)
    if m:
        return GuardResult(False, f"Forbidden keyword: {m.group(0).upper()}")

    try:
        statements = [s for s in sqlglot.parse(sql, read=dialect) if s is not None]
    except Exception as e:  # sqlglot.errors.ParseError and friends
        return GuardResult(False, f"Could not parse SQL: {str(e).splitlines()[0][:120]}")
    if len(statements) != 1:
        return GuardResult(False, "Only one statement is allowed")
    tree = statements[0]

    if not isinstance(tree, ALLOWED_ROOTS):
        return GuardResult(False, f"Only SELECT queries are allowed (got {type(tree).__name__})")

    for node in tree.walk():
        if isinstance(node, WRITE_NODES):
            return GuardResult(False, f"Operation not allowed: {type(node).__name__}")

    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}
    allowed = {t.lower() for t in allowed_tables}
    for table in tree.find_all(exp.Table):
        name = (table.name or "").lower()
        schema = (table.db or "").lower()
        if table.catalog or (schema and schema != "dbo"):
            return GuardResult(False, f"Schema-qualified table not allowed: {table.sql()}")
        if name in cte_names:
            continue
        if name not in allowed:
            return GuardResult(False, f"Table not allowed: {name or table.sql()}")

    return GuardResult(True, "OK", sql)
