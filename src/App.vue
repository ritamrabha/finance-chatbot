<template>
  <div class="app-shell">
    <!-- Header -->
    <AppHeader
      :active-model="activeModel"
      :models="models"
      :invoices-count="dbState.invoicesCount"
      :duplicate-count="dbState.duplicateFlagsCount"
      @update:active-model="activeModel = $event"
      @reset-demo="handleResetDemo"
      @nav="activeTab = $event"
    />

    <!-- Navigation Bar for Desktop with Hugeicons -->
    <AppNavbar
      :current-tab="activeTab"
      :invoices-count="dbState.invoicesCount"
      :duplicate-count="dbState.duplicateFlagsCount"
      @select-tab="activeTab = $event"
    />

    <!-- Main Content Area -->
    <main class="main-content">
      <div v-if="dbState.loading" class="db-loading-state glass-panel">
        <span class="pulse-dot"></span>
        <span>Initializing in-browser SQLite WebAssembly ledger & Groq AI engine...</span>
      </div>

      <div v-else-if="dbState.error" class="db-error-state glass-panel">
        <HugeiconsIcon :icon="Alert02Icon" :size="24" :stroke-width="1.8" color="#FFFFFF" />
        <div>
          <h3>Database Initialization Error</h3>
          <p>{{ dbState.error }}</p>
        </div>
      </div>

      <div v-else class="tab-content-wrapper">
        <!-- Home / Dashboard Tab -->
        <DashboardView
          v-if="activeTab === 'dashboard'"
          :analytics="analyticsData"
          :recent-invoices="allInvoices.slice(0, 6)"
          @nav="activeTab = $event"
          @ask-query="handleTriggerPrompt"
          @view-invoice="handleViewInvoice"
        />

        <!-- Loan Calculator Tab (Requested by User) -->
        <LoanCalculatorView
          v-else-if="activeTab === 'calculator'"
          @ask-query="handleTriggerPrompt"
        />

        <!-- Groq AI Assistant Tab -->
        <ChatbotView
          v-else-if="activeTab === 'chat'"
          :active-model="activeModel"
          :prefilled-query="prefilledPrompt"
          @clear-prefilled="prefilledPrompt = ''"
        />

        <!-- Profile & KYC Vault Tab (Requested by User) -->
        <ProfileView
          v-else-if="activeTab === 'profile' || activeTab === 'kyc-vault'"
        />

        <!-- Invoices & Review Tab -->
        <InvoicesView
          v-else-if="activeTab === 'invoices'"
          :all-invoices="allInvoices"
          @ask-query="handleTriggerPrompt"
        />

        <!-- Upload & Scan Tab -->
        <UploadView
          v-else-if="activeTab === 'upload'"
          :all-invoices="allInvoices"
          @invoice-added="refreshData"
          @nav="activeTab = $event"
        />

        <!-- Duplicate Auditor Tab -->
        <DuplicatesView
          v-else-if="activeTab === 'duplicates'"
          @updated="refreshData"
        />

        <!-- Groq Cloud Studio Tab -->
        <GroqStudioView
          v-else-if="activeTab === 'groq-studio'"
          :active-model="activeModel"
          @update:active-model="activeModel = $event"
        />
      </div>
    </main>

    <!-- Floating Mobile Bottom Navigation Dock (Matching user reference screenshot) -->
    <MobileDock
      :current-tab="activeTab"
      @select-tab="activeTab = $event"
    />

    <!-- Footer -->
    <AppFooter :active-model="activeModel" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import { Alert02Icon } from '@hugeicons/core-free-icons';

import AppHeader from './components/AppHeader.vue';
import AppNavbar from './components/AppNavbar.vue';
import AppFooter from './components/AppFooter.vue';
import MobileDock from './components/MobileDock.vue';

import DashboardView from './views/DashboardView.vue';
import LoanCalculatorView from './views/LoanCalculatorView.vue';
import InvoicesView from './views/InvoicesView.vue';
import ChatbotView from './views/ChatbotView.vue';
import UploadView from './views/UploadView.vue';
import DuplicatesView from './views/DuplicatesView.vue';
import GroqStudioView from './views/GroqStudioView.vue';
import ProfileView from './views/ProfileView.vue';

import { initDatabase, dbState, getInvoices, getAnalytics, resetToSampleData } from './services/db.js';
import { GROQ_MODELS } from './services/groq.js';

const activeTab = ref('dashboard');
const activeModel = ref('openai/gpt-oss-120b');
const models = ref(GROQ_MODELS);
const prefilledPrompt = ref('');

const allInvoices = ref([]);
const analyticsData = ref(null);

onMounted(async () => {
  try {
    await initDatabase();
    refreshData();
  } catch (err) {
    console.error('Initialization error:', err);
  }
});

function refreshData() {
  allInvoices.value = getInvoices();
  analyticsData.value = getAnalytics();
}

function handleResetDemo() {
  if (confirm('Reset database to the 37 original sample invoices? Any newly uploaded invoices will be cleared.')) {
    resetToSampleData();
    refreshData();
    alert('Database successfully reset to original demo state!');
  }
}

function handleTriggerPrompt(promptText) {
  prefilledPrompt.value = promptText;
  activeTab.value = 'chat';
}

function handleViewInvoice() {
  activeTab.value = 'invoices';
}
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  position: relative;
}

.main-content {
  flex: 1;
  max-width: 1440px;
  width: 100%;
  margin: 0 auto;
  padding: 24px;
  padding-bottom: 96px; /* Allow clearance for floating mobile dock */
}

.db-loading-state, .db-error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 36px;
  margin: 40px auto;
  max-width: 560px;
  text-align: center;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.db-error-state {
  color: #FFFFFF;
  border-color: rgba(255, 255, 255, 0.2);
}

.tab-content-wrapper {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .main-content {
    padding: 16px 12px 108px 12px;
  }
}
</style>
