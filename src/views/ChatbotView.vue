<template>
  <div class="mobile-chat-app">
    <!-- Mobile Chat Header Bar (WhatsApp / Telegram style) -->
    <div class="chat-app-header glass-panel">
      <div class="header-profile">
        <div class="avatar-circle">
          <HugeiconsIcon :icon="AiChat02Icon" :size="18" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <div class="profile-info">
          <div class="profile-name-row">
            <h2 class="profile-name">FinSight Loan AI</h2>
            <span class="model-pill">{{ activeModelObj?.name || 'Groq 120B' }}</span>
          </div>
          <div class="status-indicator-row">
            <span class="online-dot"></span>
            <span class="status-text">Online · Instant Pre-Approved Loan Check</span>
          </div>
        </div>
      </div>

      <div class="header-actions">
        <button class="btn btn-secondary btn-icon-only" @click="clearHistory" title="Clear Chat">
          <HugeiconsIcon :icon="RefreshIcon" :size="15" :stroke-width="1.8" color="#FFFFFF" />
        </button>
      </div>
    </div>

    <!-- Active Step Pill Banner (Only shown during active sequential steps) -->
    <div v-if="loanSession.active" class="loan-stepper-strip">
      <div class="stepper-text">
        <span class="stepper-badge">Step {{ loanSession.step }} of 3</span>
        <span>{{ currentStepInstruction }}</span>
      </div>
      <button class="btn-cancel-step" @click="cancelLoanFlow">Cancel</button>
    </div>

    <!-- Messages Container -->
    <div ref="chatContainer" class="messages-container">
      <!-- Welcome Screen if no messages -->
      <div v-if="messages.length === 0" class="chat-welcome">
        <div class="welcome-avatar">
          <HugeiconsIcon :icon="CreditCardValidationIcon" :size="32" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <h3 class="welcome-title">Instant Loan Pre-Approval</h3>
        <p class="welcome-desc">
          Provide your name, PAN number, and date of birth to instantly discover your eligible loan limit.
        </p>
      </div>

      <!-- Messages Loop -->
      <div v-for="(msg, idx) in messages" :key="idx" class="message-wrapper" :class="`msg-${msg.role}`">
        <!-- User Bubble -->
        <div v-if="msg.role === 'user'" class="user-bubble">
          <div class="bubble-body">{{ cleanNoHash(msg.text) }}</div>
          <div class="bubble-time">{{ msg.time }}</div>
        </div>

        <!-- Assistant Bubble -->
        <div v-else class="assistant-bubble">
          <div class="bubble-sender-tag">FinSight AI</div>
          <div class="bubble-body" v-html="cleanNoHash(msg.text)"></div>

          <!-- Pre-Approved Loan Amount Card (Clean Mock Data) -->
          <div v-if="msg.loanReport" class="loan-amount-card">
            <div class="loan-card-top">
              <div class="loan-card-badge">
                <HugeiconsIcon :icon="ShieldCheckIcon" :size="15" :stroke-width="1.8" color="#000000" />
                <span>PRE-APPROVED CREDIT OFFER</span>
              </div>
              <span class="loan-approved-date">{{ msg.loanReport.approvedAt }}</span>
            </div>

            <div class="loan-amount-hero">
              <span class="amount-label">Eligible Loan Amount</span>
              <div class="amount-number">{{ msg.loanReport.loanAmountFormatted }}</div>
              <span class="amount-sub">Instant disbursement · Zero collateral required</span>
            </div>

            <div class="loan-meta-grid">
              <div class="meta-item">
                <span class="m-lbl">Borrower</span>
                <span class="m-val">{{ msg.loanReport.fullName }}</span>
              </div>
              <div class="meta-item">
                <span class="m-lbl">PAN Number</span>
                <span class="m-val font-mono">{{ msg.loanReport.panMasked }}</span>
              </div>
              <div class="meta-item">
                <span class="m-lbl">Date of Birth</span>
                <span class="m-val">{{ msg.loanReport.dob }}</span>
              </div>
              <div class="meta-item">
                <span class="m-lbl">CIBIL Score</span>
                <span class="m-val highlight">{{ msg.loanReport.cibilScore }} ({{ msg.loanReport.cibilRating }})</span>
              </div>
              <div class="meta-item">
                <span class="m-lbl">Interest Rate</span>
                <span class="m-val">{{ msg.loanReport.interestRate }}</span>
              </div>
              <div class="meta-item">
                <span class="m-lbl">Est. Monthly EMI</span>
                <span class="m-val font-mono">{{ msg.loanReport.monthlyEmi }}</span>
              </div>
            </div>

            <div class="loan-card-actions">
              <button class="btn btn-primary btn-sm w-full" @click="handleOpenCalculator(msg.loanReport)">
                <HugeiconsIcon :icon="Calculator01Icon" :size="14" :stroke-width="1.8" color="#000000" />
                <span>Calculate EMI in Loan Calculator</span>
              </button>
              <button class="btn btn-secondary btn-sm w-full" @click="startLoanFlow">
                <HugeiconsIcon :icon="RefreshIcon" :size="14" :stroke-width="1.8" color="#FFFFFF" />
                <span>Check Another PAN</span>
              </button>
            </div>
          </div>

          <div class="bubble-time ai-time">{{ msg.time }}</div>
        </div>
      </div>

      <!-- Thinking Indicator -->
      <div v-if="isLoading" class="assistant-bubble loading-bubble">
        <div class="loading-row">
          <span class="pulse-dot"></span>
          <span>Checking pre-approved limit...</span>
        </div>
      </div>
    </div>

    <!-- Quick Action Chips (Mobile Horizontal Scrollable) -->
    <div class="quick-chips-row">
      <button class="quick-chip highlight-chip" @click="startLoanFlow">
        ⚡ Check Loan Amount
      </button>
      <button class="quick-chip" @click="fillDemoData">
        📋 Ritam Rabha · ABCDE1234F · 15/08/1995
      </button>
      <button class="quick-chip" @click="sendSuggested('How much loan can I get with my CIBIL score?')">
        💳 What loan amount can I get?
      </button>
    </div>

    <!-- Mobile Input Bar -->
    <div class="chat-input-bar">
      <form class="mobile-input-form" @submit.prevent="handleSubmit">
        <input
          v-model="inputQuery"
          type="text"
          :placeholder="currentPlaceholder"
          class="mobile-chat-input"
          :disabled="isLoading"
          autocomplete="off"
        />
        <button
          type="submit"
          class="mobile-send-btn"
          :disabled="!inputQuery.trim() || isLoading"
        >
          <HugeiconsIcon :icon="ArrowRight01Icon" :size="18" :stroke-width="2.2" color="#000000" />
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, reactive } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  AiChat02Icon,
  ArrowRight01Icon,
  Calculator01Icon,
  RefreshIcon,
  ShieldCheckIcon,
  CreditCardValidationIcon
} from '@hugeicons/core-free-icons';
import { askFinanceAssistant, askFinancialAdvisor, GROQ_MODELS } from '../services/groq.js';
import {
  validatePan,
  maskPan,
  calculateEligibleLoan,
  saveProfileToLedger
} from '../services/cibil.js';

