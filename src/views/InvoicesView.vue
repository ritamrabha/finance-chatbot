<template>
  <div class="invoices-view">
    <!-- Header & Filters Bar -->
    <div class="filter-bar glass-panel">
      <!-- Search Input -->
      <div class="search-wrap">
        <HugeiconsIcon :icon="Search01Icon" :size="16" :stroke-width="1.8" color="#71717A" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by vendor name, invoice number, keyword..."
          class="search-input"
        />
        <button v-if="searchQuery" class="clear-btn" @click="searchQuery = ''">✕</button>
      </div>

      <!-- Filters Group -->
      <div class="filter-controls">
        <!-- Status Filter -->
        <div class="filter-group">
          <label class="filter-label">Status:</label>
          <select v-model="statusFilter" class="filter-select">
            <option value="All">All Statuses ({{ allInvoices.length }})</option>
            <option value="Clean">Clean</option>
            <option value="Possible duplicate">Possible Duplicate</option>
            <option value="Likely duplicate">Likely Duplicate</option>
            <option value="Confirmed duplicate">Confirmed Duplicate</option>
          </select>
        </div>

        <!-- Currency Filter -->
        <div class="filter-group">
          <label class="filter-label">Currency:</label>
          <select v-model="currencyFilter" class="filter-select">
            <option value="All">All Currencies</option>
            <option value="INR">INR (₹)</option>
            <option value="GBP">GBP (£)</option>
          </select>
        </div>

        <!-- Export CSV Button -->
        <button class="btn btn-secondary btn-sm" @click="exportCsv">
          <HugeiconsIcon :icon="Download01Icon" :size="14" :stroke-width="1.8" color="#FFFFFF" />
          <span>Export CSV</span>
        </button>
      </div>
    </div>

    <!-- Invoices Table Panel -->
    <div class="table-panel glass-panel">
      <div class="panel-header">
        <div>
          <h2 class="panel-title">Invoices Ledger</h2>
          <p class="panel-desc">Showing {{ filteredInvoices.length }} of {{ allInvoices.length }} invoices</p>
        </div>
      </div>

      <div class="table-responsive">
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Vendor Name</th>
              <th>Invoice Number</th>
              <th>Date</th>
              <th>Status</th>
              <th>Currency</th>
              <th class="text-right">Subtotal</th>
              <th class="text-right">Tax</th>
              <th class="text-right">Total</th>
              <th class="text-right">Total (INR eq.)</th>
              <th class="text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="inv in filteredInvoices" :key="inv.id" class="ledger-row" @click="openInvoiceModal(inv.id)">
              <td class="text-dim">#{{ inv.id }}</td>
              <td class="font-semibold text-white">
                <div>{{ inv.vendor_name }}</div>
                <div v-if="inv.vendor_canonical !== inv.vendor_name" class="canonical-hint">
                  Canonical: {{ inv.vendor_canonical }}
                </div>
              </td>
              <td><span class="code-tag">{{ inv.invoice_number }}</span></td>
              <td class="text-dim">{{ inv.invoice_date }}</td>
              <td>
                <span class="badge" :class="getStatusBadgeClass(inv.status)">
                  {{ inv.status }}
                </span>
              </td>
              <td><span class="badge badge-currency">{{ inv.currency }}</span></td>
              <td class="text-right money-val text-dim">{{ formatMoney(inv.subtotal, inv.currency) }}</td>
              <td class="text-right money-val text-dim">{{ formatMoney(inv.tax, inv.currency) }}</td>
              <td class="text-right money-val font-semibold text-white">{{ formatMoney(inv.total, inv.currency) }}</td>
              <td class="text-right money-val text-cyan font-semibold">₹{{ formatNumber(inv.total_inr) }}</td>
              <td class="text-center" @click.stop>
                <button class="btn btn-secondary btn-xs" @click="openInvoiceModal(inv.id)">
                  Details →
                </button>
              </td>
            </tr>
            <tr v-if="filteredInvoices.length === 0">
              <td colspan="11" class="empty-state">
                No invoices found matching your search and filter criteria.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Invoice Details Modal -->
    <div v-if="selectedInvoice" class="modal-overlay" @click.self="selectedInvoice = null">
      <div class="modal-content glass-panel">
        <div class="modal-header">
          <div class="modal-title-group">
            <span class="badge badge-currency">{{ selectedInvoice.currency }}</span>
            <h3 class="modal-title">{{ selectedInvoice.vendor_name }}</h3>
            <span class="badge" :class="getStatusBadgeClass(selectedInvoice.status)">
              {{ selectedInvoice.status }}
            </span>
          </div>
          <button class="modal-close-btn" @click="selectedInvoice = null">✕</button>
        </div>

        <div class="modal-body">
          <!-- Summary Info Grid -->
          <div class="modal-info-grid">
            <div class="info-card">
              <span class="info-label">Invoice Number</span>
              <span class="info-value code-tag">{{ selectedInvoice.invoice_number }}</span>
            </div>
            <div class="info-card">
              <span class="info-label">Invoice Date</span>
              <span class="info-value">{{ selectedInvoice.invoice_date || 'N/A' }}</span>
            </div>
            <div class="info-card">
              <span class="info-label">Tax Type</span>
              <span class="info-value">{{ selectedInvoice.tax_type || 'Standard' }}</span>
            </div>
            <div class="info-card">
              <span class="info-label">Extraction Method</span>
              <span class="info-value">{{ selectedInvoice.extraction_method || 'Local Demo Extractor' }}</span>
            </div>
            <div class="info-card">
              <span class="info-label">Total Amount</span>
              <span class="info-value font-semibold text-white money-val">
                {{ formatMoney(selectedInvoice.total, selectedInvoice.currency) }}
              </span>
            </div>
            <div class="info-card">
              <span class="info-label">Total in INR</span>
              <span class="info-value font-semibold text-cyan money-val">
                ₹{{ formatNumber(selectedInvoice.total_inr) }}
              </span>
            </div>
          </div>

          <!-- Duplicate Alert Warning if present -->
          <div v-if="selectedInvoice.flags && selectedInvoice.flags.length > 0" class="modal-duplicate-box">
            <div class="dup-box-header">
              <HugeiconsIcon :icon="Alert02Icon" :size="18" :stroke-width="1.8" color="#FFFFFF" />
              <h4>Duplicate Detection Alert</h4>
              <span class="badge badge-likely">{{ selectedInvoice.flags[0].label }} ({{ (selectedInvoice.flags[0].score * 100).toFixed(0) }}% match)</span>
            </div>
            <p class="dup-reasons"><strong>Match Reasons:</strong> {{ selectedInvoice.flags[0].reasons }}</p>
            <div class="dup-orig-match">
              <span>Matched against Invoice <strong>#{{ selectedInvoice.flags[0].matched_invoice_id }}</strong> ({{ selectedInvoice.flags[0].orig_vendor }} · {{ selectedInvoice.flags[0].orig_inv_no }})</span>
            </div>
          </div>

          <!-- Line Items Table -->
          <div class="line-items-section">
            <h4 class="section-title">Line Items Breakdown</h4>
            <div class="table-responsive">
              <table class="data-table line-items-table">
                <thead>
                  <tr>
                    <th>Description</th>
                    <th class="text-right">Qty</th>
                    <th class="text-right">Unit Price</th>
                    <th class="text-right">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in selectedInvoice.lineItems" :key="item.id">
                    <td>{{ item.description }}</td>
                    <td class="text-right text-dim">{{ item.quantity || 1 }}</td>
                    <td class="text-right money-val text-dim">{{ formatMoney(item.unit_price, selectedInvoice.currency) }}</td>
                    <td class="text-right money-val font-semibold text-white">{{ formatMoney(item.amount, selectedInvoice.currency) }}</td>
                  </tr>
                  <tr v-if="!selectedInvoice.lineItems || selectedInvoice.lineItems.length === 0">
                    <td colspan="4" class="text-dim text-center py-4">No individual line items parsed for this invoice.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Actions -->
          <div class="modal-actions">
            <button class="btn btn-primary" @click="askGroqAboutInvoice">
              <HugeiconsIcon :icon="AiChat02Icon" :size="16" :stroke-width="1.8" color="#000000" />
              <span>Ask Groq AI about this Vendor</span>
            </button>
            <button class="btn btn-secondary" @click="selectedInvoice = null">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  Search01Icon,
  Download01Icon,
  Alert02Icon,
  AiChat02Icon
} from '@hugeicons/core-free-icons';
import { getInvoiceById } from '../services/db.js';

