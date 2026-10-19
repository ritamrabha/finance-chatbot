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

    <!-- Navigation Bar with Hugeicons -->
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
        <span class="error-icon">⚠️</span>
        <div>
          <h3>Database Initialization Error</h3>
          <p>{{ dbState.error }}</p>
        </div>
      </div>

      <div v-else class="tab-content-wrapper">
        <!-- Dashboard Tab -->
        <DashboardView
          v-if="activeTab === 'dashboard'"
          :analytics="analyticsData"
          :recent-invoices="allInvoices.slice(0, 6)"
          @nav="activeTab = $event"
          @ask-query="handleTriggerPrompt"
          @view-invoice="handleViewInvoice"
        />

        <!-- Invoices & Review Tab -->
        <InvoicesView
          v-else-if="activeTab === 'invoices'"
          :all-invoices="allInvoices"
          @ask-query="handleTriggerPrompt"
        />

        <!-- Groq AI Assistant Tab -->
        <ChatbotView
          v-else-if="activeTab === 'chat'"
          :active-model="activeModel"
          :prefilled-query="prefilledPrompt"
          @clear-prefilled="prefilledPrompt = ''"
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

        <!-- Financial KYC & CIBIL Vault Tab -->
        <KycVaultView
          v-else-if="activeTab === 'kyc-vault'"
        />

        <!-- Groq Cloud Studio Tab -->
        <GroqStudioView
          v-else-if="activeTab === 'groq-studio'"
          :active-model="activeModel"
          @update:active-model="activeModel = $event"
        />
      </div>
    </main>

    <!-- Footer -->
    <AppFooter :active-model="activeModel" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import AppHeader from './components/AppHeader.vue';
import AppNavbar from './components/AppNavbar.vue';
import AppFooter from './components/AppFooter.vue';

import DashboardView from './views/DashboardView.vue';
import InvoicesView from './views/InvoicesView.vue';
import ChatbotView from './views/ChatbotView.vue';
import UploadView from './views/UploadView.vue';
import DuplicatesView from './views/DuplicatesView.vue';
import GroqStudioView from './views/GroqStudioView.vue';
import KycVaultView from './views/KycVaultView.vue';

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

function handleViewInvoice(id) {
  activeTab.value = 'invoices';
}
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex: 1;
  max-width: 1440px;
  width: 100%;
  margin: 0 auto;
  padding: 24px;
}

.db-loading-state, .db-error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  margin: 40px auto;
  max-width: 600px;
  text-align: center;
  font-size: 0.95rem;
  color: #38BDF8;
}

.db-error-state {
  color: #FDA4AF;
  border-color: rgba(244, 63, 94, 0.4);
}

.error-icon {
  font-size: 1.8rem;
}

.tab-content-wrapper {
  animation: fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .main-content {
    padding: 16px 12px;
  }
}
</style>
