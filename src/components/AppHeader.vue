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

        <!-- Reset Button -->
        <button class="btn btn-secondary btn-sm" @click="$emit('reset-demo')" title="Reset database to the 37 original sample invoices">
          <span>🔄 Reset Demo</span>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue';

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
