<template>
  <header class="app-header">
    <div class="header-container">
      <!-- Brand & Title -->
      <div class="brand-group" @click="$emit('nav', 'dashboard')">
        <div class="brand-logo">
          <HugeiconsIcon :icon="Invoice01Icon" :size="20" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <div class="brand-text">
          <div class="title-row">
            <h1 class="brand-title">FinSight AI</h1>
            <span class="brand-badge">Enterprise</span>
          </div>
          <p class="brand-subtitle">Invoice Intelligence & Financial Suite · Groq Cloud</p>
        </div>
      </div>

      <!-- Center / Model Selector -->
      <div class="model-selector-pill">
        <div class="model-label">
          <HugeiconsIcon :icon="CpuIcon" :size="15" :stroke-width="1.8" color="#FFFFFF" />
          <span class="groq-tag">Groq AI</span>
        </div>
        <select
          :value="activeModel"
          @change="$emit('update:activeModel', $event.target.value)"
          class="model-select"
        >
          <option v-for="model in models" :key="model.id" :value="model.id">
            {{ model.name }} ({{ model.speed }})
          </option>
        </select>
      </div>

      <!-- Right Header Actions -->
      <div class="header-actions">
        <!-- DB Status -->
        <div class="status-chip" title="SQLite WebAssembly Active">
          <span class="chip-dot"></span>
          <span class="chip-text">{{ invoicesCount }} Invoices</span>
        </div>

        <!-- Duplicate Alert Chip if any -->
        <div v-if="duplicateCount > 0" class="duplicate-alert-chip" @click="$emit('nav', 'duplicates')">
          <HugeiconsIcon :icon="Alert02Icon" :size="14" :stroke-width="1.8" color="#FFFFFF" />
          <span>{{ duplicateCount }} Duplicates</span>
        </div>

        <!-- User Profile Chip with Default Auth Indicator -->
        <button class="user-profile-chip" @click="showUserModal = true" title="Authentication & Default Password Settings">
          <HugeiconsIcon :icon="User02Icon" :size="16" :stroke-width="1.8" color="#FFFFFF" />
          <div class="user-chip-text">
            <span class="user-name">{{ authState.user }}</span>
            <span class="user-badge-role">CFO</span>
          </div>
          <HugeiconsIcon :icon="CheckmarkCircle01Icon" :size="13" :stroke-width="2.2" color="#FFFFFF" />
        </button>

        <!-- Reset Button -->
        <button class="btn btn-secondary btn-sm" @click="$emit('reset-demo')" title="Reset database to demo data">
          <HugeiconsIcon :icon="RefreshIcon" :size="14" :stroke-width="1.8" color="#FFFFFF" />
          <span class="reset-text">Reset</span>
        </button>
      </div>
    </div>

    <!-- User Auth & Default Password Modal -->
    <div v-if="showUserModal" class="modal-overlay" @click.self="showUserModal = false">
      <div class="auth-modal glass-panel">
        <div class="modal-header">
          <div class="header-left">
            <div class="modal-icon-wrap">
              <HugeiconsIcon :icon="SecurityCheckIcon" :size="20" :stroke-width="1.8" color="#FFFFFF" />
            </div>
            <div>
              <h3>Authentication & Access Control</h3>
              <p class="text-dim text-xs">Default credentials are permanently configured for zero-friction access.</p>
            </div>
          </div>
          <button class="modal-close-btn" @click="showUserModal = false">✕</button>
        </div>

        <div class="modal-body">
          <div class="auth-status-card">
            <div class="status-indicator">
              <span class="status-pulse"></span>
              <span class="status-title">Active Session: <strong>{{ authState.user }}</strong></span>
            </div>
            <p class="status-desc">
              Password authentication is set to <strong>automatic</strong> using the default secret. You will never need to enter your password manually.
            </p>
          </div>

          <div class="creds-box">
            <div class="cred-row">
              <span class="cred-label">Default Username:</span>
              <code class="code-tag">{{ authState.defaultUser }}</code>
            </div>
            <div class="cred-row">
              <span class="cred-label">Default Password:</span>
              <code class="code-tag">{{ authState.defaultPassword }}</code>
            </div>
            <div class="cred-row">
              <span class="cred-label">Role & Privileges:</span>
              <span class="badge">Full Access (CFO)</span>
            </div>
          </div>

          <div class="auth-actions">
            <button class="btn btn-primary w-full" @click="handleAutoLogin">
              <HugeiconsIcon :icon="CheckmarkCircle01Icon" :size="16" :stroke-width="2" color="#000000" />
              <span>Log in as Default Admin (Instant)</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  Invoice01Icon,
  User02Icon,
  Alert02Icon,
  RefreshIcon,
  SecurityCheckIcon,
  CheckmarkCircle01Icon,
  CpuIcon
} from '@hugeicons/core-free-icons';
import { authState, loginWithDefault } from '../services/auth.js';

