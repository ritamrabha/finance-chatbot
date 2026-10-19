import { runSql } from './db.js';

// Groq API key loaded from environment / .env
const DEFAULT_API_KEY = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_GROQ_API_KEY) || '';

export const GROQ_MODELS = [
  {
    id: 'openai/gpt-oss-120b',
    name: 'OpenAI GPT-OSS 120B',
    badge: 'Recommended',
    speed: '~500 t/s',
    context: '131K tokens',
    description: 'Flagship 120B model with deep financial reasoning and precision analytics.'
  },
  {
    id: 'openai/gpt-oss-20b',
    name: 'OpenAI GPT-OSS 20B',
    badge: 'Ultra Fast',
    speed: '~1000 t/s',
    context: '131K tokens',
    description: 'High-speed 20B parameter model with 1000 tokens/sec throughput.'
  },
  {
    id: 'qwen/qwen3.8-27b',
    name: 'Qwen 3.8 27B',
    badge: 'Multilingual',
    speed: '~450 t/s',
    context: '131K tokens',
    description: 'High performance instruction-following model by Alibaba Cloud.'
  }
];

export function getGroqApiKey() {
  return localStorage.getItem('finance_groq_api_key') || (typeof import.meta !== 'undefined' && import.meta.env?.VITE_GROQ_API_KEY) || DEFAULT_API_KEY;
}

export function setGroqApiKey(key) {
  if (key) {
    localStorage.setItem('finance_groq_api_key', key.trim());
  } else {
    localStorage.removeItem('finance_groq_api_key');
  }
}

const SCHEMA_DOC = `
Table invoices (one row per invoice)
  id INTEGER PK, vendor_name TEXT (as printed), vendor_canonical TEXT (grouped vendor name with spelling variants merged; ALWAYS use this to filter or GROUP BY vendor), invoice_number TEXT, invoice_date DATE (format YYYY-MM-DD),
  currency TEXT ('INR' or 'GBP'), subtotal NUMBER, tax NUMBER, total NUMBER (in invoice currency),
  total_inr NUMBER (total converted to Indian rupees; USE THIS to compare or sum across currencies),
  tax_type TEXT ('GST (IGST)', 'GST (CGST+SGST)', 'VAT'),
  status TEXT ('Clean', 'Possible duplicate', 'Likely duplicate', 'Confirmed duplicate'),
  source_file TEXT, uploaded_by TEXT, uploaded_at DATETIME

Table line_items (products/services on each invoice)
  id INTEGER PK, invoice_id INTEGER -> invoices.id, description TEXT, quantity NUMBER, unit_price NUMBER, amount NUMBER

Table duplicate_flags (pairs of invoices that look like duplicates)
  id INTEGER PK, invoice_id INTEGER -> invoices.id (suspected duplicate), matched_invoice_id INTEGER -> invoices.id (earlier original),
  score NUMBER (0-1), label TEXT ('Likely duplicate', 'Possible duplicate'), reasons TEXT, review_status TEXT ('Open', 'Confirmed duplicate', 'Not a duplicate')
`;

function getQuarterBounds(d = new Date()) {
  const m = d.getMonth();
  const q = Math.floor(m / 3);
  const start = new Date(d.getFullYear(), q * 3, 1).toISOString().slice(0, 10);
  const end = new Date(d.getFullYear(), (q + 1) * 3, 0).toISOString().slice(0, 10);
  return { start, end };
}