const props = defineProps({
  allInvoices: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['ask-query']);

const searchQuery = ref('');
const statusFilter = ref('All');
const currencyFilter = ref('All');
const selectedInvoice = ref(null);

const filteredInvoices = computed(() => {
  return props.allInvoices.filter(inv => {
    // Search filter
    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase();
      const matchVendor = (inv.vendor_name || '').toLowerCase().includes(q);
      const matchInvNo = (inv.invoice_number || '').toLowerCase().includes(q);
      const matchStatus = (inv.status || '').toLowerCase().includes(q);
      if (!matchVendor && !matchInvNo && !matchStatus) return false;
    }

    // Status filter
    if (statusFilter.value !== 'All' && inv.status !== statusFilter.value) {
      return false;
    }

    // Currency filter
    if (currencyFilter.value !== 'All' && inv.currency !== currencyFilter.value) {
      return false;
    }

    return true;
  });
});

function openInvoiceModal(id) {
  selectedInvoice.value = getInvoiceById(id);
}

function askGroqAboutInvoice() {
  if (!selectedInvoice.value) return;
  const vendor = selectedInvoice.value.vendor_canonical || selectedInvoice.value.vendor_name;
  emit('ask-query', `Show all invoices and total spend for ${vendor}`);
  selectedInvoice.value = null;
}

