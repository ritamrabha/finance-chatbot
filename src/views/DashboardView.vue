<template>
  <div class="dashboard-view">
    <!-- Top KPI Cards -->
    <div class="kpi-grid">
      <!-- Total Spend -->
      <div class="kpi-card glass-panel">
        <div class="kpi-header">
          <span class="kpi-title">Total Spend (INR eq.)</span>
          <div class="kpi-icon-wrap">
            <HugeiconsIcon :icon="Coins01Icon" :size="18" :stroke-width="1.8" color="#FFFFFF" />
          </div>
        </div>
        <div class="kpi-value money-val">{{ formatInr(analytics?.totalInr || 0) }}</div>
        <div class="kpi-footer">
          <span class="text-white">● Live Ledger</span>
          <span class="text-dim">Includes FX conversion</span>
        </div>
      </div>

      <!-- Total Invoices -->
      <div class="kpi-card glass-panel">
        <div class="kpi-header">
          <span class="kpi-title">Total Invoices</span>
          <div class="kpi-icon-wrap">
            <HugeiconsIcon :icon="Invoice01Icon" :size="18" :stroke-width="1.8" color="#FFFFFF" />
          </div>
        </div>
        <div class="kpi-value">{{ analytics?.count || 0 }}</div>
        <div class="kpi-footer">
          <span class="badge">100% Processed</span>
          <span class="text-dim">Across 11 suppliers</span>
        </div>
      </div>

      <!-- Duplicate Alerts -->
      <div class="kpi-card glass-panel" :class="{ 'card-alert': (analytics?.flagged || 0) > 0 }">
        <div class="kpi-header">
          <span class="kpi-title">Duplicate Risk Flagged</span>
          <div class="kpi-icon-wrap">
            <HugeiconsIcon :icon="Alert02Icon" :size="18" :stroke-width="1.8" color="#FFFFFF" />
          </div>
        </div>
        <div class="kpi-value">{{ analytics?.flagged || 0 }}</div>
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
          <div class="kpi-icon-wrap">
            <HugeiconsIcon :icon="DashboardSquare01Icon" :size="18" :stroke-width="1.8" color="#FFFFFF" />
          </div>
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
            <HugeiconsIcon :icon="AiChat02Icon" :size="14" :stroke-width="1.8" color="#FFFFFF" />
            <span>Ask Groq</span>
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
            <HugeiconsIcon :icon="AiChat02Icon" :size="14" :stroke-width="1.8" color="#FFFFFF" />
            <span>Ask Groq</span>
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
                <td class="font-semibold text-white">{{ inv.vendor_name }}</td>
                <td><span class="code-tag">{{ inv.invoice_number }}</span></td>
                <td class="text-dim">{{ inv.invoice_date }}</td>
                <td>
                  <span class="badge">
                    {{ inv.status }}
                  </span>
                </td>
                <td class="text-right money-val font-semibold text-white">
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
            <h3 class="panel-title">Groq AI Financial Queries</h3>
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
            <HugeiconsIcon :icon="p.icon" :size="16" :stroke-width="1.8" color="#FFFFFF" />
            <span class="prompt-text">{{ p.text }}</span>
          </button>
        </div>

        <div class="groq-perf-banner">
          <span class="pulse-dot"></span>
          <span>Groq LPU Inference active · ~500–1000 tokens/sec throughput</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  Coins01Icon,
  Invoice01Icon,
  Alert02Icon,
  DashboardSquare01Icon,
  AiChat02Icon,
  Search01Icon,
  Calendar01Icon,
  FilterIcon
} from '@hugeicons/core-free-icons';

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

const samplePrompts = [
  { icon: Search01Icon, text: 'How much did we spend with Infosphere this quarter?' },
  { icon: Alert02Icon, text: 'Show me all flagged duplicate invoices and reasons' },
  { icon: Coins01Icon, text: 'What are our top 5 vendors by total expenditure in INR?' },
  { icon: FilterIcon, text: 'What is the spending breakdown by currency?' },
  { icon: Calendar01Icon, text: 'Show monthly spending trend in 2026' }
];
</script>

<style scoped>
.dashboard-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.kpi-card {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-alert {
  border-color: rgba(255, 255, 255, 0.25);
  background: #141414;
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kpi-title {
  font-size: 0.825rem;
  font-weight: 500;
  color: var(--text-muted);
}

.kpi-icon-wrap {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-xs);
  background: #141414;
  border: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}

.kpi-value {
  font-size: 1.75rem;
  font-weight: 700;
  color: #FFFFFF;
  letter-spacing: -0.02em;
}

.kpi-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  margin-top: 4px;
}

.kpi-link {
  background: transparent;
  border: none;
  color: #FFFFFF;
  font-weight: 500;
  font-size: 0.78rem;
  cursor: pointer;
  padding: 0;
}
.kpi-link:hover {
  text-decoration: underline;
}

.charts-grid {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 20px;
}

.chart-panel {
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.panel-title {
  font-size: 0.95rem;
  font-weight: 600;
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
  gap: 12px;
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
  font-size: 0.825rem;
}

.vendor-name {
  font-weight: 500;
  color: #E2E8F0;
}

.vendor-spend {
  color: var(--text-muted);
  font-size: 0.78rem;
}

.bar-track {
  height: 6px;
  background: #18181B;
  border-radius: 9999px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 9999px;
  background: #FFFFFF;
  transition: width 0.4s ease;
}

.monthly-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 190px;
  padding-top: 16px;
  gap: 8px;
}

.month-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  gap: 6px;
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
  max-width: 28px;
  background: #27272A;
  border-radius: 4px 4px 0 0;
  transition: height 0.4s ease, background 0.15s ease;
  cursor: pointer;
}

.month-bar:hover {
  background: #FFFFFF;
}

.month-label {
  font-size: 0.7rem;
  color: var(--text-dim);
  font-weight: 500;
}

.month-val {
  font-size: 0.65rem;
  color: var(--text-muted);
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 20px;
}

.recent-panel, .groq-prompts-panel {
  padding: 22px;
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
  font-size: 0.825rem;
}

.data-table th {
  text-align: left;
  padding: 8px 10px;
  color: var(--text-dim);
  font-size: 0.725rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border-subtle);
}

.data-table td {
  padding: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.clickable-row {
  cursor: pointer;
  transition: background 0.15s;
}
.clickable-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.prompt-chips {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.prompt-chip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: #141414;
  border: 1px solid var(--border-subtle);
  color: #E2E8F0;
  text-align: left;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.prompt-chip:hover {
  background: #1F1F1F;
  border-color: rgba(255, 255, 255, 0.2);
  color: #FFFFFF;
}

.groq-perf-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  border-radius: var(--radius-sm);
  background: #121212;
  border: 1px solid var(--border-subtle);
  font-size: 0.75rem;
  color: var(--text-muted);
}

@media (max-width: 1000px) {
  .charts-grid, .bottom-grid {
    grid-template-columns: 1fr;
  }
}
</style>
