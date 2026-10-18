<template>
  <div class="dashboard-view">
    <!-- Top KPI Cards -->
    <div class="kpi-grid">
      <!-- Total Spend -->
      <div class="kpi-card glass-panel">
        <div class="kpi-header">
          <span class="kpi-title">Total Spend (INR eq.)</span>
          <span class="kpi-icon">💰</span>
        </div>
        <div class="kpi-value money-val">{{ formatInr(analytics?.totalInr || 0) }}</div>
        <div class="kpi-footer">
          <span class="text-emerald">● Live Ledger</span>
          <span class="text-dim">Includes FX conversion</span>
        </div>
      </div>

      <!-- Total Invoices -->
      <div class="kpi-card glass-panel">
        <div class="kpi-header">
          <span class="kpi-title">Total Invoices</span>
          <span class="kpi-icon">🧾</span>
        </div>
        <div class="kpi-value">{{ analytics?.count || 0 }}</div>
        <div class="kpi-footer">
          <span class="badge badge-clean">100% Processed</span>
          <span class="text-dim">Across 11 vendors</span>
        </div>
      </div>

      <!-- Duplicate Alerts -->
      <div class="kpi-card glass-panel" :class="{ 'card-alert': (analytics?.flagged || 0) > 0 }">
        <div class="kpi-header">
          <span class="kpi-title">Duplicate Risk Flagged</span>
          <span class="kpi-icon">⚠️</span>
        </div>
        <div class="kpi-value text-rose">{{ analytics?.flagged || 0 }}</div>
        <div class="kpi-footer">
          <button class="kpi-link" @click="$emit('nav', 'duplicates')">
            Review in Auditor →
          </button>
        </div>
      </div>

      <!-- Average Invoice -->
      <div class="kpi-card glass-panel">
        <div class="kpi-header">
          <span class="kpi-title">Average Value</span>
          <span class="kpi-icon">📊</span>
        </div>
        <div class="kpi-value money-val">{{ formatInr(analytics?.avgSpend || 0) }}</div>
        <div class="kpi-footer">
          <span class="badge badge-currency">Per Document</span>
        </div>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="charts-grid">
      <!-- Top Vendors -->
      <div class="chart-panel glass-panel">
        <div class="panel-header">
          <div>
            <h3 class="panel-title">Top Vendors by Spend (INR)</h3>
            <p class="panel-desc">Aggregated across canonical supplier entities</p>
          </div>
          <button class="btn btn-secondary btn-xs" @click="$emit('ask-query', 'What are our top 5 vendors by spend in INR?')">
            ✨ Ask Groq
          </button>
        </div>

        <div class="vendor-bars">
          <div v-for="item in analytics?.spendByVendor || []" :key="item.vendor" class="vendor-bar-row">
            <div class="vendor-info">
              <span class="vendor-name">{{ item.vendor }}</span>
              <span class="vendor-spend money-val">{{ formatInr(item.spend_inr) }} ({{ item.invoice_count }} inv)</span>
            </div>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{ width: `${getVendorPercent(item.spend_inr)}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Monthly Trend -->
      <div class="chart-panel glass-panel">
        <div class="panel-header">
          <div>
            <h3 class="panel-title">Monthly Expenditure Trend</h3>
            <p class="panel-desc">Spending breakdown over time (YYYY-MM)</p>
          </div>
          <button class="btn btn-secondary btn-xs" @click="$emit('ask-query', 'Show monthly spending trend for all invoices')">
            ✨ Ask Groq
          </button>
        </div>

        <div class="monthly-bars">
          <div v-for="item in analytics?.monthlySpend || []" :key="item.month" class="month-col">
            <div class="month-bar-wrapper">
              <div
                class="month-bar"
                :style="{ height: `${getMonthHeight(item.spend_inr)}%` }"
                :title="`${item.month}: ${formatInr(item.spend_inr)}`"
              ></div>
            </div>
            <span class="month-label">{{ formatMonth(item.month) }}</span>
            <span class="month-val money-val">{{ formatCompact(item.spend_inr) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Row: Recent Invoices & Quick Prompt Starters -->
    <div class="bottom-grid">
      <!-- Recent Invoices Table -->
      <div class="recent-panel glass-panel">
        <div class="panel-header">
          <div>
            <h3 class="panel-title">Recent Invoices</h3>
            <p class="panel-desc">Latest ledger entries</p>
          </div>
          <button class="btn btn-secondary btn-xs" @click="$emit('nav', 'invoices')">
            View All {{ analytics?.count }} →
          </button>
        </div>

        <div class="table-responsive">
          <table class="data-table">
            <thead>
              <tr>
                <th>Vendor</th>
                <th>Invoice #</th>
                <th>Date</th>
                <th>Status</th>
                <th class="text-right">Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="inv in recentInvoices" :key="inv.id" class="clickable-row" @click="$emit('view-invoice', inv.id)">
                <td class="font-semibold">{{ inv.vendor_name }}</td>
                <td><span class="code-tag">{{ inv.invoice_number }}</span></td>
                <td class="text-dim">{{ inv.invoice_date }}</td>
                <td>
                  <span class="badge" :class="getStatusBadgeClass(inv.status)">
                    {{ inv.status }}
                  </span>
                </td>
                <td class="text-right money-val font-semibold">
                  {{ inv.currency === 'INR' ? '₹' : '£' }}{{ Number(inv.total).toLocaleString('en-IN', { minimumFractionDigits: 2 }) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Quick Groq Prompts Box -->
      <div class="groq-prompts-panel glass-panel">
        <div class="panel-header">
          <div>
            <h3 class="panel-title">✨ Groq AI Quick Questions</h3>
            <p class="panel-desc">Test natural language SQL reasoning</p>
          </div>
        </div>

        <div class="prompt-chips">
          <button
            v-for="p in samplePrompts"
            :key="p.text"
            class="prompt-chip"
            @click="$emit('ask-query', p.text)"
          >
            <span class="prompt-icon">{{ p.icon }}</span>
            <span class="prompt-text">{{ p.text }}</span>
          </button>
        </div>

        <div class="groq-perf-banner">
          <span class="pulse-dot"></span>
          <span>Groq LPU Inference active · ~500–1000 tokens/second</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  analytics: {
    type: Object,
    default: () => ({})
  },
  recentInvoices: {
    type: Array,
    default: () => []
  }
});

defineEmits(['nav', 'ask-query', 'view-invoice']);

const maxVendorSpend = computed(() => {
  if (!props.analytics?.spendByVendor?.length) return 1;
  return Math.max(...props.analytics.spendByVendor.map(v => v.spend_inr));
});

const maxMonthSpend = computed(() => {
  if (!props.analytics?.monthlySpend?.length) return 1;
  return Math.max(...props.analytics.monthlySpend.map(m => m.spend_inr));
});

function getVendorPercent(val) {
  return Math.min(100, Math.round((val / maxVendorSpend.value) * 100));
}

function getMonthHeight(val) {
  return Math.max(12, Math.min(100, Math.round((val / maxMonthSpend.value) * 100)));
}

function formatInr(num) {
  return '₹' + Number(num || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatCompact(num) {
  const n = Number(num || 0);
  if (n >= 10000000) return '₹' + (n / 10000000).toFixed(1) + 'Cr';
  if (n >= 100000) return '₹' + (n / 100000).toFixed(1) + 'L';
  if (n >= 1000) return '₹' + (n / 1000).toFixed(1) + 'k';
  return '₹' + n.toFixed(0);
}

function formatMonth(ym) {
  if (!ym) return '';
  const parts = ym.split('-');
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const mIdx = parseInt(parts[1], 10) - 1;
  return `${months[mIdx]} '${parts[0].slice(2)}`;
}

