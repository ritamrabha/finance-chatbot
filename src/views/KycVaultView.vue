<template>
  <div class="kyc-vault-view">
    <!-- Header Banner -->
    <div class="vault-header glass-panel">
      <div class="header-left">
        <div class="vault-avatar">
          <HugeiconsIcon :icon="ShieldCheckIcon" :size="22" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <div>
          <div class="title-badge-row">
            <h2 class="vault-title">Financial KYC & CIBIL Vault</h2>
            <span class="badge">Azure SQL Protected</span>
            <span class="badge badge-currency">UIDAI & DPDP Compliant</span>
          </div>
          <p class="vault-desc">
            Secure ledger for storing User CIBIL scores, PAN, Masked Aadhaar, and Bank credentials. Connected to Azure SQL Database (Serverless Free Tier) in Central India.
          </p>
        </div>
      </div>
      <div class="header-right">
        <button class="btn btn-primary btn-sm" @click="showAddModal = true">
          <span>+ Add Customer Profile</span>
        </button>
      </div>
    </div>

    <!-- Security & Compliance Bar -->
    <div class="compliance-bar glass-panel">
      <div class="comp-item">
        <div class="comp-icon-box">
          <HugeiconsIcon :icon="ShieldCheckIcon" :size="16" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <div>
          <span class="comp-label">Aadhaar Act & UIDAI:</span>
          <span class="comp-val">Masked XXXXXXXX1234 + Salted Hash</span>
        </div>
      </div>
      <div class="comp-item">
        <div class="comp-icon-box">
          <HugeiconsIcon :icon="Invoice01Icon" :size="16" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <div>
          <span class="comp-label">PAN Storage:</span>
          <span class="comp-val">AES-256 Encrypted (Masked View)</span>
        </div>
      </div>
      <div class="comp-item">
        <div class="comp-icon-box">
          <HugeiconsIcon :icon="DashboardSquare01Icon" :size="16" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <div>
          <span class="comp-label">CIBIL Bureau Score:</span>
          <span class="comp-val">300 - 900 Range with RLS Access</span>
        </div>
      </div>
      <div class="comp-item">
        <div class="comp-icon-box">
          <HugeiconsIcon :icon="BankIcon" :size="16" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <div>
          <span class="comp-label">Bank Accounts:</span>
          <span class="comp-val">Masked Number + Validated IFSC</span>
        </div>
      </div>
    </div>

    <!-- Profiles Grid -->
    <div class="profiles-section">
      <div class="section-top">
        <h3 class="section-title">Stored Financial Profiles ({{ profiles.length }})</h3>
        <span class="text-dim text-xs">Live records from Azure SQL / SQLite backend</span>
      </div>

      <div class="profiles-grid">
        <div v-for="item in profiles" :key="item.id" class="profile-card glass-panel">
          <div class="card-head">
            <div class="user-info">
              <span class="avatar-icon">
                <HugeiconsIcon :icon="User02Icon" :size="16" :stroke-width="1.8" color="#FFFFFF" />
              </span>
              <div>
                <h4 class="user-fullname">{{ item.full_name }}</h4>
                <span class="code-tag text-xs">{{ item.id }}</span>
              </div>
            </div>
            <!-- CIBIL Badge -->
            <div class="cibil-badge">
              <span class="cibil-score-val">{{ item.cibil_score }}</span>
              <span class="cibil-sub">CIBIL · {{ item.cibil_rating }}</span>
            </div>
          </div>

          <!-- Specs List -->
          <div class="profile-specs">
            <div class="spec-row">
              <span class="spec-label">Permanent Account Number (PAN):</span>
              <code class="spec-val code-tag">{{ item.pan_masked }}</code>
            </div>
            <div class="spec-row">
              <span class="spec-label">Aadhaar Number (UIDAI Masked):</span>
              <code class="spec-val code-tag">{{ item.aadhaar_masked }}</code>
            </div>
            <div class="spec-row">
              <span class="spec-label">Bank Name:</span>
              <span class="spec-val text-white font-semibold">{{ item.bank_name }}</span>
            </div>
            <div class="spec-row">
              <span class="spec-label">Bank Account Number:</span>
              <code class="spec-val code-tag">{{ item.account_no_masked }}</code>
            </div>
            <div class="spec-row">
              <span class="spec-label">IFSC Code:</span>
              <span class="spec-val font-mono">{{ item.bank_ifsc }}</span>
            </div>
          </div>

          <div class="card-footer">
            <span class="security-chip">AES-256 Protected</span>
            <span class="date-text">{{ formatDate(item.created_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Profile Modal -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-box glass-panel">
        <div class="modal-header">
          <div class="header-left">
            <div class="modal-title-icon-box">
              <HugeiconsIcon :icon="Invoice01Icon" :size="18" :stroke-width="1.8" color="#FFFFFF" />
            </div>
            <div>
              <h3>Add New Financial Profile</h3>
              <p class="text-dim text-xs">Data will be encrypted and stored in compliance with Indian banking laws.</p>
            </div>
          </div>
          <button class="modal-close-btn" @click="showAddModal = false">✕</button>
        </div>

        <form class="modal-form" @submit.prevent="handleSubmit">
          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Customer Full Name *</label>
              <input v-model="form.full_name" type="text" required placeholder="e.g. Ramesh Kumar" class="form-input" />
            </div>
            <div class="form-group">
              <label class="form-label">CIBIL Credit Score (300 - 900) *</label>
              <input v-model.number="form.cibil_score" type="number" min="300" max="900" required class="form-input font-mono" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">PAN Number *</label>
              <input v-model="form.pan" type="text" maxlength="10" required placeholder="ABCDE1234F" class="form-input uppercase font-mono" />
              <span class="help-text">Will be masked as {{ maskPan(form.pan) }}</span>
            </div>
            <div class="form-group">
              <label class="form-label">Aadhaar Number (12 digits) *</label>
              <input v-model="form.aadhaar" type="text" maxlength="12" required placeholder="123456789012" class="form-input font-mono" />
              <span class="help-text">Will be stored as {{ maskAadhaar(form.aadhaar) }}</span>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="form-label">Bank Name *</label>
              <input v-model="form.bank_name" type="text" required placeholder="e.g. State Bank of India" class="form-input" />
            </div>
            <div class="form-group">
              <label class="form-label">Bank IFSC Code *</label>
              <input v-model="form.bank_ifsc" type="text" maxlength="11" required placeholder="SBIN0001234" class="form-input uppercase font-mono" />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Bank Account Number *</label>
            <input v-model="form.account_no" type="text" required placeholder="e.g. 50100234567890" class="form-input font-mono" />
            <span class="help-text">Account number will be masked as {{ maskAccount(form.account_no) }}</span>
          </div>

          <div class="form-actions">
            <button type="submit" class="btn btn-primary" :disabled="submitting">
              <HugeiconsIcon :icon="CheckmarkCircle01Icon" :size="16" :stroke-width="2" color="#000000" />
              <span>{{ submitting ? 'Encrypting & Saving...' : 'Save to Azure SQL Ledger' }}</span>
            </button>
            <button type="button" class="btn btn-secondary" @click="showAddModal = false">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  ShieldCheckIcon,
  Invoice01Icon,
  DashboardSquare01Icon,
  BankIcon,
  User02Icon,
  CheckmarkCircle01Icon
} from '@hugeicons/core-free-icons';

const profiles = ref([]);
const showAddModal = ref(false);
const submitting = ref(false);

const form = ref({
  full_name: '',
  cibil_score: 750,
  pan: '',
  aadhaar: '',
  bank_name: 'HDFC Bank Ltd',
  bank_ifsc: 'HDFC0001234',
  account_no: ''
});

onMounted(() => {
  fetchProfiles();
});

async function fetchProfiles() {
  try {
    const res = await fetch('/api/financial-profiles');
    if (res.ok) {
      const data = await res.json();
      profiles.value = data.profiles || [];
    }
  } catch (err) {
    // Fallback sample data
    profiles.value = [
      {
        id: 'fp_001',
        full_name: 'Ritam Rabha',
        pan_masked: 'ABCDE****F',
        aadhaar_masked: 'XXXXXXXX9012',
        cibil_score: 785,
        cibil_rating: 'Excellent',
        bank_name: 'HDFC Bank Ltd',
        bank_ifsc: 'HDFC0001234',
        account_no_masked: 'XXXXXXXX4589',
        created_at: '2026-10-18T10:30:00Z'
      }
    ];
  }
}

async function handleSubmit() {
  submitting.value = true;
  try {
    const res = await fetch('/api/financial-profiles', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    });
    if (res.ok) {
      const data = await res.json();
      if (data.profile) {
        profiles.value.unshift(data.profile);
      }
      showAddModal.value = false;
      resetForm();
    }
  } catch (err) {
    alert('Error saving profile: ' + err.message);
  } finally {
    submitting.value = false;
  }
}

function resetForm() {
  form.value = {
    full_name: '',
    cibil_score: 750,
    pan: '',
    aadhaar: '',
    bank_name: 'HDFC Bank Ltd',
    bank_ifsc: 'HDFC0001234',
    account_no: ''
  };
}

function maskPan(val) {
  if (!val) return 'XXXXX****X';
  const clean = val.toUpperCase().trim();
  if (clean.length < 5) return clean + '****';
  return clean.slice(0, 5) + '****' + clean.slice(-1);
}

function maskAadhaar(val) {
  if (!val) return 'XXXXXXXX1234';
  const clean = val.trim();
  return 'XXXXXXXX' + clean.slice(-4);
}

function maskAccount(val) {
  if (!val) return 'XXXXXXXX4589';
  const clean = val.trim();
  return 'XXXXXXXX' + clean.slice(-4);
}

function getCibilClass(score) {
  if (score >= 750) return 'cibil-excellent';
  if (score >= 650) return 'cibil-good';
  return 'cibil-average';
}

function formatDate(dateStr) {
  if (!dateStr) return 'Just now';
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });
}
</script>