const props = defineProps({
  activeModel: {
    type: String,
    default: 'openai/gpt-oss-120b'
  },
  prefilledQuery: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['clear-prefilled', 'nav']);

const chatContainer = ref(null);
const inputQuery = ref('');
const isLoading = ref(false);

const activeModelObj = computed(() => {
  return GROQ_MODELS.find(m => m.id === props.activeModel);
});

// Sequential Loan Session: collects Name -> PAN -> DOB
const loanSession = reactive({
  active: false,
  step: 0, // 1 = Name, 2 = PAN, 3 = DOB
  fullName: '',
  pan: '',
  dob: ''
});

const currentStepInstruction = computed(() => {
  switch (loanSession.step) {
    case 1:
      return 'Enter your full legal name:';
    case 2:
      return 'Enter your 10-character PAN (e.g. ABCDE1234F):';
    case 3:
      return 'Enter your date of birth (DD/MM/YYYY):';
    default:
      return '';
  }
});

const currentPlaceholder = computed(() => {
  if (loanSession.active) {
    switch (loanSession.step) {
      case 1:
        return 'Enter your full name...';
      case 2:
        return 'Enter 10-character PAN (e.g. ABCDE1234F)...';
      case 3:
        return 'Enter date of birth (e.g. 15/08/1995)...';
      default:
        return 'Type your response...';
    }
  }
  return 'Enter Name, PAN, DOB or ask a question...';
});

const messages = ref([
  {
    role: 'assistant',
    text: 'Welcome! Share your name, PAN number, and date of birth to check your pre-approved loan amount.',
    time: formatTimeNow(),
    model: props.activeModel
  }
]);

watch(
  () => props.prefilledQuery,
  (val) => {
    if (val) {
      inputQuery.value = val;
      emit('clear-prefilled');
    }
  },
  { immediate: true }
);

function formatTimeNow() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function cleanNoHash(text) {
  if (!text) return '';
  return text.replace(/#+/g, '').trim();
}

function startLoanFlow() {
  loanSession.active = true;
  loanSession.step = 1;
  loanSession.fullName = '';
  loanSession.pan = '';
  loanSession.dob = '';

  messages.value.push({
    role: 'assistant',
    text: 'Please enter your full legal name.',
    time: formatTimeNow(),
    model: props.activeModel
  });
  scrollToBottom();
}

function cancelLoanFlow() {
  loanSession.active = false;
  loanSession.step = 0;
  messages.value.push({
    role: 'assistant',
    text: 'Loan assessment cancelled. You can restart anytime or ask any question.',
    time: formatTimeNow(),
    model: props.activeModel
  });
  scrollToBottom();
}

function fillDemoData() {
  inputQuery.value = 'Ritam Rabha, ABCDE1234F, 15/08/1995';
  handleSubmit();
}

function sendSuggested(text) {
  inputQuery.value = text;
  handleSubmit();
}

// Check if a message contains all 3 parameters: Name, PAN, DOB
function parseFullLoanPayload(text) {
  const panMatch = text.match(/[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}/);
  const dobMatch = text.match(/\b(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})\b/);
  
  if (panMatch && dobMatch) {
    let name = 'Applicant';
    // Remove the PAN and DOB from the text to isolate the name
    let remainder = text.replace(panMatch[0], '').replace(dobMatch[0], '');
    remainder = remainder.replace(/name|pan|dob|date of birth|is|my|and|,|:|;/gi, '').trim();
    if (remainder.length >= 2) {
      name = remainder.replace(/\s+/g, ' ').trim();
    }
    return {
      fullName: name,
      pan: panMatch[0].toUpperCase(),
      dob: dobMatch[0]
    };
  }
  return null;
}

async function processLoanApproval(payload) {
  isLoading.value = true;
  scrollToBottom();

  try {
    await new Promise(r => setTimeout(r, 400)); // Minimal realistic delay

    const report = calculateEligibleLoan(payload);

    // Save profile to backend Azure SQL / SQLite
    saveProfileToLedger({
      fullName: report.fullName,
      rawPan: report.pan,
      cibilScore: report.cibilScore
    }).catch(() => {});

    // 1 clean sentence without '#'
    const sentence = `Based on your PAN ${report.panMasked} and date of birth, your pre-approved eligible loan amount is ${report.loanAmountFormatted} at ${report.interestRate}.`;

    messages.value.push({
      role: 'assistant',
      text: sentence,
      loanReport: report,
      time: formatTimeNow(),
      model: props.activeModel
    });
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      text: `Unable to compute loan limit: ${err.message}`,
      time: formatTimeNow(),
      model: props.activeModel
    });
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
}

