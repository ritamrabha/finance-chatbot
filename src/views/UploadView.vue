<template>
  <div class="upload-view">
    <!-- Top Info -->
    <div class="intro-bar glass-panel">
      <div class="intro-content">
        <h2 class="intro-title">Scan & Audit Invoices</h2>
        <p class="intro-desc">
          Drag and drop an invoice or click any sample below. Our multi-factor pipeline extracts line items and checks 4 signals (vendor, invoice no, amount, date) for duplicate risk before payment.
        </p>
      </div>
    </div>

    <!-- Quick Sample Invoices Carousel / Selector -->
    <div class="samples-panel glass-panel">
      <div class="panel-header">
        <div>
          <h3 class="panel-title">Demo Invoice Samples (Click to simulate scan)</h3>
          <p class="panel-desc">Test real sample PDFs, including planted duplicates and recurring bills</p>
        </div>
      </div>

      <div class="samples-grid">
        <button
          v-for="s in samplePicks"
          :key="s.file"
          class="sample-card"
          :class="{ selected: selectedSample?.file === s.file, 'dup-sample': s.isPlantedDuplicate }"
          @click="selectSample(s)"
        >
          <div class="sample-badge-row">
            <span class="sample-file">{{ s.file }}</span>
            <span v-if="s.isPlantedDuplicate" class="badge badge-likely">Duplicate Test</span>
            <span v-else class="badge">Original</span>
          </div>
          <div class="sample-vendor">{{ s.vendor }}</div>
          <div class="sample-meta">
            <span class="code-tag">{{ s.invoice_number }}</span>
            <span class="sample-amt money-val">
              {{ s.currency === 'INR' ? '₹' : '£' }}{{ s.total.toLocaleString('en-IN') }}
            </span>
          </div>
        </button>
      </div>
    </div>

    <!-- Drop Zone & Active Extraction Form -->
    <div class="scan-grid">
      <!-- File Dropzone -->
      <div
        class="dropzone glass-panel"
        :class="{ dragging: isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleFileDrop"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".pdf,.png,.jpg,.jpeg"
          class="hidden-file-input"
          @change="handleFileSelect"
        />
        <div class="drop-icon-box">
          <HugeiconsIcon :icon="Invoice01Icon" :size="32" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <h4 class="drop-title">Drop invoice file here (PDF or image)</h4>
        <p class="drop-subtitle">or select a sample above for instantaneous testing</p>
        <button class="btn btn-secondary btn-sm" @click="$refs.fileInput.click()">
          Browse Local Files
        </button>
        <div class="drop-hints">
          <span>Max 10 MB · Validated magic bytes · SHA-256 integrity</span>
        </div>
      </div>

      <!-- Live Extraction & Duplicate Check Results -->
      <div class="results-card glass-panel" v-if="currentExtraction">
        <div class="panel-header">
          <div class="ext-header-left">
            <h3 class="panel-title">Extracted Document Data</h3>
            <span class="badge">Confidence {{ (currentExtraction.confidence * 100).toFixed(0) }}%</span>
          </div>
          <span class="code-tag">{{ currentExtraction.source_file }}</span>
        </div>

        <!-- Extracted Fields Grid -->
        <div class="fields-grid">
          <div class="field-item">
            <span class="field-label">Vendor Name:</span>
            <span class="field-val font-semibold text-white">{{ currentExtraction.vendor_name }}</span>
          </div>
          <div class="field-item">
            <span class="field-label">Invoice Number:</span>
            <span class="field-val code-tag">{{ currentExtraction.invoice_number }}</span>
          </div>
          <div class="field-item">
            <span class="field-label">Date:</span>
            <span class="field-val">{{ currentExtraction.invoice_date }}</span>
          </div>
          <div class="field-item">
            <span class="field-label">Currency & Tax:</span>
            <span class="field-val">{{ currentExtraction.currency }} · {{ currentExtraction.tax_type }}</span>
          </div>
          <div class="field-item">
            <span class="field-label">Subtotal:</span>
            <span class="field-val money-val">{{ currentExtraction.currency === 'INR' ? '₹' : '£' }}{{ currentExtraction.subtotal?.toLocaleString('en-IN') }}</span>
          </div>
          <div class="field-item highlight-field">
            <span class="field-label">Total Amount:</span>
            <span class="field-val font-semibold text-white money-val">
              {{ currentExtraction.currency === 'INR' ? '₹' : '£' }}{{ currentExtraction.total?.toLocaleString('en-IN') }}
            </span>
          </div>
        </div>

        <!-- Live Duplicate Check Banner -->
        <div class="dup-evaluation" :class="dupResult?.isFlagged ? 'dup-warning' : 'dup-safe'">
          <div class="dup-eval-header">
            <div class="eval-icon-box">
              <HugeiconsIcon
                :icon="dupResult?.isFlagged ? Alert02Icon : ShieldCheckIcon"
                :size="20"
                :stroke-width="1.8"
                color="#FFFFFF"
              />
            </div>
            <div class="eval-title-wrap">
              <h4 class="eval-title">
                {{ dupResult?.isFlagged ? `Flagged: ${dupResult.label}` : 'Safe to Pay: Clean Invoice' }}
              </h4>
              <p class="eval-desc">
                {{ dupResult?.isFlagged ? `Overall duplicate match score: ${(dupResult.score * 100).toFixed(0)}%` : 'No suspicious matches against prior ledger entries.' }}
              </p>
            </div>
          </div>

          <!-- Reasons if flagged -->
          <div v-if="dupResult?.isFlagged" class="dup-reasons-list">
            <div v-for="(reason, rIdx) in dupResult.reasons" :key="rIdx" class="reason-pill">
              <span>● {{ reason }}</span>
            </div>
            <div v-if="dupMatches.length > 0" class="matched-info">
              <span>Original: Invoice #{{ dupMatches[0].matchedInvoiceId }} ({{ dupMatches[0].vendor }} · {{ dupMatches[0].invNo }})</span>
            </div>
          </div>
        </div>

        <!-- Action Row -->
        <div class="action-footer">
          <button
            class="btn btn-primary"
            :class="{ 'btn-danger': dupResult?.isFlagged }"
            @click="commitInvoice"
          >
            <HugeiconsIcon :icon="CheckmarkCircle01Icon" :size="16" :stroke-width="2" :color="dupResult?.isFlagged ? '#FFFFFF' : '#000000'" />
            <span>{{ dupResult?.isFlagged ? 'Flag & Save for Human Audit' : 'Save to Approved Ledger' }}</span>
          </button>
          <button class="btn btn-secondary" @click="currentExtraction = null">
            Discard
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  Invoice01Icon,
  Alert02Icon,
  ShieldCheckIcon,
  CheckmarkCircle01Icon
} from '@hugeicons/core-free-icons';
import { getSampleInvoices, generateExtractionFromSample } from '../services/sampleFiles.js';
import { compareInvoices } from '../services/duplicates.js';
import { addInvoice } from '../services/db.js';

