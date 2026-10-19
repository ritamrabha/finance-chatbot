<template>
  <nav class="app-navbar" aria-label="Main Navigation">
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
              :size="19"
              :stroke-width="1.8"
              color="currentColor"
            />
          </div>
          <span class="tab-label">{{ tab.name }}</span>

          <!-- Badges -->
          <span v-if="tab.badge" class="nav-badge" :class="tab.badgeClass">
            {{ tab.badge }}
          </span>
        </button>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  Home01Icon,
  Calculator01Icon,
  AiChat02Icon,
  Invoice01Icon,
  AddInvoiceIcon,
  FileSearchIcon,
  User02Icon,
  CpuIcon
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
    name: 'Home',
    icon: Home01Icon
  },
  {
    id: 'calculator',
    name: 'Loan Calculator',
    icon: Calculator01Icon
  },
  {
    id: 'chat',
    name: 'AI Chat Assistant',
    icon: AiChat02Icon
  },
  {
    id: 'invoices',
    name: 'Invoices',
    icon: Invoice01Icon,
    badge: props.invoicesCount ? String(props.invoicesCount) : null,
    badgeClass: 'badge-count'
  },
  {
    id: 'upload',
    name: 'Upload & Scan',
    icon: AddInvoiceIcon
  },
  {
    id: 'duplicates',
    name: 'Duplicates',
    icon: FileSearchIcon,
    badge: props.duplicateCount > 0 ? String(props.duplicateCount) : null,
    badgeClass: 'badge-alert'
  },
  {
    id: 'profile',
    name: 'Profile & Vault',
    icon: User02Icon
  },
  {
    id: 'groq-studio',
    name: 'Groq Studio',
    icon: CpuIcon
  }
]);
</script>

<style scoped>
.app-navbar {
  background: #0A0A0A;
  border-bottom: 1px solid var(--border-subtle);
  padding: 6px 24px;
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
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-dim);
  font-family: var(--font-sans);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.nav-item:hover {
  color: #FFFFFF;
  background: #141414;
}

.nav-item.active {
  color: #FFFFFF;
  background: #1C1C1C;
  border-color: rgba(255, 255, 255, 0.18);
  font-weight: 600;
}

.icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.tab-label {
  letter-spacing: -0.01em;
}

.nav-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: var(--radius-full);
}

.badge-count {
  background: #1A1A1A;
  color: #A1A1AA;
  border: 1px solid var(--border-subtle);
}

.badge-alert {
  background: #1F1F1F;
  color: #FFFFFF;
  border: 1px solid rgba(255, 255, 255, 0.25);
}

@media (max-width: 768px) {
  /* On mobile screens, main top navbar is hidden or condensed because the floating dock is used */
  .app-navbar {
    display: none;
  }
}
</style>
