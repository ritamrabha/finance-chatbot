/**
 * Duplicate invoice detection with fuzzy matching.
 * Port of app/duplicates.py logic:
 *   - Vendor name: 35%
 *   - Invoice number: 30% (capped at 0.5 if digits differ)
 *   - Amount: 25% (exact within 0.5%, zero at 5%)
 *   - Date: 10% (1.0 on same day, zero at 30 days)
 * Decision:
 *   - >= 0.90: Likely duplicate
 *   - >= 0.80: Possible duplicate
 */

const WEIGHTS = { vendor: 0.35, invoice_number: 0.30, amount: 0.25, date: 0.10 };
const LIKELY_THRESHOLD = 0.90;
const POSSIBLE_THRESHOLD = 0.80;
const VENDOR_GATE = 0.75;
const AMOUNT_EXACT_TOL = 0.005;
const AMOUNT_ZERO_AT = 0.05;
const DATE_ZERO_AT_DAYS = 30;

const SUFFIXES = new Set([
  'pvt', 'private', 'ltd', 'limited', 'llp', 'llc', 'inc', 'incorporated', 'plc',
  'co', 'company', 'corp', 'corporation', 'the', 'and', 'industries', 'inds', 'ind'
]);

export function normalizeVendor(name) {
  let s = (name || '').toLowerCase().replace(/&/g, ' and ');
  // Collapse dotted initials like a.b.c. -> abc
  s = s.replace(/\b(?:[a-z]\.){2,}/g, (m) => m.replace(/\./g, ''));
  s = s.replace(/[^a-z0-9 ]+/g, ' ');
  const tokens = s.split(/\s+/).filter(t => t && !SUFFIXES.has(t));
  return tokens.join(' ');
}

export function normalizeInvoiceNumber(num) {
  const s = (num || '').toUpperCase();
  const parts = s.match(/[A-Z]+|\d+/g) || [];
  return parts.map(p => {
    if (/^\d+$/.test(p)) {
      return p.replace(/^0+/, '') || '0';
    }
    return p;
  }).join('');
}

function extractDigits(normNum) {
  return normNum.replace(/\D/g, '');
}

/**
 * Levenshtein distance
 */
function levenshteinDistance(s1, s2) {
  const m = s1.length;
  const n = s2.length;
  const dp = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));

  for (let i = 0; i <= m; i++) dp[i][0] = i;
  for (let j = 0; j <= n; j++) dp[0][j] = j;

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (s1[i - 1] === s2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1];
      } else {
        dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
      }
    }
  }
  return dp[m][n];
}

function fuzzyRatio(s1, s2) {
  if (!s1 && !s2) return 1.0;
  if (!s1 || !s2) return 0.0;
  if (s1 === s2) return 1.0;
  const maxLen = Math.max(s1.length, s2.length);
  if (maxLen === 0) return 1.0;
  const dist = levenshteinDistance(s1, s2);
  return Math.max(0, 1 - dist / maxLen);
}

function tokenSortRatio(s1, s2) {
  const t1 = s1.split(/\s+/).filter(Boolean).sort().join(' ');
  const t2 = s2.split(/\s+/).filter(Boolean).sort().join(' ');
  return fuzzyRatio(t1, t2);
}

export function vendorSimilarity(a, b) {
  const na = normalizeVendor(a);
  const nb = normalizeVendor(b);
  if (!na || !nb) return 0.0;
  return tokenSortRatio(na, nb);
}

export function invoiceNumberSimilarity(a, b) {
  const na = normalizeInvoiceNumber(a);
  const nb = normalizeInvoiceNumber(b);
  if (!na || !nb) return 0.0;
  if (na === nb) return 1.0;
  let sim = fuzzyRatio(na, nb);
  if (extractDigits(na) !== extractDigits(nb)) {
    sim = Math.min(sim, 0.5); // different digits = different invoices
  }
  return sim;
}

export function amountSimilarity(a, b) {
  if (a == null || b == null) return 0.0;
  const numA = Number(a);
  const numB = Number(b);
  const hi = Math.max(Math.abs(numA), Math.abs(numB));
  if (hi === 0) return 1.0;
  const diff = Math.abs(numA - numB) / hi;
  if (diff <= AMOUNT_EXACT_TOL) return 1.0;
  if (diff >= AMOUNT_ZERO_AT) return 0.0;
  return 1 - (diff - AMOUNT_EXACT_TOL) / (AMOUNT_ZERO_AT - AMOUNT_EXACT_TOL);
}

export function dateSimilarity(a, b) {
  if (!a || !b) return 0.5; // neutral if unknown
  const da = new Date(String(a).slice(0, 10));
  const db = new Date(String(b).slice(0, 10));
  if (isNaN(da.getTime()) || isNaN(db.getTime())) return 0.5;
  const diffDays = Math.abs((da - db) / (1000 * 60 * 60 * 24));
  return Math.max(0.0, 1 - diffDays / DATE_ZERO_AT_DAYS);
}

/**
 * Compare two invoices
 */
export function compareInvoices(invA, invB) {
  if ((invA.currency || '').toUpperCase() !== (invB.currency || '').toUpperCase()) {
    return { score: 0.0, label: 'No match', isFlagged: false, reasons: ['Different currency'], parts: {} };
  }

  const v = vendorSimilarity(invA.vendor_name, invB.vendor_name);
  if (v < VENDOR_GATE) {
    return { score: 0.0, label: 'No match', isFlagged: false, reasons: ['Different vendor'], parts: { vendor: v } };
  }

  const parts = {
    vendor: v,
    invoice_number: invoiceNumberSimilarity(invA.invoice_number, invB.invoice_number),
    amount: amountSimilarity(invA.total, invB.total),
    date: dateSimilarity(invA.invoice_date, invB.invoice_date),
  };

  let score = WEIGHTS.vendor * parts.vendor +
              WEIGHTS.invoice_number * parts.invoice_number +
              WEIGHTS.amount * parts.amount +
              WEIGHTS.date * parts.date;

  const sameNumberRule = v >= 0.90 && parts.invoice_number === 1.0;
  if (sameNumberRule) {
    score = Math.max(score, POSSIBLE_THRESHOLD);
  }

  const reasons = [];
  reasons.push(v >= 0.97 ? 'Same vendor' : `Vendor names ${Math.round(v * 100)}% similar`);
  
  if (parts.invoice_number === 1.0) {
    reasons.push(invA.invoice_number === invB.invoice_number ? 'Same invoice number' : 'Same invoice number (different formatting)');
  } else if (parts.invoice_number <= 0.5) {
    reasons.push('Different invoice number');
  }

  if (sameNumberRule && parts.amount < 1.0) {
    reasons.push('Same vendor and invoice number but different amount - possible revised invoice');
  }

  if (parts.amount === 1.0) {
    reasons.push('Same amount');
  } else if (parts.amount > 0.8) {
    reasons.push(`Amount differs by ~${Math.abs(Number(invA.total) - Number(invB.total)).toFixed(2)}`);
  }

  if (parts.date === 1.0) {
    reasons.push('Same date');
  } else if (parts.date > 0.5) {
    reasons.push('Dates within 15 days');
  }

  let label = 'No match';
  if (score >= LIKELY_THRESHOLD) {
    label = 'Likely duplicate';
  } else if (score >= POSSIBLE_THRESHOLD) {
    label = 'Possible duplicate';
  }

  return {
    score: Math.min(1.0, Math.max(0.0, score)),
    label,
    isFlagged: score >= POSSIBLE_THRESHOLD,
    parts,
    reasons
  };
}