async function handleSubmit() {
  const query = inputQuery.value.trim();
  if (!query || isLoading.value) return;

  const now = formatTimeNow();

  // Cancel commands
  if (['cancel', 'exit', 'stop'].includes(query.toLowerCase())) {
    messages.value.push({ role: 'user', text: query, time: now });
    inputQuery.value = '';
    cancelLoanFlow();
    return;
  }

  // 1. Direct one-shot extraction: if user sends Name, PAN, and DOB together
  const fullPayload = parseFullLoanPayload(query);
  if (fullPayload) {
    messages.value.push({ role: 'user', text: query, time: now });
    inputQuery.value = '';
    loanSession.active = false;
    loanSession.step = 0;
    await processLoanApproval(fullPayload);
    return;
  }

  // 2. Sequential Step Progression
  if (loanSession.active) {
    messages.value.push({ role: 'user', text: query, time: now });
    inputQuery.value = '';
    scrollToBottom();

    if (loanSession.step === 1) {
      // Step 1: Name
      if (query.length < 2) {
        messages.value.push({
          role: 'assistant',
          text: 'Please enter a valid full name with at least 2 characters.',
          time: formatTimeNow(),
          model: props.activeModel
        });
        scrollToBottom();
        return;
      }
      loanSession.fullName = query.trim();
      loanSession.step = 2;
      messages.value.push({
        role: 'assistant',
        text: `Name recorded as ${loanSession.fullName}. Please enter your 10-character PAN number.`,
        time: formatTimeNow(),
        model: props.activeModel
      });
      scrollToBottom();
      return;
    }

    if (loanSession.step === 2) {
      // Step 2: PAN
      const panMatch = query.match(/[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}/);
      const cleanPan = panMatch ? panMatch[0].toUpperCase() : query.trim().toUpperCase();

      if (!validatePan(cleanPan)) {
        messages.value.push({
          role: 'assistant',
          text: 'Please enter a valid 10-character PAN (e.g. ABCDE1234F).',
          time: formatTimeNow(),
          model: props.activeModel
        });
        scrollToBottom();
        return;
      }

      loanSession.pan = cleanPan;
      loanSession.step = 3;
      messages.value.push({
        role: 'assistant',
        text: `PAN ${maskPan(cleanPan)} verified. Please enter your date of birth (DD/MM/YYYY).`,
        time: formatTimeNow(),
        model: props.activeModel
      });
      scrollToBottom();
      return;
    }

    if (loanSession.step === 3) {
      // Step 3: DOB -> Run it!
      const dobMatch = query.match(/\b(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})\b/);
      loanSession.dob = dobMatch ? dobMatch[0] : query.trim();

      const payload = {
        fullName: loanSession.fullName,
        pan: loanSession.pan,
        dob: loanSession.dob
      };

      loanSession.active = false;
      loanSession.step = 0;
      await processLoanApproval(payload);
      return;
    }
  }

  // 3. User asks to check loan or gives PAN trigger
  const lower = query.toLowerCase();
  if (
    lower.includes('loan') ||
    lower.includes('cibil') ||
    lower.includes('how much') ||
    lower.includes('credit limit') ||
    lower.includes('check score') ||
    lower.includes('pan')
  ) {
    messages.value.push({ role: 'user', text: query, time: now });
    inputQuery.value = '';

    // Check if PAN was in the query
    const panMatch = query.match(/[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}/);
    if (panMatch && validatePan(panMatch[0])) {
      loanSession.active = true;
      loanSession.pan = panMatch[0].toUpperCase();
      loanSession.fullName = 'Applicant';
      loanSession.step = 3;
      messages.value.push({
        role: 'assistant',
        text: `PAN ${maskPan(loanSession.pan)} verified. Please enter your date of birth (DD/MM/YYYY) to calculate your loan amount.`,
        time: formatTimeNow(),
        model: props.activeModel
      });
      scrollToBottom();
      return;
    }

    // Start 3-step sequence
    startLoanFlow();
    return;
  }

  // 4. Standard conversational/financial query: respond in 1 sentence max with no '#'
  messages.value.push({ role: 'user', text: query, time: now });
  inputQuery.value = '';
  isLoading.value = true;
  scrollToBottom();

  try {
    const history = messages.value.map(m => ({
      role: m.role,
      content: m.text
    }));

    const result = await askFinancialAdvisor(query, history, props.activeModel);
    
    // Ensure 1 sentence max & no '#'
    let text = (result.text || 'You can share your name, PAN, and date of birth to check your pre-approved loan amount.').replace(/#+/g, '').trim();
    const firstSentence = text.split(/(?<=[.?!])\s+/)[0] || text;
    text = firstSentence.trim();

    messages.value.push({
      role: 'assistant',
      text,
      time: formatTimeNow(),
      model: props.activeModel
    });
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      text: 'Share your name, PAN number, and date of birth to check your eligible loan limit.',
      time: formatTimeNow(),
      model: props.activeModel
    });
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
}