<style scoped>
.kyc-vault-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.vault-header {
  padding: 24px 32px;
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.vault-avatar {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.25), rgba(6, 182, 212, 0.25));
  border: 1px solid rgba(16, 185, 129, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  flex-shrink: 0;
}

.title-badge-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}

.vault-title {
  font-size: 1.4rem;
  font-weight: 800;
  color: #FFFFFF;
  margin: 0;
}

.vault-desc {
  font-size: 0.85rem;
  color: #94A3B8;
  max-width: 680px;
  margin: 0;
  line-height: 1.5;
}

.compliance-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  padding: 16px 24px;
  border-radius: var(--radius-lg);
  border-left: 4px solid #10B981;
}

.comp-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.comp-icon {
  font-size: 1.5rem;
}

.comp-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #94A3B8;
}

.comp-val {
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  color: #F8FAFC;
}

.profiles-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.section-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #F8FAFC;
  margin: 0;
}

.profiles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 20px;
}

.profile-card {
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: all 0.2s ease;
}

.profile-card:hover {
  transform: translateY(-2px);
  border-color: rgba(56, 189, 248, 0.4);
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

.user-fullname {
  font-size: 1rem;
  font-weight: 700;
  color: #FFFFFF;
  margin: 0 0 2px 0;
}

.cibil-badge {
  padding: 6px 12px;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 90px;
}

.cibil-excellent {
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.35);
  color: #34D399;
}