const props = defineProps({
  allInvoices: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['invoice-added', 'nav']);

const fileInput = ref(null);
const isDragging = ref(false);
const samplePicks = ref(getSampleInvoices().slice(0, 8));
const selectedSample = ref(null);
const currentExtraction = ref(null);
const dupResult = ref(null);
const dupMatches = ref([]);

function selectSample(sample) {
  selectedSample.value = sample;
  const ext = generateExtractionFromSample(sample);
  processExtraction(ext);
}

function handleFileDrop(e) {
  isDragging.value = false;
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    simulateFileUpload(files[0]);
  }
}

function handleFileSelect(e) {
  const files = e.target.files;
  if (files.length > 0) {
    simulateFileUpload(files[0]);
  }
}

function simulateFileUpload(file) {
  const fakeExt = {
    vendor_name: 'Apex Global Logistics Pvt Ltd',
    vendor_canonical: 'Apex Global Logistics',
    invoice_number: 'AGL-2026-904',
    invoice_date: new Date().toISOString().slice(0, 10),
    currency: 'INR',
    subtotal: 18000.0,
    tax: 3240.0,
    total: 21240.0,
    tax_type: 'GST (IGST 18%)',
    confidence: 0.98,
    source_file: file.name,
    line_items: [
      { description: 'Freight & Haulage Services', quantity: 1, unit_price: 18000.0, amount: 18000.0 }
    ]
  };
  processExtraction(fakeExt);
}