function buildSqlSystemPrompt() {
  const today = new Date().toISOString().slice(0, 10);
  const { start: qStart, end: qEnd } = getQuarterBounds();

  return `You are a careful finance data analyst. You translate a user's question about invoices into exactly ONE read-only SQLite SELECT query.

Database: SQLite. Dates are TEXT 'YYYY-MM-DD'. Use strftime('%Y', invoice_date), strftime('%m', invoice_date), date ranges with BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'. Use LIMIT n. Use LIKE with LOWER() for case-insensitive matching.
Today's date is ${today}. "This quarter" means calendar quarter ${qStart} to ${qEnd}.

Schema:
${SCHEMA_DOC}

Rules:
- Output ONLY a valid JSON object, with no markdown code blocks and no surrounding commentary, in this format:
  {"sql": "<one SELECT statement>", "chart": {"type": "bar" | "line" | "none", "x": "<column>", "y": "<column>"}, "cannot_answer": null}
- Only SELECT. Never write INSERT/UPDATE/DELETE/DROP/ALTER or PRAGMA. No comments.
- Only use tables: invoices, line_items, duplicate_flags.
- Give result columns friendly aliases (e.g. total_spend_inr, invoice_count).
- Match vendors using LOWER(vendor_canonical) LIKE '%keyword%'.
- When summing or comparing money across vendors or currencies, use total_inr. When showing individual invoices, show total and currency.
- For duplicate queries, join duplicate_flags to invoices twice (suspect and original).
- Keep results small: LIMIT 50.
- Use "chart" for comparisons or trends with 2+ rows (bar for categories, line for dates/months). Else "none".
- If the question cannot be answered from invoice data or asks to modify data, return:
  {"sql": null, "chart": {"type": "none"}, "cannot_answer": "<short polite reason>"}.
`;
}

const ANSWER_SYSTEM_PROMPT = `Explain the financial query result in one sentence maximum without using any '#' characters.`;

const ADVISOR_SYSTEM_PROMPT = `You are a concise financial loan assistant. Answer in one sentence maximum without using any '#' characters.`;

/**
 * Call Groq API via proxy or direct endpoint
 */
async function callGroqChat(messages, model, responseFormat = null) {
  const apiKey = getGroqApiKey();

  const payload = {
    model,
    messages,
    temperature: 0.1,
    max_tokens: 800
  };

  if (responseFormat) {
    payload.response_format = responseFormat;
  }

  const endpoints = ['/api/groq/chat/completions'];
  if (apiKey) {
    endpoints.push('https://api.groq.com/openai/v1/chat/completions');
  }

  let lastError = null;

  for (const url of endpoints) {
    try {
      const headers = {
        'Content-Type': 'application/json'
      };
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`;
      }

      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        const msg = errJson.error?.message || response.statusText;
        throw new Error(`Groq API Error (${response.status}): ${msg}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      lastError = err;
    }
  }

  throw lastError || new Error('Groq API Key is missing. Please set your Groq API key in the studio settings.');
}

