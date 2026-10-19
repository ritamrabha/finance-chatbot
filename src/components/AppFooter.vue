<template>
  <footer class="app-footer">
    <div class="footer-container">
      <!-- Left Column: Specs & Security -->
      <div class="footer-col">
        <div class="footer-brand">
          <div class="footer-logo">
            <HugeiconsIcon :icon="Invoice01Icon" :size="18" :stroke-width="1.8" color="#FFFFFF" />
          </div>
          <span class="footer-title">FinSight AI</span>
          <span class="badge">Audit-Grade</span>
        </div>
        <p class="footer-desc">
          Automated multi-factor invoice auditing, duplicate detection, and read-only financial intelligence powered by Groq LPU engine.
        </p>
        <div class="security-pills">
          <span class="sec-pill">
            <HugeiconsIcon :icon="ShieldCheckIcon" :size="13" :stroke-width="1.8" color="#FFFFFF" />
            <span>Read-Only Guard</span>
          </span>
          <span class="sec-pill">
            <HugeiconsIcon :icon="DatabaseIcon" :size="13" :stroke-width="1.8" color="#FFFFFF" />
            <span>SQLite Wasm</span>
          </span>
          <span class="sec-pill">
            <HugeiconsIcon :icon="CpuIcon" :size="13" :stroke-width="1.8" color="#FFFFFF" />
            <span>Groq LPU Speed</span>
          </span>
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
            <span class="sig-name">Invoice Number Discrepancy</span>
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
        <span>© 2026 FinSight AI · Enterprise Minimalist Edition</span>
        <span class="text-dim">All queries are strictly sandboxed and executed in read-only mode</span>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  Invoice01Icon,
  ShieldCheckIcon,
  DatabaseIcon,
  CpuIcon
} from '@hugeicons/core-free-icons';

defineProps({
  activeModel: {
    type: String,
    default: 'openai/gpt-oss-120b'
  }
});
</script>

<style scoped>
.app-footer {
  margin-top: 40px;
  background: #000000;
  border-top: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 0.85rem;
}

.footer-container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 36px 24px;
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  gap: 36px;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.footer-logo {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-xs);
  background: #141414;
  border: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}

.footer-title {
  font-weight: 700;
  font-size: 1.05rem;
  color: #FFFFFF;
}

.footer-desc {
  color: var(--text-dim);
  font-size: 0.8rem;
  line-height: 1.5;
  margin-bottom: 14px;
  max-width: 420px;
}

.security-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.sec-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  padding: 4px 10px;
  background: #0E0E0E;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  color: var(--text-muted);
}

.col-title {
  color: #FFFFFF;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 14px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.signal-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
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
  color: var(--text-dim);
}

.sig-weight {
  font-family: var(--font-mono);
  font-weight: 600;
  color: #FFFFFF;
}

.sys-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 10px;
  font-size: 0.8rem;
}

.sys-label {
  color: var(--text-dim);
}

.sys-val {
  color: #FFFFFF;
  font-weight: 500;
}

.footer-bottom {
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding: 14px 24px;
  font-size: 0.75rem;
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
    gap: 24px;
  }
}
</style>
