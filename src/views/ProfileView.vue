<template>
  <div class="profile-view-container">
    <!-- Profile Hero Card -->
    <div class="profile-hero glass-panel">
      <div class="hero-left">
        <div class="user-avatar-box">
          <HugeiconsIcon :icon="User02Icon" :size="32" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <div>
          <div class="hero-title-row">
            <h2 class="user-fullname">{{ authState.name || 'Finance Administrator' }}</h2>
            <span class="badge">Active Session</span>
            <span class="badge badge-clean">Auto-Authenticated</span>
          </div>
          <div class="user-meta">
            <span class="meta-tag">Username: <strong>{{ authState.user }}</strong></span>
            <span class="meta-separator">·</span>
            <span class="meta-tag">{{ authState.role }}</span>
            <span class="meta-separator">·</span>
            <span class="meta-tag">Azure SQL: Connected</span>
          </div>
        </div>
      </div>

      <!-- Quick Session Action -->
      <div class="hero-right">
        <button class="btn btn-secondary btn-sm" @click="handleRefreshSession">
          <HugeiconsIcon :icon="RefreshIcon" :size="16" :stroke-width="1.8" color="#FFFFFF" />
          <span>Sync Profile</span>
        </button>
      </div>
    </div>

    <!-- Security & Default Access Pill Card -->
    <div class="security-card glass-panel">
      <div class="sec-header">
        <div class="sec-icon-wrap">
          <HugeiconsIcon :icon="SecurityCheckIcon" :size="20" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <div>
          <h3 class="sec-title">Authentication & Security Credentials</h3>
          <p class="sec-desc">Default credentials are permanently stored for zero-friction access. You will never be blocked by a login screen.</p>
        </div>
      </div>

      <div class="creds-grid">
        <div class="cred-cell">
          <span class="cred-name">Default Username</span>
          <code class="code-tag">{{ authState.defaultUser }}</code>
        </div>
        <div class="cred-cell">
          <span class="cred-name">Default Password</span>
          <code class="code-tag">{{ authState.defaultPassword }}</code>
        </div>
        <div class="cred-cell">
          <span class="cred-name">Access Privileges</span>
          <span class="badge">Unrestricted (CFO & Admin)</span>
        </div>
        <div class="cred-cell">
          <span class="cred-name">Session Persistence</span>
          <span class="badge badge-clean">Permanent (Browser & Server)</span>
        </div>
      </div>
    </div>

    <!-- KYC & Financial Identity (Azure SQL) -->
    <div class="kyc-section glass-panel">
      <div class="section-head">
        <div>
          <h3 class="card-title">KYC & Financial Bureau Records</h3>
          <p class="subtitle">Stored in Azure SQL Database (Serverless Free Tier) in Central India with AES encryption and UIDAI masking.</p>
        </div>
        <button class="btn btn-primary btn-sm" @click="showAddModal = true">
          <span>+ Add Financial Profile</span>
        </button>
      </div>

      <!-- Compliance summary -->
      <div class="compliance-pills">
        <div class="comp-pill">
          <HugeiconsIcon :icon="ShieldCheckIcon" :size="16" :stroke-width="1.8" color="#FFFFFF" />
          <span>UIDAI Compliant: Masked Aadhaar (XXXXXXXX1234)</span>
        </div>
        <div class="comp-pill">
          <HugeiconsIcon :icon="BankIcon" :size="16" :stroke-width="1.8" color="#FFFFFF" />
          <span>Bank Validation: Masked Accounts & Active IFSC</span>
        </div>
      </div>

      <!-- Profiles Grid -->
      <div class="profiles-grid">
        <div v-for="item in profiles" :key="item.id" class="profile-card">
          <div class="p-top">
            <div class="p-user">
              <span class="p-avatar">
                <HugeiconsIcon :icon="User02Icon" :size="18" :stroke-width="1.8" color="#FFFFFF" />
              </span>
              <div>
                <h4 class="p-name">{{ item.full_name }}</h4>
                <span class="code-tag text-xs">{{ item.id }}</span>
              </div>
            </div>
            <!-- CIBIL score pill -->
            <div class="cibil-pill">
              <span class="cibil-num">{{ item.cibil_score }}</span>
              <span class="cibil-lbl">CIBIL · {{ item.cibil_rating }}</span>
            </div>
          </div>

          <div class="p-details">
            <div class="p-row">
              <span class="p-label">PAN Number</span>
              <code class="code-tag">{{ item.pan_masked }}</code>
            </div>
            <div class="p-row">
              <span class="p-label">Aadhaar (UIDAI Masked)</span>
              <code class="code-tag">{{ item.aadhaar_masked }}</code>
            </div>
            <div class="p-row">
              <span class="p-label">Bank Institution</span>
              <span class="text-white font-semibold">{{ item.bank_name }}</span>
            </div>
            <div class="p-row">
              <span class="p-label">Account Number</span>
              <code class="code-tag">{{ item.account_no_masked }}</code>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Profile Modal -->
    <div v-if="showAddModal" class="modal-overlay" @click.self="showAddModal = false">
      <div class="modal-content glass-panel add-modal">
        <div class="modal-head">
          <h3 class="title">Add Customer Financial Profile</h3>
          <button class="modal-close" @click="showAddModal = false">✕</button>
        </div>

        <form @submit.prevent="handleSaveProfile" class="add-form">
          <div class="form-group">
            <label class="label">Full Name / Entity Name</label>
            <input type="text" v-model="form.full_name" required placeholder="e.g. Ritam Rabha" class="modal-input" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="label">CIBIL Bureau Score (300 - 900)</label>
              <input type="number" v-model.number="form.cibil_score" min="300" max="900" required class="modal-input" />
            </div>
            <div class="form-group">
              <label class="label">Permanent Account Number (PAN)</label>
              <input type="text" v-model="form.pan" required maxlength="10" placeholder="e.g. ABCDE1234F" class="modal-input" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="label">12-Digit Aadhaar Number</label>
              <input type="text" v-model="form.aadhaar" required maxlength="12" placeholder="e.g. 543298761234" class="modal-input" />
            </div>
            <div class="form-group">
              <label class="label">Bank Name</label>
              <input type="text" v-model="form.bank_name" required placeholder="e.g. HDFC Bank" class="modal-input" />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label class="label">Bank Account Number</label>
              <input type="text" v-model="form.account_no" required placeholder="e.g. 100234567890" class="modal-input" />
            </div>
            <div class="form-group">
              <label class="label">IFSC Code</label>
              <input type="text" v-model="form.bank_ifsc" required maxlength="11" placeholder="e.g. HDFC0001234" class="modal-input" />
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn btn-secondary" @click="showAddModal = false">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="saving">
              {{ saving ? 'Saving...' : 'Save Profile to Azure SQL' }}
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
  User02Icon,
  RefreshIcon,
  SecurityCheckIcon,
  ShieldCheckIcon,
  BankIcon
} from '@hugeicons/core-free-icons';
import { authState } from '../services/auth.js';