export async function askFinancialAdvisor(question, history = [], model = 'openai/gpt-oss-120b') {
  const startTime = performance.now();
  const advisorMessages = [
    { role: 'system', content: ADVISOR_SYSTEM_PROMPT },
    ...history.slice(-3).map(h => ({
      role: h.role === 'user' ? 'user' : 'assistant',
      content: (h.text || h.content || '').replace(/#+/g, '').trim()
    })).filter(m => m.content),
    { role: 'user', content: question }
  ];

  try {
    const resp = await callGroqChat(advisorMessages, model);
    let text = resp.choices[0]?.message?.content?.trim() || 'You can share your name, PAN, and date of birth to check your pre-approved loan amount.';
    text = text.replace(/#+/g, '').trim();
    const firstSentence = text.split(/(?<=[.?!])\s+/)[0] || text;
    text = firstSentence.trim();

    return {
      text,
      sql: null,
      rows: [],
      columns: [],
      chart: { type: 'none' },
      executionTime: Math.round(performance.now() - startTime),
      usage: resp.usage || {},
      model
    };
  } catch (err) {
    return {
      text: 'Share your name, PAN number, and date of birth to check your pre-approved loan limit.',
      sql: null,
      rows: [],
      columns: [],
      chart: { type: 'none' },
      executionTime: Math.round(performance.now() - startTime),
      usage: {},
      model
    };
  }
}

/**
 * Main Question-Answering Pipeline
 */
export async function askFinanceAssistant(question, history = [], model = 'openai/gpt-oss-120b') {
  const startTime = performance.now();

  const messages = [
    { role: 'system', content: buildSqlSystemPrompt() }
  ];

  // Include recent conversation context
  for (const h of history.slice(-2)) {
    if (h.question && h.sql) {
      messages.push({ role: 'user', content: `Question: ${h.question}` });
      messages.push({ role: 'assistant', content: JSON.stringify({ sql: h.sql }) });
    }
  }

  messages.push({ role: 'user', content: `Question: <<<${question}>>>` });

  let rawJson = null;
  let sqlPlan = null;
  let groqUsage = null;

  // Step 1: Request SQL from Groq
  const planResp = await callGroqChat(messages, model, { type: 'json_object' });
  groqUsage = planResp.usage || {};
  const content = planResp.choices[0]?.message?.content || '{}';

  try {
    const match = content.match(/\{[\s\S]*\}/);
    sqlPlan = JSON.parse(match ? match[0] : content);
  } catch (e) {
    throw new Error('Groq did not return valid JSON for SQL generation: ' + content);
  }

  if (sqlPlan.cannot_answer || !sqlPlan.sql) {
    // Fallback to Financial Advisor response so the user NEVER receives a robotic refusal
    return await askFinancialAdvisor(question, history, model);
  }

  // Step 2: Execute SQL on SQLite WebAssembly
  let queryResult;
  try {
    queryResult = runSql(sqlPlan.sql);
  } catch (sqlErr) {
    // One retry attempt with error feedback
    messages.push({ role: 'assistant', content: JSON.stringify(sqlPlan) });
    messages.push({
      role: 'user',
      content: `Your previous query produced an error: ${sqlErr.message}. Please generate a corrected JSON object with valid SQLite syntax.`
    });

    const retryResp = await callGroqChat(messages, model, { type: 'json_object' });
    const retryContent = retryResp.choices[0]?.message?.content || '{}';
    const retryMatch = retryContent.match(/\{[\s\S]*\}/);
    sqlPlan = JSON.parse(retryMatch ? retryMatch[0] : retryContent);

    if (!sqlPlan.sql) {
      throw new Error('Unable to construct a valid query for this question.');
    }
    queryResult = runSql(sqlPlan.sql);
  }

  // Step 3: Send preview of rows back to Groq for financial explanation
  const rowPreview = queryResult.rows.slice(0, 25);
  const explainMessages = [
    { role: 'system', content: ANSWER_SYSTEM_PROMPT },
    {
      role: 'user',
      content: `Question: ${question}\n\nResult rows (${queryResult.rows.length} total):\n${JSON.stringify(rowPreview, null, 2)}`
    }
  ];

  const explainResp = await callGroqChat(explainMessages, model);
  let explanation = explainResp.choices[0]?.message?.content?.trim() || 'Found matching records.';
  explanation = explanation.replace(/#+/g, '').trim();
  const firstSentence = explanation.split(/(?<=[.?!])\s+/)[0] || explanation;
  explanation = firstSentence.trim();

  // Merge usage tokens
  if (explainResp.usage) {
    groqUsage = {
      prompt_tokens: (groqUsage.prompt_tokens || 0) + (explainResp.usage.prompt_tokens || 0),
      completion_tokens: (groqUsage.completion_tokens || 0) + (explainResp.usage.completion_tokens || 0),
      total_tokens: (groqUsage.total_tokens || 0) + (explainResp.usage.total_tokens || 0),
    };
  }

  const totalTime = Math.round(performance.now() - startTime);

  return {
    text: explanation,
    sql: sqlPlan.sql,
    rows: queryResult.rows,
    columns: queryResult.columns,
    chart: sqlPlan.chart || { type: 'none' },
    executionTime: totalTime,
    usage: groqUsage,
    model
  };
}

/**
 * Fetch available models from Groq
 */
export async function fetchLiveGroqModels() {
  const apiKey = getGroqApiKey();
  if (!apiKey) return GROQ_MODELS;

  try {
    const res = await fetch('/api/groq/models', {
      headers: { Authorization: `Bearer ${apiKey}` }
    });
    if (!res.ok) throw new Error('Models call failed');
    const data = await res.json();
    return data.data || GROQ_MODELS;
  } catch (e) {
    return GROQ_MODELS;
  }
}