function handleOpenCalculator(report) {
  if (report) {
    const loanPayload = {
      principal: report.loanAmount || 1500000,
      rate: parseFloat(report.interestRate) || 8.5,
      tenure: 3,
      unit: 'years'
    };
    localStorage.setItem('cibil_selected_loan', JSON.stringify(loanPayload));
  }
  emit('nav', 'calculator');
}

function clearHistory() {
  messages.value = [];
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
  });
}
</script>

<style scoped>
.mobile-chat-app {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 170px);
  max-width: 680px;
  margin: 0 auto;
  background: #000000;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
  position: relative;
}

/* Mobile Header Bar */
.chat-app-header {
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 0;
  border-top: none;
  border-left: none;
  border-right: none;
  border-bottom: 1px solid var(--border-subtle);
  background: #0A0A0A;
  z-index: 10;
}

.header-profile {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #18181B;
  border: 1px solid var(--border-bright);
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.profile-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.profile-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #FFFFFF;
}

.model-pill {
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: var(--radius-full);
  background: #181818;
  border: 1px solid var(--border-subtle);
  color: var(--text-dim);
}

.status-indicator-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.online-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #2DD4BF;
  box-shadow: 0 0 6px rgba(45, 212, 191, 0.6);
}

.status-text {
  font-size: 0.7rem;
  color: var(--text-dim);
}

.btn-icon-only {
  width: 32px;
  height: 32px;
  padding: 0;
  border-radius: 50%;
}

/* Active Stepper Strip */
.loan-stepper-strip {
  padding: 8px 16px;
  background: #111111;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.775rem;
}

.stepper-text {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #FFFFFF;
}

.stepper-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  background: #FFFFFF;
  color: #000000;
}

