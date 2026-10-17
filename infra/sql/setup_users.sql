-- Alternative to scripts/setup_azure_sql.py: paste into Azure Portal >
-- SQL database > Query editor (signed in as the admin). Replace the two
-- <CHANGE_ME> passwords first. Do NOT save real passwords in this file.

-- 1. Tables (same as app/db.py SCHEMA_TSQL; the app also creates them on start)
IF OBJECT_ID('dbo.invoices') IS NULL CREATE TABLE dbo.invoices (
    id INT IDENTITY(1,1) PRIMARY KEY, vendor_name NVARCHAR(200) NOT NULL, vendor_canonical NVARCHAR(200) NULL,
    invoice_number NVARCHAR(100) NOT NULL, invoice_date DATE NULL, currency NVARCHAR(3) NOT NULL,
    subtotal DECIMAL(18,2) NULL, tax DECIMAL(18,2) NULL, total DECIMAL(18,2) NOT NULL, total_inr DECIMAL(18,2) NULL,
    tax_type NVARCHAR(50) NULL, status NVARCHAR(30) NOT NULL DEFAULT 'Clean', source_file NVARCHAR(260) NULL,
    blob_path NVARCHAR(500) NULL, file_sha256 CHAR(64) NULL, extraction_method NVARCHAR(50) NULL,
    confidence FLOAT NULL, uploaded_by NVARCHAR(100) NULL, uploaded_at DATETIME2 NULL);
IF OBJECT_ID('dbo.line_items') IS NULL CREATE TABLE dbo.line_items (
    id INT IDENTITY(1,1) PRIMARY KEY, invoice_id INT NOT NULL REFERENCES dbo.invoices(id),
    description NVARCHAR(500) NULL, quantity DECIMAL(18,3) NULL, unit_price DECIMAL(18,2) NULL, amount DECIMAL(18,2) NULL);
IF OBJECT_ID('dbo.duplicate_flags') IS NULL CREATE TABLE dbo.duplicate_flags (
    id INT IDENTITY(1,1) PRIMARY KEY, invoice_id INT NOT NULL REFERENCES dbo.invoices(id),
    matched_invoice_id INT NOT NULL REFERENCES dbo.invoices(id), score FLOAT NOT NULL, label NVARCHAR(30) NOT NULL,
    reasons NVARCHAR(1000) NULL, review_status NVARCHAR(30) NOT NULL DEFAULT 'Open', created_at DATETIME2 NULL);
GO

-- 2. App writer: read/write data, create tables
CREATE USER [invoice_app_writer] WITH PASSWORD = '<CHANGE_ME_WRITER>';
ALTER ROLE db_datareader ADD MEMBER [invoice_app_writer];
ALTER ROLE db_datawriter ADD MEMBER [invoice_app_writer];
ALTER ROLE db_ddladmin  ADD MEMBER [invoice_app_writer];

-- 3. Chatbot reader: SELECT on three tables only. Writes explicitly denied.
CREATE USER [invoice_chat_reader] WITH PASSWORD = '<CHANGE_ME_READER>';
GRANT SELECT ON dbo.invoices TO [invoice_chat_reader];
GRANT SELECT ON dbo.line_items TO [invoice_chat_reader];
GRANT SELECT ON dbo.duplicate_flags TO [invoice_chat_reader];
DENY INSERT, UPDATE, DELETE, ALTER ON dbo.invoices TO [invoice_chat_reader];
DENY INSERT, UPDATE, DELETE, ALTER ON dbo.line_items TO [invoice_chat_reader];
DENY INSERT, UPDATE, DELETE, ALTER ON dbo.duplicate_flags TO [invoice_chat_reader];
DENY CREATE TABLE, CREATE VIEW, CREATE PROCEDURE, EXECUTE TO [invoice_chat_reader];
