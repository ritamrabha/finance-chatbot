import initSqlJs from 'sql.js';
import sqlWasmUrl from 'sql.js/dist/sql-wasm.wasm?url';
import initialSeed from '../data/invoices_seed.json';
import { MemoryDatabase } from './sqlFallback.js';
import { reactive } from 'vue';

const FX_TO_INR = { INR: 1.0, GBP: 110.0 };

let sqlEngine = null;
let sqliteDb = null;
let fallbackDb = null;
let usingFallback = false;

export const dbState = reactive({
  ready: false,
  loading: true,
  error: null,
  invoicesCount: 0,
  duplicateFlagsCount: 0,
  engineType: 'WASM',
  lastUpdated: Date.now()
});

const SCHEMA = `
CREATE TABLE IF NOT EXISTS invoices (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name       TEXT NOT NULL,
    vendor_canonical  TEXT,
    invoice_number    TEXT NOT NULL,
    invoice_date      TEXT,
    currency          TEXT NOT NULL,
    subtotal          REAL,
    tax               REAL,
    total             REAL NOT NULL,
    total_inr         REAL,
    tax_type          TEXT,
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
    score              REAL,
    label              TEXT,
    reasons            TEXT,
    review_status      TEXT DEFAULT 'Open',
    created_at         TEXT
);
`;

/**
 * Initialize SQLite database with WebAssembly or safe in-memory fallback
 */
export async function initDatabase() {
  if (sqliteDb || fallbackDb) return sqliteDb || fallbackDb;

  dbState.loading = true;

  try {
    // 1. Try fetching WASM binary directly with validation
    let wasmBinary = null;
    try {
      const resp = await fetch(sqlWasmUrl);
      if (resp.ok) {
        const buffer = await resp.arrayBuffer();
        const header = new Uint8Array(buffer.slice(0, 4));
        // Verify WebAssembly magic bytes: \0asm -> 0x00, 0x61, 0x73, 0x6d
        if (header[0] === 0x00 && header[1] === 0x61 && header[2] === 0x73 && header[3] === 0x6d) {
          wasmBinary = buffer;
        }
      }
    } catch (fetchErr) {
      console.warn('WASM binary direct fetch failed, trying standard loader:', fetchErr);
    }

    // 2. Initialize sql.js
    sqlEngine = await initSqlJs({
      locateFile: () => sqlWasmUrl,
      wasmBinary: wasmBinary || undefined
    });

    const savedBinary = localStorage.getItem('finance_invoices_db_bin');
    if (savedBinary) {
      try {
        const u8 = Uint8Array.from(atob(savedBinary), c => c.charCodeAt(0));
        sqliteDb = new sqlEngine.Database(u8);
      } catch (err) {
        sqliteDb = new sqlEngine.Database();
        seedData(sqliteDb, initialSeed);
      }
    } else {
      sqliteDb = new sqlEngine.Database();
      seedData(sqliteDb, initialSeed);
    }

    dbState.engineType = 'SQLite (WebAssembly)';
    usingFallback = false;
  } catch (wasmErr) {
    console.warn('SQLite WebAssembly failed to compile/load, activating resilient in-memory relational engine:', wasmErr);
    fallbackDb = new MemoryDatabase(initialSeed);
    dbState.engineType = 'In-Memory Relational Engine';
    usingFallback = true;
  }

  refreshCounts();
  dbState.ready = true;
  dbState.loading = false;
  return sqliteDb || fallbackDb;
}

function persistDb() {
  if (sqliteDb && !usingFallback) {
    try {
      const data = sqliteDb.export();
      let binary = '';
      const bytes = new Uint8Array(data);
      const len = bytes.byteLength;
      for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      localStorage.setItem('finance_invoices_db_bin', btoa(binary));
    } catch (err) {
      console.warn('Storage quota or persistence error:', err);
    }
  }
  refreshCounts();
}

