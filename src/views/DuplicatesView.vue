<template>
  <div class="duplicates-view">
    <!-- Header -->
    <div class="audit-header glass-panel">
      <div class="header-left">
        <h2 class="audit-title">Duplicate Invoice Auditor</h2>
        <p class="audit-desc">
          Automated RapidFuzz detection flags duplicate invoices before payments are released. Compare suspected duplicates side-by-side with original entries.
        </p>
      </div>

      <div class="filter-pills">
        <button
          v-for="st in ['All', 'Open', 'Confirmed duplicate', 'Not a duplicate']"
          :key="st"
          class="pill-btn"
          :class="{ active: activeStatusFilter === st }"
          @click="activeStatusFilter = st"
        >
          {{ st }}
        </button>
      </div>
    </div>

    <!-- Flagged Pairs List -->
    <div class="pairs-container">
      <div
        v-for="pair in filteredPairs"
        :key="pair.flag_id"
        class="pair-card glass-panel"
        :class="{ 'card-resolved': pair.review_status !== 'Open' }"
      >
        <!-- Card Top Bar -->
        <div class="pair-top-bar">
          <div class="pair-status-info">
            <span class="badge" :class="pair.score >= 0.9 ? 'badge-likely' : 'badge-possible'">
              {{ pair.label }}
            </span>
            <span class="score-badge money-val">
              Match Score: {{ (pair.score * 100).toFixed(0) }}%
            </span>
            <span class="badge" :class="getReviewBadgeClass(pair.review_status)">
              Review: {{ pair.review_status }}
            </span>
          </div>

          <div class="pair-actions" v-if="pair.review_status === 'Open'">
            <button class="btn btn-danger btn-sm" @click="handleResolve(pair.flag_id, 'Confirmed duplicate')">
              <HugeiconsIcon :icon="Alert02Icon" :size="14" :stroke-width="1.8" color="#FFFFFF" />
              <span>Confirm Duplicate</span>
            </button>
            <button class="btn btn-secondary btn-sm" @click="handleResolve(pair.flag_id, 'Not a duplicate')">
              <HugeiconsIcon :icon="CheckmarkCircle01Icon" :size="14" :stroke-width="1.8" color="#FFFFFF" />
              <span>Mark as Clean</span>
            </button>
          </div>
          <div v-else class="resolved-note">
            <span>Decision logged: <strong>{{ pair.review_status }}</strong></span>
          </div>
        </div>

        <!-- Side by Side Comparison Grid -->
        <div class="comparison-grid">
          <!-- Suspect Newer Invoice -->
          <div class="invoice-box suspect-box">
            <div class="box-tag suspect-tag">Suspect Invoice (Newer #{{ pair.invoice_id }})</div>
            <div class="box-content">
              <div class="box-row">
                <span class="row-label">Vendor:</span>
                <span class="row-val font-semibold">{{ pair.current_vendor }}</span>
              </div>
              <div class="box-row">
                <span class="row-label">Invoice #:</span>
                <span class="row-val code-tag">{{ pair.current_invoice_no }}</span>
              </div>
              <div class="box-row">
                <span class="row-label">Date:</span>
                <span class="row-val">{{ pair.current_date }}</span>
              </div>
              <div class="box-row">
                <span class="row-label">Total Amount:</span>
                <span class="row-val money-val text-white">
                  {{ pair.current_currency === 'INR' ? '₹' : '£' }}{{ Number(pair.current_total).toLocaleString('en-IN') }}
                </span>
              </div>
              <div class="box-row">
                <span class="row-label">File:</span>
                <span class="row-val text-dim text-xs">{{ pair.current_source }}</span>
              </div>
            </div>
          </div>

          <!-- Score Breakdown Meter in Center -->
          <div class="audit-meter-box">
            <div class="meter-icon">
              <HugeiconsIcon :icon="FileSearchIcon" :size="20" :stroke-width="1.8" color="#FFFFFF" />
            </div>
            <div class="meter-score money-val">{{ (pair.score * 100).toFixed(0) }}%</div>
            <div class="meter-label">RapidFuzz Ratio</div>
            <div class="meter-reasons">
              <div v-for="(reason, idx) in splitReasons(pair.reasons)" :key="idx" class="meter-reason-pill">
                {{ reason }}
              </div>
            </div>
          </div>

          <!-- Original Earlier Invoice -->
          <div class="invoice-box orig-box">
            <div class="box-tag orig-tag">Original Invoice (Earlier #{{ pair.orig_id }})</div>
            <div class="box-content">
              <div class="box-row">
                <span class="row-label">Vendor:</span>
                <span class="row-val font-semibold">{{ pair.orig_vendor }}</span>
              </div>
              <div class="box-row">
                <span class="row-label">Invoice #:</span>
                <span class="row-val code-tag">{{ pair.orig_invoice_no }}</span>
              </div>
              <div class="box-row">
                <span class="row-label">Date:</span>
                <span class="row-val">{{ pair.orig_date }}</span>
              </div>
              <div class="box-row">
                <span class="row-label">Total Amount:</span>
                <span class="row-val money-val text-white">
                  {{ pair.orig_currency === 'INR' ? '₹' : '£' }}{{ Number(pair.orig_total).toLocaleString('en-IN') }}
                </span>
              </div>
              <div class="box-row">
                <span class="row-label">File:</span>
                <span class="row-val text-dim text-xs">{{ pair.orig_source }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="filteredPairs.length === 0" class="empty-flags glass-panel">
        <HugeiconsIcon :icon="ShieldCheckIcon" :size="28" :stroke-width="1.8" color="#FFFFFF" />
        <h3>No duplicate flags match this filter</h3>
        <p class="text-dim">All invoices are clean or no pairs have been flagged.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  Alert02Icon,
  CheckmarkCircle01Icon,
  FileSearchIcon,
  ShieldCheckIcon
} from '@hugeicons/core-free-icons';
import { getDuplicateFlagsWithDetails, updateFlagStatus } from '../services/db.js';

const emit = defineEmits(['updated']);

const activeStatusFilter = ref('Open');
const pairs = ref(getDuplicateFlagsWithDetails());

const filteredPairs = computed(() => {
  if (activeStatusFilter.value === 'All') return pairs.value;
  return pairs.value.filter(p => p.review_status === activeStatusFilter.value);
});

function splitReasons(reasonsStr) {
  if (!reasonsStr) return [];
  return reasonsStr.split(';').map(r => r.trim()).filter(Boolean);
}

function handleResolve(flagId, status) {
  updateFlagStatus(flagId, status);
  pairs.value = getDuplicateFlagsWithDetails();
  emit('updated');
}

function getReviewBadgeClass(status) {
  if (status === 'Open') return 'badge-possible';
  if (status === 'Confirmed duplicate') return 'badge-likely';
  return 'badge-clean';
}
</script>

<style scoped>
.duplicates-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.audit-header {
  padding: 20px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.audit-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #FFFFFF;
}

.audit-desc {
  font-size: 0.82rem;
  color: var(--text-dim);
  max-width: 600px;
  margin-top: 4px;
}

.filter-pills {
  display: flex;
  gap: 8px;
}

.pill-btn {
  padding: 6px 14px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.pill-btn:hover {
  color: #FFFFFF;
  border-color: var(--border-bright);
}

.pill-btn.active {
  background: rgba(14, 165, 233, 0.15);
  border-color: rgba(14, 165, 233, 0.4);
  color: #38BDF8;
}

.pairs-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.pair-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  border-left: 4px solid var(--rose);
}

.pair-card.card-resolved {
  border-left-color: var(--border-subtle);
  opacity: 0.75;
}

.pair-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border-subtle);
}