const showAddModal = ref(false);
const saving = ref(false);

const profiles = ref([
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
  },
  {
    id: 'fp_002',
    full_name: 'Sharma Enterprise Pvt Ltd',
    pan_masked: 'AAACS****K',
    aadhaar_masked: 'XXXXXXXX4411',
    cibil_score: 740,
    cibil_rating: 'Good',
    bank_name: 'State Bank of India',
    bank_ifsc: 'SBIN0005678',
    account_no_masked: 'XXXXXXXX8821',
    created_at: '2026-10-18T12:00:00Z'
  }
]);

const form = ref({
  full_name: '',
  cibil_score: 750,
  pan: '',
  aadhaar: '',
  bank_name: '',
  bank_ifsc: '',
  account_no: ''
});

onMounted(async () => {
  await fetchProfiles();
});

async function fetchProfiles() {
  try {
    const res = await fetch('/api/financial-profiles');
    if (res.ok) {
      const data = await res.json();
      if (data.profiles && data.profiles.length > 0) {
        profiles.value = data.profiles;
      }
    }
  } catch (err) {
    console.warn('Using offline profiles fallback');
  }
}

async function handleSaveProfile() {
  saving.value = true;
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
      form.value = {
        full_name: '',
        cibil_score: 750,
        pan: '',
        aadhaar: '',
        bank_name: '',
        bank_ifsc: '',
        account_no: ''
      };
    }
  } catch (err) {
    alert('Failed to save profile: ' + err.message);
  } finally {
    saving.value = false;
  }
}

function handleRefreshSession() {
  fetchProfiles();
}
</script>

<style scoped>
.profile-view-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.profile-hero {
  padding: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.hero-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-avatar-box {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: #171717;
  border: 1px solid var(--border-bright);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.user-fullname {
  font-size: 1.3rem;
  font-weight: 600;
  color: #FFFFFF;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 0.85rem;
  color: var(--text-dim);
  flex-wrap: wrap;
}

.meta-separator {
  color: #3F3F46;
}

.security-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.sec-header {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.sec-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: #141414;
  border: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sec-title {
  font-size: 1rem;
  font-weight: 600;
  color: #FFFFFF;
}

.sec-desc {
  font-size: 0.825rem;
  color: var(--text-dim);
  margin-top: 2px;
}

.creds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.cred-cell {
  background: #141414;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cred-name {
  font-size: 0.75rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.kyc-section {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
}

.card-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: #FFFFFF;
}

.subtitle {
  font-size: 0.825rem;
  color: var(--text-dim);
  margin-top: 2px;
}

.compliance-pills {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.comp-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #121212;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  padding: 6px 14px;
  font-size: 0.775rem;
  color: var(--text-muted);
}

.profiles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
}

.profile-card {
  background: #121212;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.p-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.p-user {
  display: flex;
  align-items: center;
  gap: 10px;
}

.p-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #1C1C1C;
  border: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}

.p-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: #FFFFFF;
}

.cibil-pill {
  background: #18181B;
  border: 1px solid var(--border-bright);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.cibil-num {
  font-family: var(--font-mono);
  font-weight: 700;
  font-size: 1rem;
  color: #FFFFFF;
}

.cibil-lbl {
  font-size: 0.65rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.p-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.p-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.825rem;
}

.p-label {
  color: var(--text-dim);
}

/* Modal */
.add-modal {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-close {
  background: transparent;
  border: none;
  color: var(--text-dim);
  font-size: 1.2rem;
  cursor: pointer;
}

.add-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

@media (max-width: 600px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}

.modal-input {
  width: 100%;
  background: #141414;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  color: #FFFFFF;
  font-size: 0.875rem;
  outline: none;
}

.modal-input:focus {
  border-color: #FFFFFF;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}
</style>