function seedData(db, seed) {
  db.run(SCHEMA);
  db.run('DELETE FROM duplicate_flags;');
  db.run('DELETE FROM line_items;');
  db.run('DELETE FROM invoices;');

  // Insert invoices
  const invStmt = db.prepare(`
    INSERT INTO invoices (id, vendor_name, vendor_canonical, invoice_number, invoice_date, currency,
      subtotal, tax, total, total_inr, tax_type, status, source_file, blob_path, file_sha256,
      extraction_method, confidence, uploaded_by, uploaded_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `);

  for (const inv of seed.invoices) {
    invStmt.run([
      inv.id,
      inv.vendor_name,
      inv.vendor_canonical || inv.vendor_name,
      inv.invoice_number,
      inv.invoice_date,
      inv.currency,
      inv.subtotal,
      inv.tax,
      inv.total,
      inv.total_inr || (inv.total * (FX_TO_INR[inv.currency] || 1.0)),
      inv.tax_type,
      inv.status || 'Clean',
      inv.source_file,
      inv.blob_path,
      inv.file_sha256,
      inv.extraction_method,
      inv.confidence,
      inv.uploaded_by,
      inv.uploaded_at
    ]);
  }
  invStmt.free();

  // Insert line items
  const lineStmt = db.prepare(`
    INSERT INTO line_items (id, invoice_id, description, quantity, unit_price, amount)
    VALUES (?, ?, ?, ?, ?, ?)
  `);
  for (const item of seed.line_items) {
    lineStmt.run([
      item.id,
      item.invoice_id,
      item.description,
      item.quantity,
      item.unit_price,
      item.amount
    ]);
  }
  lineStmt.free();

  // Insert duplicate flags
  const flagStmt = db.prepare(`
    INSERT INTO duplicate_flags (id, invoice_id, matched_invoice_id, score, label, reasons, review_status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
  `);
  for (const flag of seed.duplicate_flags) {
    flagStmt.run([
      flag.id,
      flag.invoice_id,
      flag.matched_invoice_id,
      flag.score,
      flag.label,
      flag.reasons,
      flag.review_status || 'Open',
      flag.created_at
    ]);
  }
  flagStmt.free();
}

function refreshCounts() {
  try {
    const active = sqliteDb || fallbackDb;
    if (!active) return;
    const resInv = active.exec('SELECT count(*) FROM invoices')[0];
    dbState.invoicesCount = resInv ? resInv.values[0][0] : 0;
    const resFlag = active.exec('SELECT count(*) FROM duplicate_flags WHERE review_status = "Open"')[0];
    dbState.duplicateFlagsCount = resFlag ? resFlag.values[0][0] : 0;
    dbState.lastUpdated = Date.now();
  } catch (e) {
    console.error('Count refresh error:', e);
  }
}

/**
 * Validate and execute a read-only SELECT query
 */
export function runSql(sql) {
  const active = sqliteDb || fallbackDb;
  if (!active) throw new Error('Database is not initialized');

  const trimmed = sql.trim().replace(/;+$/, '');
  
  if (!/^\s*SELECT\b/i.test(trimmed)) {
    throw new Error('Security Violation: Only SELECT queries are permitted.');
  }

  const blocked = /\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|PRAGMA|EXEC|TRUNCATE)\b/i;
  if (blocked.test(trimmed)) {
    throw new Error('Security Violation: Query contains prohibited keyword.');
  }

  try {
    const results = active.exec(trimmed);
    if (!results || results.length === 0) {
      return { columns: [], rows: [] };
    }
    const { columns, values } = results[0];
    const rows = values.map(row => {
      const obj = {};
      columns.forEach((col, idx) => {
        obj[col] = row[idx];
      });
      return obj;
    });

    return { columns, rows, rawValues: values };
  } catch (err) {
    if (usingFallback || !fallbackDb) throw new Error(`SQL Execution Error: ${err.message}`);
    // If wasm exec failed, try fallback
    const fbRes = fallbackDb.exec(trimmed);
    if (!fbRes || fbRes.length === 0) return { columns: [], rows: [] };
    const { columns, values } = fbRes[0];
    const rows = values.map(row => {
      const obj = {};
      columns.forEach((col, idx) => { obj[col] = row[idx]; });
      return obj;
    });
    return { columns, rows, rawValues: values };
  }
}

