<template>
  <header class="app-header">
    <div class="header-container">
      <!-- Brand & Title -->
      <div class="brand-group">
        <div class="brand-logo">
          <span class="logo-icon">🧾</span>
          <div class="logo-glow"></div>
        </div>
        <div class="brand-text">
          <div class="title-row">
            <h1 class="brand-title">FinSight <span class="gradient-text">AI</span></h1>
            <span class="brand-badge">Enterprise Edition</span>
          </div>
          <p class="brand-subtitle">Invoice Intelligence & Duplicate Auditor · Powered by Groq Cloud</p>
        </div>
      </div>

      <!-- Center / Model Selector -->
      <div class="model-selector-pill">
        <div class="model-label">
          <span class="pulse-dot"></span>
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
        <div class="status-chip" title="SQLite in-memory WebAssembly">
          <span class="chip-dot"></span>
          <span class="chip-text">{{ invoicesCount }} Invoices</span>
        </div>

        <!-- Duplicate Alert Chip if any -->
        <div v-if="duplicateCount > 0" class="duplicate-alert-chip" @click="$emit('nav', 'duplicates')">
          <span class="alert-icon">⚠️</span>
          <span>{{ duplicateCount }} Duplicates</span>
        </div>

        <!-- User Profile Chip with Default Auth Indicator -->
        <button class="user-profile-chip" @click="showUserModal = true" title="Authentication & Default Password Settings">
          <span class="user-avatar-sm">👤</span>
          <div class="user-chip-text">
            <span class="user-name">{{ authState.user }}</span>
            <span class="user-badge-role">CFO</span>
          </div>
          <span class="auth-lock-dot" title="Auto-authenticated with default password">✓</span>
        </button>

        <!-- Reset Button -->
        <button class="btn btn-secondary btn-sm" @click="$emit('reset-demo')" title="Reset database to the 37 original sample invoices">
          <span>🔄 Reset Demo</span>
        </button>
      </div>
    </div>

    <!-- User Auth & Default Password Modal -->
    <div v-if="showUserModal" class="modal-overlay" @click.self="showUserModal = false">
      <div class="auth-modal glass-panel">
        <div class="modal-header">
          <div class="header-left">
            <span class="auth-icon">🔐</span>
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
              <span class="badge badge-clean">Full Access (CFO)</span>
            </div>
          </div>

          <div class="auth-actions">
            <button class="btn btn-primary w-full" @click="handleAutoLogin">
              ✓ Log in as Default Admin (Instant)
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue';
import { authState, loginWithDefault } from '../services/auth.js';

const showUserModal = ref(false);

function handleAutoLogin() {
  loginWithDefault();
  showUserModal.value = false;
}

const props = defineProps({
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
  background: rgba(8, 12, 21, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-subtle);
  padding: 14px 24px;
}

.header-container {
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.brand-group {
  display: flex;
  align-items: center;
  gap: 14px;
}

.brand-logo {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.2), rgba(20, 184, 166, 0.2));
  border: 1px solid rgba(14, 165, 233, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon {
  font-size: 1.5rem;
  z-index: 2;
}

.logo-glow {
  position: absolute;
  inset: 0;
  border-radius: 12px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.4) 0%, transparent 70%);
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.brand-title {
  font-size: 1.35rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #FFFFFF;
}

.gradient-text {
  background: linear-gradient(135deg, #38BDF8 0%, #10B981 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.brand-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.brand-subtitle {
  font-size: 0.8rem;
  color: var(--text-dim);
  font-weight: 500;
}

.model-selector-pill {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid var(--border-bright);
  padding: 6px 14px;
  border-radius: var(--radius-full);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.25);
}

.model-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.groq-tag {
  font-size: 0.75rem;
  font-weight: 700;
  color: #F97316;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.model-select {
  background: transparent;
  border: none;
  color: #F8FAFC;
  font-family: var(--font-sans);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  outline: none;
}

.model-select option {
  background: #0F172A;
  color: #FFFFFF;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-chip {
  display: flex;
  align-items: center;
  gap: 7px;
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.25);
  padding: 5px 12px;
  border-radius: var(--radius-full);
  font-size: 0.8rem;
  font-weight: 600;
  color: #34D399;
}

.chip-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10B981;
}

.duplicate-alert-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(244, 63, 94, 0.12);
  border: 1px solid rgba(244, 63, 94, 0.35);
  padding: 5px 12px;
  border-radius: var(--radius-full);
  font-size: 0.8rem;
  font-weight: 600;
  color: #FB7185;
  cursor: pointer;
  transition: all 0.2s ease;
}

.duplicate-alert-chip:hover {
  background: rgba(244, 63, 94, 0.22);
  transform: translateY(-1px);
}

.btn-sm {
  padding: 6px 14px;
  font-size: 0.8rem;
}

.user-profile-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(30, 41, 59, 0.7);
  border: 1px solid rgba(56, 189, 248, 0.3);
  padding: 4px 12px;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-profile-chip:hover {
  background: rgba(56, 189, 248, 0.15);
  border-color: rgba(56, 189, 248, 0.6);
  transform: translateY(-1px);
}

.user-avatar-sm {
  font-size: 1rem;
}

.user-chip-text {
  display: flex;
  align-items: center;
  gap: 6px;
}

.user-name {
  font-size: 0.8rem;
  font-weight: 700;
  color: #F8FAFC;
}

.user-badge-role {
  background: rgba(56, 189, 248, 0.2);
  color: #38BDF8;
  font-size: 0.65rem;
  font-weight: 800;
  padding: 1px 6px;
  border-radius: 4px;
}

.auth-lock-dot {
  color: #10B981;
  font-weight: 800;
  font-size: 0.75rem;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.auth-modal {
  width: 100%;
  max-width: 480px;
  background: #0F172A;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.auth-icon {
  font-size: 1.8rem;
}

.modal-header h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #FFFFFF;
  margin: 0;
}

.modal-close-btn {
  background: transparent;
  border: none;
  color: #94A3B8;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px;
}

.modal-close-btn:hover {
  color: #FFFFFF;
}

.auth-status-card {
  background: rgba(16, 185, 129, 0.08);
  border: 1px solid rgba(16, 185, 129, 0.25);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 16px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.status-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 8px #10B981;
}

.status-title {
  font-size: 0.9rem;
  color: #F8FAFC;
}

.status-desc {
  font-size: 0.8rem;
  color: #94A3B8;
  margin: 0;
  line-height: 1.4;
}

.creds-box {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cred-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.85rem;
}

.cred-label {
  color: #94A3B8;
  font-weight: 500;
}

.auth-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

@media (max-width: 900px) {
  .brand-subtitle {
    display: none;
  }
  .model-selector-pill {
    order: 3;
    width: 100%;
    justify-content: center;
  }
}
</style>