.btn-cancel-step {
  background: transparent;
  border: none;
  color: var(--text-dim);
  font-size: 0.725rem;
  cursor: pointer;
}

.btn-cancel-step:hover {
  color: #FFFFFF;
}

/* Messages Stream */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chat-welcome {
  margin: auto;
  text-align: center;
  padding: 24px 16px;
  max-width: 360px;
}

.welcome-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #141414;
  border: 1px solid var(--border-bright);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px auto;
}

.welcome-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #FFFFFF;
  margin-bottom: 6px;
}

.welcome-desc {
  font-size: 0.8rem;
  color: var(--text-dim);
  line-height: 1.4;
}

.message-wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
}

/* Mobile Native Chat Bubbles */
.user-bubble {
  align-self: flex-end;
  max-width: 82%;
  background: #27272A;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 18px 18px 4px 18px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.assistant-bubble {
  align-self: flex-start;
  max-width: 88%;
  background: #141414;
  border: 1px solid var(--border-subtle);
  border-radius: 18px 18px 18px 4px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bubble-sender-tag {
  font-size: 0.675rem;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.bubble-body {
  font-size: 0.875rem;
  color: #FFFFFF;
  line-height: 1.4;
}

.bubble-time {
  font-size: 0.65rem;
  color: var(--text-dim);
  align-self: flex-end;
}

.ai-time {
  align-self: flex-start;
}

/* Pre-Approved Loan Amount Card */
.loan-amount-card {
  margin-top: 6px;
  background: #080808;
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-md);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.loan-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.7rem;
}

.loan-card-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #FFFFFF;
  color: #000000;
  padding: 3px 8px;
  border-radius: var(--radius-full);
  font-weight: 700;
  font-size: 0.65rem;
  letter-spacing: 0.04em;
}

.loan-approved-date {
  color: var(--text-dim);
}

.loan-amount-hero {
  text-align: center;
  padding: 10px 0;
  border-top: 1px solid var(--border-subtle);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.amount-label {
  font-size: 0.7rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.amount-number {
  font-size: 2.2rem;
  font-weight: 800;
  color: #FFFFFF;
  font-family: var(--font-mono);
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.amount-sub {
  font-size: 0.7rem;
  color: #2DD4BF;
}

.loan-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.meta-item {
  background: #111111;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xs);
  padding: 6px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.m-lbl {
  font-size: 0.65rem;
  color: var(--text-dim);
  text-transform: uppercase;
}

.m-val {
  font-size: 0.8rem;
  font-weight: 600;
  color: #FFFFFF;
}

.m-val.highlight {
  color: #2DD4BF;
}

.font-mono {
  font-family: var(--font-mono);
}

.loan-card-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.loading-bubble {
  padding: 10px 14px;
}

.loading-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: var(--text-muted);
}

/* Quick Action Chips */
.quick-chips-row {
  display: flex;
  gap: 8px;
  padding: 8px 14px;
  overflow-x: auto;
  white-space: nowrap;
  border-top: 1px solid var(--border-subtle);
  background: #050505;
}

.quick-chips-row::-webkit-scrollbar {
  display: none;
}

.quick-chip {
  padding: 6px 12px;
  border-radius: var(--radius-full);
  background: #141414;
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s ease;
}

.quick-chip:hover {
  background: #202020;
  border-color: var(--border-bright);
  color: #FFFFFF;
}

.highlight-chip {
  background: #FFFFFF;
  color: #000000;
  border-color: #FFFFFF;
  font-weight: 600;
}

.highlight-chip:hover {
  background: #E2E8F0;
  color: #000000;
}

/* Mobile Input Bar */
.chat-input-bar {
  padding: 10px 14px;
  background: #0A0A0A;
  border-top: 1px solid var(--border-subtle);
}

.mobile-input-form {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mobile-chat-input {
  flex: 1;
  padding: 10px 16px;
  border-radius: var(--radius-full);
  background: #141414;
  border: 1px solid var(--border-subtle);
  color: #FFFFFF;
  font-size: 0.85rem;
  outline: none;
  font-family: var(--font-sans);
}

.mobile-chat-input:focus {
  border-color: #FFFFFF;
}

.mobile-send-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #FFFFFF;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: transform 0.1s ease;
}

.mobile-send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.mobile-send-btn:not(:disabled):hover {
  transform: scale(1.05);
}

@media (max-width: 640px) {
  .mobile-chat-app {
    height: calc(100vh - 145px);
    border-radius: 0;
    border-left: none;
    border-right: none;
  }
  .amount-number {
    font-size: 1.9rem;
  }
}
</style>
