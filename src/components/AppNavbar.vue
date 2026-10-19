<template>
  <nav class="app-navbar">
    <div class="nav-container">
      <div class="nav-tabs">
        <button
          v-for="tab in navTabs"
          :key="tab.id"
          class="nav-item"
          :class="{ active: currentTab === tab.id }"
          @click="$emit('select-tab', tab.id)"
        >
          <!-- Hugeicons Icon -->
          <div class="icon-wrapper">
            <HugeiconsIcon
              :icon="tab.icon"
              :size="22"
              :stroke-width="1.75"
              color="currentColor"
            />
          </div>
          <span class="tab-label">{{ tab.name }}</span>

          <!-- Badges -->
          <span v-if="tab.badge" class="nav-badge" :class="tab.badgeClass">
            {{ tab.badge }}
          </span>
          <span v-if="tab.isNew" class="sparkle-dot" title="Powered by Groq">✨</span>
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  DashboardSquare01Icon,
  Invoice01Icon,
  AiChat02Icon,
  AddInvoiceIcon,
  FileSearchIcon,
  CpuIcon,
  BankIcon
} from '@hugeicons/core-free-icons';

const props = defineProps({
  currentTab: {
    type: String,
    default: 'dashboard'
  },
  duplicateCount: {
    type: Number,
    default: 0
  },
  invoicesCount: {
    type: Number,
    default: 0
  }
});

defineEmits(['select-tab']);

const navTabs = computed(() => [
  {
    id: 'dashboard',
    name: 'Dashboard',
    icon: DashboardSquare01Icon
  },
  {
    id: 'invoices',
    name: 'Invoices & Review',
    icon: Invoice01Icon,
    badge: props.invoicesCount ? String(props.invoicesCount) : null,
    badgeClass: 'badge-count'
  },
  {
    id: 'chat',
    name: 'Groq AI Assistant',
    icon: AiChat02Icon,
    isNew: true
  },
  {
    id: 'upload',
    name: 'Upload & Scan',
    icon: AddInvoiceIcon
  },
  {
    id: 'duplicates',
    name: 'Duplicate Auditor',
    icon: FileSearchIcon,
    badge: props.duplicateCount > 0 ? String(props.duplicateCount) : null,
    badgeClass: 'badge-alert'
  },
  {
    id: 'kyc-vault',
    name: 'KYC & CIBIL Vault',
    icon: BankIcon,
    badge: 'Azure SQL',
    badgeClass: 'badge-clean'
  },
  {
    id: 'groq-studio',
    name: 'Groq Cloud Studio',
    icon: CpuIcon
  }
]);
</script>

<style scoped>
.app-navbar {
  background: rgba(11, 17, 32, 0.75);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-subtle);
  padding: 8px 24px;
}

.nav-container {
  max-width: 1440px;
  margin: 0 auto;
  overflow-x: auto;
  scrollbar-width: none;
}
.nav-container::-webkit-scrollbar {
  display: none;
}

.nav-tabs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 18px;
  border-radius: var(--radius-md);
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-muted);
  font-family: var(--font-sans);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  white-space: nowrap;
  position: relative;
}

.nav-item:hover {
  color: #FFFFFF;
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.08);
}

.nav-item.active {
  color: #38BDF8;
  background: rgba(14, 165, 233, 0.12);
  border-color: rgba(14, 165, 233, 0.35);
  box-shadow: 0 2px 14px rgba(14, 165, 233, 0.2);
}

.icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease;
}

.nav-item:hover .icon-wrapper {
  transform: translateY(-1px);
}

.nav-item.active .icon-wrapper {
  color: #38BDF8;
}

.tab-label {
  letter-spacing: -0.01em;
}

.nav-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: var(--radius-full);
}

.badge-count {
  background: rgba(255, 255, 255, 0.08);
  color: #CBD5E1;
}

.badge-alert {
  background: rgba(244, 63, 94, 0.2);
  color: #FDA4AF;
  border: 1px solid rgba(244, 63, 94, 0.4);
}

.sparkle-dot {
  font-size: 0.85rem;
  animation: pulseGlow 2.5s infinite;
}

@media (max-width: 768px) {
  .app-navbar {
    padding: 6px 12px;
  }
  .nav-item {
    padding: 8px 12px;
    font-size: 0.85rem;
  }
}
</style>