function formatMoney(amount, currency) {
  const sym = currency === 'INR' ? '₹' : '£';
  return sym + Number(amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatNumber(num) {
  return Number(num || 0).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function getStatusBadgeClass(status) {
  if (status === 'Clean') return 'badge-clean';
  if (status === 'Likely duplicate') return 'badge-likely';
  if (status === 'Possible duplicate') return 'badge-possible';
  if (status === 'Confirmed duplicate') return 'badge-likely';
  return 'badge-open';
}

function exportCsv() {
  const headers = ['ID', 'Vendor Name', 'Canonical', 'Invoice #', 'Date', 'Currency', 'Subtotal', 'Tax', 'Total', 'Total INR', 'Status'];
  const rows = filteredInvoices.value.map(i => [
    i.id,
    `"${(i.vendor_name || '').replace(/"/g, '""')}"`,
    `"${(i.vendor_canonical || '').replace(/"/g, '""')}"`,
    `"${i.invoice_number}"`,
    i.invoice_date,
    i.currency,
    i.subtotal,
    i.tax,
    i.total,
    i.total_inr,
    i.status
  ]);

  const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `invoices_export_${new Date().toISOString().slice(0, 10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
</script>

<style scoped>
.invoices-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-bar {
  padding: 16px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.search-wrap {
  flex: 1;
  min-width: 280px;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 14px;
  font-size: 0.9rem;
  color: var(--text-dim);
}

.search-input {
  width: 100%;
  padding: 10px 36px 10px 40px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  color: #FFFFFF;
  font-family: var(--font-sans);
  font-size: 0.9rem;
  outline: none;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 14px var(--primary-glow);
}

.clear-btn {
  position: absolute;
  right: 12px;
  background: transparent;
  border: none;
  color: var(--text-dim);
  cursor: pointer;
  font-size: 0.9rem;
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 0.8rem;
  color: var(--text-dim);
  font-weight: 600;
}

.filter-select {
  padding: 8px 14px;
  border-radius: var(--radius-md);
  background: #0F172A;
  border: 1px solid var(--border-subtle);
  color: #E2E8F0;
  font-family: var(--font-sans);
  font-size: 0.85rem;
  outline: none;
  cursor: pointer;
}

.table-panel {
  padding: 24px;
}

.panel-header {
  margin-bottom: 20px;
}

.panel-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #FFFFFF;
}

.panel-desc {
  font-size: 0.8rem;
  color: var(--text-dim);
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
  padding: 12px 14px;
  color: var(--text-dim);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border-subtle);
  white-space: nowrap;
}

.data-table td {
  padding: 13px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.ledger-row {
  cursor: pointer;
  transition: background 0.15s;
}

.ledger-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.canonical-hint {
  font-size: 0.72rem;
  color: var(--text-dim);
}

.text-white {
  color: #FFFFFF;
}
.text-cyan {
  color: #38BDF8;
}
.text-right {
  text-align: right;
}
.text-center {
  text-align: center;
}
.font-semibold {
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-dim);
  font-size: 0.9rem;
}

/* Modal Styling */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-subtle);
}

.modal-title-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #FFFFFF;
}

.modal-close-btn {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px;
}

.modal-close-btn:hover {
  color: #FFFFFF;
}

.modal-body {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.modal-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
}

.info-card {
  padding: 14px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 0.75rem;
  color: var(--text-dim);
}

.info-value {
  font-size: 0.95rem;
  color: #F1F5F9;
}

.modal-duplicate-box {
  padding: 16px 20px;
  border-radius: var(--radius-md);
  background: rgba(244, 63, 94, 0.08);
  border: 1px solid rgba(244, 63, 94, 0.35);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dup-box-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dup-box-header h4 {
  font-size: 0.95rem;
  color: #FDA4AF;
  font-weight: 700;
}

.dup-reasons {
  font-size: 0.85rem;
  color: #E2E8F0;
}

.dup-orig-match {
  font-size: 0.8rem;
  color: #FB7185;
}

.section-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 12px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border-subtle);
}
</style>
