<template>
  <footer class="app-footer">
    <div class="footer-container">
      <!-- Left Column: Specs & Security -->
      <div class="footer-col">
        <div class="footer-brand">
          <span class="footer-logo">🧾</span>
          <span class="footer-title">FinSight AI</span>
          <span class="badge badge-clean">Audit-Grade Security</span>
        </div>
        <p class="footer-desc">
          Automated multi-factor invoice auditing, RapidFuzz duplicate prevention, and zero-compromise read-only SQL querying with Groq LLM intelligence.
        </p>
        <div class="security-pills">
          <span class="sec-pill">🔒 SELECT-Only Guard</span>
          <span class="sec-pill">⚡ SQLite WebAssembly</span>
          <span class="sec-pill">🚀 Groq LPU™ Engine</span>
        </div>
      </div>

      <!-- Center Column: Weights breakdown -->
      <div class="footer-col">
        <h4 class="col-title">Duplicate Detection Signals</h4>
        <div class="signal-list">
          <div class="signal-row">
            <span class="sig-name">Vendor Normalization & Token Ratio</span>
            <span class="sig-weight">35%</span>
          </div>
          <div class="signal-row">
            <span class="sig-name">Invoice Number & Digit Discrepancy</span>
            <span class="sig-weight">30%</span>
          </div>
          <div class="signal-row">
            <span class="sig-name">Amount Proximity (0.5% - 5.0%)</span>
            <span class="sig-weight">25%</span>
          </div>
          <div class="signal-row">
            <span class="sig-name">Date Proximity (0 - 30 days)</span>
            <span class="sig-weight">10%</span>
          </div>
        </div>
      </div>

      <!-- Right Column: System Status -->
      <div class="footer-col">
        <h4 class="col-title">System Architecture</h4>
        <div class="sys-item">
          <span class="sys-label">Active LLM Provider:</span>
          <span class="sys-val">Groq Cloud (OpenAI Compatible)</span>
        </div>
        <div class="sys-item">
          <span class="sys-label">Primary LLM Model:</span>
          <span class="sys-val code-tag">{{ activeModel }}</span>
        </div>
        <div class="sys-item">
          <span class="sys-label">Database Dialect:</span>
          <span class="sys-val">SQLite (WebAssembly)</span>
        </div>
        <div class="sys-item">
          <span class="sys-label">Demo FX Rate:</span>
          <span class="sys-val">1 GBP (£) = 110.00 INR (₹)</span>
        </div>
      </div>
    </div>

    <!-- Bottom Bar -->
    <div class="footer-bottom">
      <div class="bottom-container">
        <span>© 2026 AI Invoice Assistant & Finance Intelligence · Enterprise Edition</span>
        <span class="text-dim">All queries are strictly sandboxed and executed in read-only mode</span>
      </div>
    </div>
  </footer>
</template>

<script setup>
defineProps({
  activeModel: {
    type: String,
    default: 'openai/gpt-oss-120b'
  }
});
</script>

<style scoped>
.app-footer {
  margin-top: 60px;
  background: #060911;
  border-top: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 0.85rem;
}

.footer-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 40px 24px;
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  gap: 40px;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.footer-logo {
  font-size: 1.3rem;
}

.footer-title {
  font-weight: 700;
  font-size: 1.1rem;
  color: #FFFFFF;
}

.footer-desc {
  color: var(--text-dim);
  font-size: 0.82rem;
  line-height: 1.6;
  margin-bottom: 16px;
  max-width: 440px;
}

.security-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.sec-pill {
  font-size: 0.75rem;
  padding: 3px 10px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: #CBD5E1;
}

.col-title {
  color: #FFFFFF;
  font-size: 0.9rem;
  font-weight: 700;
  margin-bottom: 16px;
  letter-spacing: -0.01em;
}

.signal-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.signal-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  padding: 4px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.sig-name {
  color: var(--text-muted);
}

.sig-weight {
  font-family: var(--font-mono);
  font-weight: 600;
  color: #38BDF8;
}

.sys-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-bottom: 10px;
  font-size: 0.8rem;
}

.sys-label {
  color: var(--text-dim);
}

.sys-val {
  color: #E2E8F0;
  font-weight: 500;
}

.footer-bottom {
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding: 16px 24px;
  font-size: 0.78rem;
}

.bottom-container {
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

@media (max-width: 900px) {
  .footer-container {
    grid-template-columns: 1fr;
    gap: 30px;
  }
}
</style>
