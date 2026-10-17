"""One-time Azure SQL setup: create tables and the two least-privilege users.

  invoice_app_writer   - used by the app to save invoices. Can read/write data
                         and create the tables. Cannot manage users.
  invoice_chat_reader  - used ONLY by the chatbot. SELECT on our 3 tables,
                         nothing else; writes are explicitly DENIED.

Run from your machine (needs "ODBC Driver 18 for SQL Server" installed and
your IP allowed in the SQL server firewall). It reads everything from
environment variables, so no password is typed on the command line:

  AZURE_SQL_SERVER, AZURE_SQL_DATABASE, AZURE_SQL_ADMIN_USER, AZURE_SQL_ADMIN_PASSWORD,
  AZURE_SQL_WRITER_PASSWORD, AZURE_SQL_READER_PASSWORD
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pyodbc  # noqa: E402

from app.db import CHAT_TABLES, SCHEMA_TSQL  # noqa: E402

WRITER, READER = "invoice_app_writer", "invoice_chat_reader"


def env(name):
    v = os.getenv(name, "").strip()
    if not v:
        sys.exit(f"Missing environment variable {name}")
    return v


def q(pw: str) -> str:
    """CREATE USER can't take a bound parameter, so escape quotes for the literal."""
    return pw.replace("'", "''")


def main():
    conn = pyodbc.connect(
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{env('AZURE_SQL_SERVER')},1433;Database={env('AZURE_SQL_DATABASE')};"
        f"Uid={env('AZURE_SQL_ADMIN_USER')};Pwd={env('AZURE_SQL_ADMIN_PASSWORD')};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;", autocommit=True)
    cur = conn.cursor()

    for stmt in SCHEMA_TSQL:
        cur.execute(stmt)
    print("Tables ready.")

    for user, pw in ((WRITER, env("AZURE_SQL_WRITER_PASSWORD")), (READER, env("AZURE_SQL_READER_PASSWORD"))):
        cur.execute(f"IF USER_ID('{user}') IS NULL CREATE USER [{user}] WITH PASSWORD = '{q(pw)}'")
        cur.execute(f"ALTER USER [{user}] WITH PASSWORD = '{q(pw)}'")

    # Writer: data read/write + create tables
    cur.execute(f"ALTER ROLE db_datareader ADD MEMBER [{WRITER}]")
    cur.execute(f"ALTER ROLE db_datawriter ADD MEMBER [{WRITER}]")
    cur.execute(f"ALTER ROLE db_ddladmin ADD MEMBER [{WRITER}]")

    # Reader: SELECT on exactly our tables, everything else denied
    for t in CHAT_TABLES:
        cur.execute(f"GRANT SELECT ON dbo.{t} TO [{READER}]")
        cur.execute(f"DENY INSERT, UPDATE, DELETE, ALTER ON dbo.{t} TO [{READER}]")
    cur.execute(f"DENY CREATE TABLE, CREATE VIEW, CREATE PROCEDURE, EXECUTE TO [{READER}]")
    print(f"Users ready: {WRITER} (read/write), {READER} (read-only).")


if __name__ == "__main__":
    main()