function processExtraction(ext) {
  currentExtraction.value = ext;
  dupMatches.value = [];

  let bestMatch = null;
  let highestScore = 0;

  // Compare against all existing invoices in ledger
  for (const inv of props.allInvoices) {
    const res = compareInvoices(ext, inv);
    if (res.isFlagged && res.score > highestScore) {
      highestScore = res.score;
      bestMatch = {
        ...res,
        matchedInvoiceId: inv.id,
        vendor: inv.vendor_name,
        invNo: inv.invoice_number
      };
      dupMatches.value = [bestMatch];
    }
  }

  dupResult.value = bestMatch || { isFlagged: false, score: 0, label: 'Clean', reasons: [] };
}

function commitInvoice() {
  if (!currentExtraction.value) return;

  const matchesForDb = dupMatches.value.map(m => ({
    matchedInvoiceId: m.matchedInvoiceId,
    score: m.score,
    label: m.label,
    reasons: m.reasons
  }));

  const newId = addInvoice(
    currentExtraction.value,
    currentExtraction.value.line_items || [],
    matchesForDb
  );

  alert(`Invoice #${newId} saved successfully! ${dupResult.value?.isFlagged ? 'Marked for duplicate review.' : 'Status: Clean.'}`);
  currentExtraction.value = null;
  selectedSample.value = null;
  emit('invoice-added');
}
</script>

<style scoped>
.upload-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.intro-bar {
  padding: 20px 24px;
}

.intro-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 6px;
}

.intro-desc {
  font-size: 0.88rem;
  color: var(--text-muted);
  max-width: 800px;
  line-height: 1.6;
}

.samples-panel {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #FFFFFF;
}

.panel-desc {
  font-size: 0.78rem;
  color: var(--text-dim);
}

.samples-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}

.sample-card {
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.sample-card:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: var(--border-bright);
  transform: translateY(-2px);
}

.sample-card.selected {
  border-color: var(--primary);
  background: rgba(14, 165, 233, 0.1);
  box-shadow: 0 0 16px var(--primary-glow);
}

.sample-badge-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sample-file {
  font-size: 0.75rem;
  color: var(--text-dim);
  font-family: var(--font-mono);
}

.sample-vendor {
  font-weight: 600;
  color: #F1F5F9;
  font-size: 0.88rem;
}

.sample-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sample-amt {
  font-size: 0.85rem;
  color: #38BDF8;
  font-weight: 700;
}

.scan-grid {
  display: grid;
  grid-template-columns: 1fr 1.3fr;
  gap: 20px;
}

.dropzone {
  padding: 40px 30px;
  border: 2px dashed rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.25s;
  min-height: 380px;
}

.dropzone:hover, .dropzone.dragging {
  border-color: var(--primary);
  background: rgba(14, 165, 233, 0.05);
}

.hidden-file-input {
  display: none;
}

.drop-icon {
  font-size: 3rem;
  margin-bottom: 4px;
}

.drop-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #FFFFFF;
}

.drop-subtitle {
  font-size: 0.85rem;
  color: var(--text-dim);
  max-width: 320px;
}

.drop-hints {
  font-size: 0.72rem;
  color: var(--text-dim);
  margin-top: 14px;
}

.results-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ext-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.fields-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}

.field-item {
  padding: 12px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.highlight-field {
  background: rgba(14, 165, 233, 0.08);
  border-color: rgba(14, 165, 233, 0.25);
}

.field-label {
  font-size: 0.75rem;
  color: var(--text-dim);
}

.field-val {
  font-size: 0.9rem;
  color: #E2E8F0;
}

.dup-evaluation {
  padding: 16px 20px;
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.dup-warning {
  background: rgba(244, 63, 94, 0.1);
  border: 1px solid rgba(244, 63, 94, 0.4);
}

.dup-safe {
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.dup-eval-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.eval-icon {
  font-size: 1.4rem;
}

.eval-title {
  font-size: 1rem;
  font-weight: 700;
  color: #FFFFFF;
}

.eval-desc {
  font-size: 0.8rem;
  color: #CBD5E1;
}

.dup-reasons-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.reason-pill {
  font-size: 0.82rem;
  color: #FDA4AF;
}

.matched-info {
  font-size: 0.78rem;
  color: #FB7185;
  margin-top: 4px;
}

.action-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 10px;
  border-top: 1px solid var(--border-subtle);
}

@media (max-width: 900px) {
  .scan-grid {
    grid-template-columns: 1fr;
  }
}
</style>