function getStatusBadgeClass(status) {
  if (status === 'Clean') return 'badge-clean';
  if (status === 'Likely duplicate') return 'badge-likely';
  if (status === 'Possible duplicate') return 'badge-possible';
  return 'badge-open';
}

const samplePrompts = [
  { icon: '🔍', text: 'How much did we spend with Infosphere this quarter?' },
  { icon: '⚠️', text: 'Show me all flagged duplicate invoices and reasons' },
  { icon: '🏆', text: 'What are our top 5 vendors by total expenditure in INR?' },
  { icon: '💱', text: 'What is the spending breakdown by currency?' },
  { icon: '📅', text: 'Show monthly spending trend in 2026' }
];
</script>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}

.kpi-card {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-alert {
  border-color: rgba(244, 63, 94, 0.4);
  background: rgba(244, 63, 94, 0.05);
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kpi-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--text-muted);
}

.kpi-icon {
  font-size: 1.3rem;
}

.kpi-value {
  font-size: 1.85rem;
  font-weight: 800;
  color: #FFFFFF;
  letter-spacing: -0.02em;
}

.kpi-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.78rem;
  margin-top: 4px;
}

.kpi-link {
  background: transparent;
  border: none;
  color: #FB7185;
  font-weight: 600;
  font-size: 0.8rem;
  cursor: pointer;
  padding: 0;
  transition: transform 0.2s;
}
.kpi-link:hover {
  text-decoration: underline;
  transform: translateX(2px);
}