const showUserModal = ref(false);

function handleAutoLogin() {
  loginWithDefault();
  showUserModal.value = false;
}

defineProps({
  activeModel: {
    type: String,
    default: 'openai/gpt-oss-120b'
  },
  models: {
    type: Array,
    default: () => []
  },
  invoicesCount: {
    type: Number,
    default: 0
  },
  duplicateCount: {
    type: Number,
    default: 0
  }
});

defineEmits(['update:activeModel', 'reset-demo', 'nav']);
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #000000;
  border-bottom: 1px solid var(--border-subtle);
  padding: 12px 24px;
}

.header-container {
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.brand-group {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.brand-logo {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: #141414;
  border: 1px solid var(--border-bright);
  display: flex;
  align-items: center;
  justify-content: center;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.brand-title {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #FFFFFF;
}

.brand-badge {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  background: #171717;
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.brand-subtitle {
  font-size: 0.75rem;
  color: var(--text-dim);
}

.model-selector-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #0F0F0F;
  border: 1px solid var(--border-subtle);
  padding: 5px 12px;
  border-radius: var(--radius-full);
}

.model-label {
  display: flex;
  align-items: center;
  gap: 5px;
}

.groq-tag {
  font-size: 0.75rem;
  font-weight: 600;
  color: #FFFFFF;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.model-select {
  background: transparent;
  border: none;
  color: #E4E4E7;
  font-family: var(--font-sans);
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  outline: none;
}

.model-select option {
  background: #000000;
  color: #FFFFFF;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #121212;
  border: 1px solid var(--border-subtle);
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-muted);
}

.chip-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #FFFFFF;
}

.duplicate-alert-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #18181B;
  border: 1px solid var(--border-bright);
  padding: 4px 10px;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
  color: #FFFFFF;
  cursor: pointer;
}

.user-profile-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #141414;
  border: 1px solid var(--border-subtle);
  padding: 4px 10px;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.15s ease;
}

.user-profile-chip:hover {
  background: #1F1F1F;
  border-color: var(--border-bright);
}

.user-chip-text {
  display: flex;
  align-items: center;
  gap: 5px;
}

.user-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: #FFFFFF;
}

.user-badge-role {
  background: #27272A;
  color: #E4E4E7;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
}

/* Modal */
.auth-modal {
  max-width: 500px;
  width: 100%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.modal-header .header-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.modal-icon-wrap {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-sm);
  background: #171717;
  border: 1px solid var(--border-bright);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close-btn {
  background: transparent;
  border: none;
  color: var(--text-dim);
  font-size: 1.1rem;
  cursor: pointer;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.auth-status-card {
  background: #141414;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
}

.status-pulse {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #FFFFFF;
}

.status-desc {
  font-size: 0.8rem;
  color: var(--text-dim);
  line-height: 1.4;
}

.creds-box {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #0F0F0F;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 14px;
}

.cred-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.825rem;
}

.cred-label {
  color: var(--text-dim);
}

@media (max-width: 768px) {
  .app-header {
    padding: 8px 14px;
  }
  .brand-subtitle,
  .model-selector-pill,
  .status-chip,
  .reset-text,
  .duplicate-alert-chip,
  .user-profile-chip {
    display: none;
  }
}
</style>