export function getInvoices(filters = {}) {
  let query = 'SELECT * FROM invoices WHERE 1=1';
  if (filters.search) {
    query += ` AND (LOWER(vendor_name) LIKE '%${filters.search.toLowerCase()}%' OR LOWER(invoice_number) LIKE '%${filters.search.toLowerCase()}%')`;
  }
  if (filters.status && filters.status !== 'All') {
    query += ` AND status = '${filters.status}'`;
  }
  if (filters.currency && filters.currency !== 'All') {
    query += ` AND currency = '${filters.currency}'`;
  }

  query += ' ORDER BY id DESC';
  return runSql(query).rows;
}

export function getInvoiceById(id) {
  const inv = runSql(`SELECT * FROM invoices WHERE id = ${Number(id)}`).rows[0];
  if (!inv) return null;
  const items = runSql(`SELECT * FROM line_items WHERE invoice_id = ${Number(id)}`).rows;
  const flags = runSql(`
    SELECT df.*, orig.vendor_name as orig_vendor, orig.invoice_number as orig_inv_no, orig.total as orig_total
    FROM duplicate_flags df
    JOIN invoices orig ON orig.id = df.matched_invoice_id
    WHERE df.invoice_id = ${Number(id)}
  `).rows;
  return { ...inv, lineItems: items, flags };
}

export function getDuplicateFlagsWithDetails() {
  const query = `
    SELECT 
      df.id as flag_id,
      df.score,
      df.label,
      df.reasons,
      df.review_status,
      df.created_at,
      cur.id as invoice_id,
      cur.vendor_name as current_vendor,
      cur.invoice_number as current_invoice_no,
      cur.invoice_date as current_date,
      cur.total as current_total,
      cur.currency as current_currency,
      cur.status as current_status,
      cur.source_file as current_source,
      orig.id as orig_id,
      orig.vendor_name as orig_vendor,
      orig.invoice_number as orig_invoice_no,
      orig.invoice_date as orig_date,
      orig.total as orig_total,
      orig.currency as orig_currency,
      orig.status as orig_status,
      orig.source_file as orig_source
    FROM duplicate_flags df
    JOIN invoices cur ON cur.id = df.invoice_id
    JOIN invoices orig ON orig.id = df.matched_invoice_id
    ORDER BY df.score DESC, df.id DESC
  `;
  return runSql(query).rows;
}

export function updateFlagStatus(flagId, newStatus) {
  const active = sqliteDb || fallbackDb;
  if (!active) return;
  active.run(`UPDATE duplicate_flags SET review_status = ? WHERE id = ?`, [newStatus, flagId]);
  
  const flag = runSql(`SELECT invoice_id FROM duplicate_flags WHERE id = ${flagId}`).rows[0];
  if (flag) {
    const invStatus = newStatus === 'Confirmed duplicate' ? 'Confirmed duplicate' : 'Clean';
    active.run(`UPDATE invoices SET status = ? WHERE id = ?`, [invStatus, flag.invoice_id]);
  }
  
  persistDb();
}