.charts-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 20px;
}

.chart-panel {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.panel-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #FFFFFF;
}

.panel-desc {
  font-size: 0.8rem;
  color: var(--text-dim);
}

.btn-xs {
  padding: 5px 12px;
  font-size: 0.75rem;
}

.vendor-bars {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.vendor-bar-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.vendor-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.vendor-name {
  font-weight: 600;
  color: #E2E8F0;
}

.vendor-spend {
  color: #38BDF8;
  font-size: 0.8rem;
}

.bar-track {
  height: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #0EA5E9, #10B981);
  transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.monthly-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 200px;
  padding-top: 20px;
  gap: 10px;
}

.month-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  gap: 8px;
}

.month-bar-wrapper {
  flex: 1;
  width: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.month-bar {
  width: 70%;
  max-width: 32px;
  background: linear-gradient(180deg, #38BDF8 0%, rgba(14, 165, 233, 0.3) 100%);
  border-radius: 6px 6px 0 0;
  transition: height 0.6s cubic-bezier(0.16, 1, 0.3, 1);
  cursor: pointer;
}

.month-bar:hover {
  background: linear-gradient(180deg, #0284C7 0%, #10B981 100%);
}

.month-label {
  font-size: 0.75rem;
  color: var(--text-dim);
  font-weight: 600;
}

.month-val {
  font-size: 0.7rem;
  color: #94A3B8;
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 20px;
}

.recent-panel, .groq-prompts-panel {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.table-responsive {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.data-table th {
  text-align: left;
  padding: 10px 12px;
  color: var(--text-dim);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border-subtle);
}

.data-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.clickable-row {
  cursor: pointer;
  transition: background 0.15s;
}
.clickable-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.text-right {
  text-align: right;
}
.font-semibold {
  font-weight: 600;
}

.prompt-chips {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.prompt-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-subtle);
  color: #E2E8F0;
  text-align: left;
  font-size: 0.82rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.prompt-chip:hover {
  background: rgba(14, 165, 233, 0.1);
  border-color: rgba(14, 165, 233, 0.3);
  transform: translateX(3px);
  color: #38BDF8;
}

.groq-perf-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  background: rgba(249, 115, 22, 0.08);
  border: 1px solid rgba(249, 115, 22, 0.25);
  font-size: 0.75rem;
  color: #FB923C;
  font-weight: 600;
}

@media (max-width: 1000px) {
  .charts-grid, .bottom-grid {
    grid-template-columns: 1fr;
  }
}
</style>