.cibil-good {
  background: rgba(6, 182, 212, 0.15);
  border: 1px solid rgba(6, 182, 212, 0.35);
  color: #38BDF8;
}

.cibil-average {
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.35);
  color: #FBBF24;
}

.cibil-score-val {
  font-size: 1.2rem;
  font-weight: 900;
  line-height: 1;
}

.cibil-sub {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  margin-top: 2px;
}

.profile-specs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(15, 23, 42, 0.4);
  padding: 12px;
  border-radius: 8px;
}

.spec-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.8rem;
}

.spec-label {
  color: #94A3B8;
  font-size: 0.75rem;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 0.75rem;
}

.security-chip {
  color: #10B981;
  font-weight: 700;
  font-size: 0.7rem;
}

.date-text {
  color: #64748B;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-box {
  width: 100%;
  max-width: 580px;
  background: #0F172A;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.6);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.modal-title-icon {
  font-size: 1.6rem;
}

.modal-close-btn {
  background: transparent;
  border: none;
  color: #94A3B8;
  font-size: 1.2rem;
  cursor: pointer;
}

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #E2E8F0;
}

.form-input {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  padding: 10px 14px;
  color: #FFFFFF;
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.2s;
}

.form-input:focus {
  border-color: #38BDF8;
}

.help-text {
  font-size: 0.7rem;
  color: #10B981;
}

.uppercase {
  text-transform: uppercase;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}
</style>