export function addInvoice(invoiceData, lineItems = [], matches = []) {
  const totalInr = invoiceData.total_inr || (invoiceData.total * (FX_TO_INR[invoiceData.currency] || 1.0));
  const uploadedAt = new Date().toISOString().replace('T', ' ').slice(0, 19);

  let initialStatus = 'Clean';
  if (matches.length > 0) {
    initialStatus = matches[0].label;
  }

  if (usingFallback && fallbackDb) {
    const newId = fallbackDb.insertInvoice(invoiceData, lineItems, matches);
    persistDb();
    return newId;
  }

  sqliteDb.run(`
    INSERT INTO invoices (
      vendor_name, vendor_canonical, invoice_number, invoice_date, currency,
      subtotal, tax, total, total_inr, tax_type, status, source_file, blob_path,
      file_sha256, extraction_method, confidence, uploaded_by, uploaded_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `, [
    invoiceData.vendor_name,
    invoiceData.vendor_canonical || invoiceData.vendor_name,
    invoiceData.invoice_number,
    invoiceData.invoice_date,
    invoiceData.currency || 'INR',
    invoiceData.subtotal || invoiceData.total,
    invoiceData.tax || 0,
    invoiceData.total,
    totalInr,
    invoiceData.tax_type || 'GST',
    initialStatus,
    invoiceData.source_file || 'manual_upload.pdf',
    `local://${invoiceData.source_file || 'manual.pdf'}`,
    invoiceData.file_sha256 || 'manual_hash_' + Date.now(),
    invoiceData.extraction_method || 'Groq AI Document Parser',
    invoiceData.confidence || 0.98,
    'admin',
    uploadedAt
  ]);

  const newId = sqliteDb.exec('SELECT last_insert_rowid() as id')[0].values[0][0];

  if (lineItems && lineItems.length > 0) {
    const stmt = sqliteDb.prepare(`
      INSERT INTO line_items (invoice_id, description, quantity, unit_price, amount)
      VALUES (?, ?, ?, ?, ?)
    `);
    for (const item of lineItems) {
      stmt.run([newId, item.description, item.quantity || 1, item.unit_price || item.amount, item.amount]);
    }
    stmt.free();
  }

  for (const m of matches) {
    sqliteDb.run(`
      INSERT INTO duplicate_flags (invoice_id, matched_invoice_id, score, label, reasons, review_status, created_at)
      VALUES (?, ?, ?, ?, ?, 'Open', ?)
    `, [newId, m.matchedInvoiceId, m.score, m.label, m.reasons.join('; '), uploadedAt]);
  }

  persistDb();
  return newId;
}

export function resetToSampleData() {
  localStorage.removeItem('finance_invoices_db_bin');
  if (sqliteDb && !usingFallback) {
    seedData(sqliteDb, initialSeed);
  } else {
    fallbackDb = new MemoryDatabase(initialSeed);
  }
  persistDb();
}

export function getAnalytics() {
  const active = sqliteDb || fallbackDb;
  if (!active) return null;

  const totalInr = runSql('SELECT SUM(total_inr) as sum FROM invoices').rows[0]?.sum || 0;
  const count = runSql('SELECT COUNT(*) as count FROM invoices').rows[0]?.count || 0;
  const flagged = runSql('SELECT COUNT(*) as count FROM duplicate_flags WHERE review_status = "Open"').rows[0]?.count || 0;
  const avgSpend = count > 0 ? totalInr / count : 0;

  const spendByVendor = runSql(`
    SELECT vendor_canonical as vendor, ROUND(SUM(total_inr), 2) as spend_inr, COUNT(*) as invoice_count
    FROM invoices
    GROUP BY vendor_canonical
    ORDER BY spend_inr DESC
    LIMIT 6
  `).rows;

  const spendByCurrency = runSql(`
    SELECT currency, COUNT(*) as count, ROUND(SUM(total), 2) as total
    FROM invoices
    GROUP BY currency
  `).rows;

  const monthlySpend = runSql(`
    SELECT SUBSTR(invoice_date, 1, 7) as month, ROUND(SUM(total_inr), 2) as spend_inr
    FROM invoices
    WHERE invoice_date IS NOT NULL
    GROUP BY month
    ORDER BY month ASC
  `).rows;

  const statusBreakdown = runSql(`
    SELECT status, COUNT(*) as count
    FROM invoices
    GROUP BY status
  `).rows;

  return {
    totalInr,
    count,
    flagged,
    avgSpend,
    spendByVendor,
    spendByCurrency,
    monthlySpend,
    statusBreakdown
  };
}