.pair-status-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.score-badge {
  font-size: 0.82rem;
  font-weight: 700;
  color: #FDA4AF;
}

.pair-actions {
  display: flex;
  gap: 10px;
}

.resolved-note {
  font-size: 0.82rem;
  color: var(--text-dim);
}

.comparison-grid {
  display: grid;
  grid-template-columns: 1fr 220px 1fr;
  gap: 18px;
  align-items: center;
}

.invoice-box {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.box-tag {
  padding: 8px 14px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.suspect-tag {
  background: rgba(244, 63, 94, 0.15);
  color: #FB7185;
  border-bottom: 1px solid rgba(244, 63, 94, 0.25);
}

.orig-tag {
  background: rgba(14, 165, 233, 0.12);
  color: #38BDF8;
  border-bottom: 1px solid rgba(14, 165, 233, 0.25);
}

.box-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.box-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}

.row-label {
  color: var(--text-dim);
  font-size: 0.78rem;
}

.audit-meter-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 16px 10px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-md);
  border: 1px dashed var(--border-subtle);
}

.meter-icon {
  font-size: 1.5rem;
  margin-bottom: 4px;
}

.meter-score {
  font-size: 1.8rem;
  font-weight: 800;
  color: #FB7185;
}

.meter-label {
  font-size: 0.7rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 10px;
}

.meter-reasons {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.meter-reason-pill {
  font-size: 0.72rem;
  background: rgba(244, 63, 94, 0.08);
  border: 1px solid rgba(244, 63, 94, 0.2);
  color: #FDA4AF;
  padding: 4px 8px;
  border-radius: 4px;
}

.empty-flags {
  padding: 60px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.empty-icon {
  font-size: 2.5rem;
}

@media (max-width: 960px) {
  .comparison-grid {
    grid-template-columns: 1fr;
  }
}
</style>
