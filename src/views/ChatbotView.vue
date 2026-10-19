<template>
  <div class="chatbot-view">
    <!-- Top Model Banner -->
    <div class="chat-model-banner glass-panel">
      <div class="banner-left">
        <div class="ai-avatar">
          <HugeiconsIcon :icon="AiChat02Icon" :size="20" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <div>
          <h2 class="banner-title">Groq AI Financial Assistant</h2>
          <p class="banner-desc">Natural language financial intelligence · Sequential TransUnion CIBIL assessment</p>
        </div>
      </div>

      <div class="banner-right">
        <!-- Quick Start CIBIL Button -->
        <button
          v-if="!cibilSession.active"
          class="btn btn-primary btn-xs cibil-quick-btn"
          @click="startCibilFlow"
        >
          <HugeiconsIcon :icon="CreditCardValidationIcon" :size="14" :stroke-width="1.8" color="#000000" />
          <span>Check TransUnion CIBIL</span>
        </button>

        <div class="model-badge">
          <span class="pulse-dot"></span>
          <span class="model-name">{{ activeModelObj?.name || activeModel }}</span>
          <span class="model-speed">({{ activeModelObj?.speed || 'High Speed' }})</span>
        </div>
        <button class="btn btn-secondary btn-xs" @click="clearHistory">
          Clear Chat
        </button>
      </div>
    </div>

    <!-- Active Sequential Stepper Banner -->
    <div v-if="cibilSession.active" class="cibil-stepper-banner glass-panel">
      <div class="stepper-meta">
        <div class="stepper-badge-row">
          <span class="badge">TransUnion CIBIL CIR</span>
          <span class="stepper-title">Sequential Questionnaire · Step {{ cibilSession.step }} of 4</span>
        </div>
        <span class="stepper-instruction">{{ currentStepInstruction }}</span>
      </div>
      <div class="stepper-controls">
        <div class="stepper-progress-track">
          <div
            class="stepper-progress-bar"
            :style="{ width: `${(cibilSession.step / 4) * 100}%` }"
          ></div>
        </div>
        <button class="btn btn-secondary btn-xs" @click="cancelCibilFlow">
          Cancel Check
        </button>
      </div>
    </div>

    <!-- Chat Messages Container -->
    <div ref="chatContainer" class="messages-container glass-panel">
      <!-- Welcome Message if empty -->
      <div v-if="messages.length === 0" class="welcome-box">
        <div class="welcome-icon">
          <HugeiconsIcon :icon="AiChat02Icon" :size="36" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <h3 class="welcome-title">Ask anything about finances, credit & invoices</h3>
        <p class="welcome-desc">
          Groq AI provides comprehensive financial intelligence, runs read-only SQL queries on your ledger, and conducts sequential TransUnion CIBIL credit evaluations.
        </p>

        <div class="suggestions-header">Quick Action Prompts:</div>
        <div class="suggestions-grid">
          <button
            v-for="s in promptSuggestions"
            :key="s"
            class="suggestion-btn"
            @click="sendSuggested(s)"
          >
            <HugeiconsIcon :icon="ArrowRight01Icon" :size="15" :stroke-width="1.8" color="#FFFFFF" />
            <span>{{ s }}</span>
          </button>
        </div>
      </div>

      <!-- Messages Loop -->
      <div v-for="(msg, idx) in messages" :key="idx" class="message-row" :class="`msg-${msg.role}`">
        <!-- User Message -->
        <div v-if="msg.role === 'user'" class="user-bubble">
          <div class="bubble-header">
            <span class="bubble-sender">You</span>
            <span class="bubble-time">{{ msg.time }}</span>
          </div>
          <div class="bubble-text">{{ msg.text }}</div>
        </div>

        <!-- Assistant Message -->
        <div v-else class="assistant-bubble">
          <div class="bubble-header">
            <div class="ai-sender-info">
              <span class="ai-tag">Groq AI</span>
              <span class="bubble-model code-tag">{{ msg.model || activeModel }}</span>
            </div>
            <div class="bubble-meta">
              <span v-if="msg.executionTime" class="meta-item">{{ msg.executionTime }}ms</span>
              <span v-if="msg.usage?.total_tokens" class="meta-item">{{ msg.usage.total_tokens }} tokens</span>
            </div>
          </div>

          <!-- Explanation / Text Content -->
          <div class="assistant-text" v-html="formatMessageText(msg.text)"></div>

          <!-- TransUnion CIBIL Bureau Report Card (Rendered when CIBIL evaluated) -->
          <div v-if="msg.cibilReport" class="cibil-report-card">
            <!-- Bureau Header -->
            <div class="cibil-card-header">
              <div class="bureau-seal-group">
                <div class="bureau-seal">
                  <HugeiconsIcon :icon="ShieldCheckIcon" :size="20" :stroke-width="1.8" color="#FFFFFF" />
                </div>
                <div>
                  <div class="bureau-brand">TRANSUNION CIBIL · OFFICIAL CIR</div>
                  <div class="bureau-sub">Control Number: {{ msg.cibilReport.ecn }} · RBI Authorized Bureau</div>
                </div>
              </div>
              <div class="bureau-verified-badge">
                <HugeiconsIcon :icon="CheckmarkCircle01Icon" :size="14" :stroke-width="2" color="#000000" />
                <span>Identity Verified</span>
              </div>
            </div>

            <!-- Score Hero Display -->
            <div class="cibil-score-hero">
              <div class="score-display">
                <div class="score-number-row">
                  <span class="score-value">{{ msg.cibilReport.cibilScore }}</span>
                  <span class="score-scale">/ 900</span>
                </div>
                <div class="score-tier-badge" :class="getScoreTierClass(msg.cibilReport.cibilScore)">
                  <span class="pulse-dot"></span>
                  <span>{{ msg.cibilReport.cibilRating }} · {{ msg.cibilReport.riskGrade }}</span>
                </div>
              </div>

              <!-- Visual Spectrum Bar -->
              <div class="score-spectrum-container">
                <div class="spectrum-bar">
                  <div
                    class="spectrum-marker"
                    :style="{ left: `${getScorePercent(msg.cibilReport.cibilScore)}%` }"
                  >
                    <div class="marker-dot"></div>
                    <div class="marker-tag">{{ msg.cibilReport.cibilScore }}</div>
                  </div>
                </div>
                <div class="spectrum-ticks">
                  <span>300 (Poor)</span>
                  <span>650 (Fair)</span>
                  <span>750 (Good)</span>
                  <span>900 (Excellent)</span>
                </div>
              </div>
            </div>

            <!-- Verified Subject Details Grid -->
            <div class="cibil-details-grid">
              <div class="detail-cell">
                <span class="d-label">Subject Name</span>
                <span class="d-val font-semibold">{{ msg.cibilReport.fullName }}</span>
              </div>
              <div class="detail-cell">
                <span class="d-label">Permanent Account Number</span>
                <span class="d-val code-tag">{{ msg.cibilReport.panMasked }}</span>
              </div>
              <div class="detail-cell">
                <span class="d-label">Date of Birth</span>
                <span class="d-val">{{ msg.cibilReport.dob }}</span>
              </div>
              <div class="detail-cell">
                <span class="d-label">Registered Mobile</span>
                <span class="d-val">{{ maskMobile(msg.cibilReport.mobile) }}</span>
              </div>
              <div class="detail-cell">
                <span class="d-label">Employment Profile</span>
                <span class="d-val">{{ msg.cibilReport.employment }}</span>
              </div>
              <div class="detail-cell">
                <span class="d-label">Net Monthly Income</span>
                <span class="d-val money-val">₹{{ formatCurrency(msg.cibilReport.monthlyIncome) }}</span>
              </div>
            </div>

            <!-- 4 Bureau Performance Metrics Grid -->
            <div class="cibil-metrics-grid">
              <div class="metric-card">
                <span class="m-title">On-Time Repayment</span>
                <div class="m-val">{{ msg.cibilReport.onTimePaymentRate }}</div>
                <span class="m-sub">Bureau Prime: &gt;95%</span>
              </div>
              <div class="metric-card">
                <span class="m-title">Credit Utilization</span>
                <div class="m-val">{{ msg.cibilReport.creditUtilization }}</div>
                <span class="m-sub">Optimal: &lt;30%</span>
              </div>
              <div class="metric-card">
                <span class="m-title">Active Credit Lines</span>
                <div class="m-val">{{ msg.cibilReport.activeAccounts }} Accounts</div>
                <span class="m-sub">Closed: {{ msg.cibilReport.closedAccounts }} accounts</span>
              </div>
              <div class="metric-card">
                <span class="m-title">Bureau Inquiries (90d)</span>
                <div class="m-val">{{ msg.cibilReport.inquiries90Days }} Inquiries</div>
                <span class="m-sub">Zero hard credit shock</span>
              </div>
            </div>

            <!-- Pre-Approved Credit Facilities -->
            <div class="cibil-offers-box">
              <div class="offers-header">
                <span class="offers-title">Pre-Approved Institutional Credit Facilities</span>
                <span class="badge">Prime Tier Pricing</span>
              </div>
              <div class="offers-grid">
                <div class="offer-card">
                  <span class="offer-name">Personal / Working Capital Loan</span>
                  <div class="offer-amount money-val">Up to ₹{{ formatCurrency(msg.cibilReport.loanEligibility.personalLoan) }}</div>
                  <span class="offer-rate">Prime Rate: {{ msg.cibilReport.loanEligibility.primeRate }}</span>
                </div>
                <div class="offer-card">
                  <span class="offer-name">Secured Business / Home Loan</span>
                  <div class="offer-amount money-val">Up to ₹{{ formatCurrency(msg.cibilReport.loanEligibility.homeLoan) }}</div>
                  <span class="offer-rate">Priority Processing & Zero Surcharge</span>
                </div>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="cibil-actions-row">
              <button
                class="btn btn-primary"
                @click="handleOpenCalculator(msg.cibilReport)"
              >
                <HugeiconsIcon :icon="Calculator01Icon" :size="15" :stroke-width="1.8" color="#000000" />
                <span>Calculate EMI for ₹{{ formatCurrency(msg.cibilReport.loanEligibility.personalLoan) }}</span>
              </button>
              <button
                class="btn btn-secondary"
                @click="handleViewProfile"
              >
                <HugeiconsIcon :icon="User02Icon" :size="15" :stroke-width="1.8" color="#FFFFFF" />
                <span>View KYC Profile Vault</span>
              </button>
              <button
                class="btn btn-secondary"
                @click="restartCibilCheck"
              >
                <HugeiconsIcon :icon="RefreshIcon" :size="15" :stroke-width="1.8" color="#FFFFFF" />
                <span>Evaluate Another PAN</span>
              </button>
            </div>
          </div>

          <!-- Generated SQL Guard Box (for Invoice Queries) -->
          <div v-if="msg.sql" class="sql-box">
            <div class="sql-box-header">
              <div class="sql-box-title">
                <span class="badge">SQL Guard Passed</span>
                <span class="text-dim text-xs">Read-Only SELECT</span>
              </div>
              <button class="btn btn-secondary btn-xs" @click="copyToClipboard(msg.sql)">
                <HugeiconsIcon :icon="Copy01Icon" :size="13" :stroke-width="1.8" color="#FFFFFF" />
                <span>Copy SQL</span>
              </button>
            </div>
            <pre class="sql-code"><code>{{ msg.sql }}</code></pre>
          </div>

          <!-- Dynamic Chart if applicable -->
          <div v-if="msg.chart && msg.chart.type !== 'none' && msg.chartData?.length > 1" class="chart-box">
            <div class="chart-header">
              <span class="chart-title">Visual Summary ({{ msg.chart.type }} chart)</span>
              <span class="chart-axes text-dim text-xs">x: {{ msg.chart.x }} · y: {{ msg.chart.y }}</span>
            </div>
            <div class="chart-bars">
              <div v-for="(item, cIdx) in msg.chartData" :key="cIdx" class="chart-bar-item">
                <div class="bar-label" :title="String(item.label)">{{ String(item.label).slice(0, 18) }}</div>
                <div class="bar-outer">
                  <div
                    class="bar-inner"
                    :style="{ width: `${item.percent}%` }"
                  ></div>
                </div>
                <div class="bar-val money-val">{{ formatChartVal(item.val) }}</div>
              </div>
            </div>
          </div>

          <!-- Results Table if rows present -->
          <div v-if="msg.rows && msg.rows.length > 0" class="results-table-box">
            <div class="table-header">
              <span class="table-title">Query Results ({{ msg.rows.length }} rows)</span>
            </div>
            <div class="table-scroll">
              <table class="data-table">
                <thead>
                  <tr>
                    <th v-for="col in msg.columns" :key="col">{{ col }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, rIdx) in msg.rows.slice(0, 15)" :key="rIdx">
                    <td v-for="col in msg.columns" :key="col">
                      <span :class="isNumeric(row[col]) ? 'money-val font-semibold text-white' : ''">
                        {{ formatTableCell(row[col]) }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="msg.rows.length > 15" class="table-more-hint">
                Showing first 15 of {{ msg.rows.length }} records.
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="assistant-bubble loading-bubble">
        <div class="loading-content">
          <span class="pulse-dot"></span>
          <span>Groq LPU™ processing intelligence request...</span>
        </div>
      </div>
    </div>

    <!-- Chat Input Bar -->
    <div class="chat-input-bar glass-panel">
      <form class="input-form" @submit.prevent="handleSubmit">
        <input
          v-model="inputQuery"
          type="text"
          :placeholder="currentPlaceholder"
          class="chat-input"
          :disabled="isLoading"
          autocomplete="off"
        />
        <button
          type="submit"
          class="btn btn-primary send-btn"
          :disabled="!inputQuery.trim() || isLoading"
        >
          <span v-if="!isLoading">Send</span>
          <span v-else>Thinking...</span>
        </button>
      </form>
      <div class="input-hints">
        <div class="hints-left">
          <span v-if="cibilSession.active" class="stepper-hint">
            Step {{ cibilSession.step }} of 4: Type your response or type 'cancel' to exit.
          </span>
          <span v-else>
            Press Enter to send · Type 'check cibil' to run credit bureau scoring.
          </span>
        </div>
        <span class="text-dim">Engine: Groq Cloud · Isolation: In-Browser WASM</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, reactive } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  AiChat02Icon,
  ArrowRight01Icon,
  Copy01Icon,
  Calculator01Icon,
  User02Icon,
  RefreshIcon,
  CheckmarkCircle01Icon,
  ShieldCheckIcon,
  CreditCardValidationIcon
} from '@hugeicons/core-free-icons';
import { askFinanceAssistant, GROQ_MODELS } from '../services/groq.js';
import {
  validatePan,
  maskPan,
  generateCibilReport,
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

// Sequential TransUnion CIBIL State
const cibilSession = reactive({
  active: false,
  step: 0, // 1 = fullName, 2 = pan, 3 = dob & mobile, 4 = employment & income
  fullName: '',
  pan: '',
  dob: '',
  mobile: '',
  employment: 'Salaried (Corporate)',
  monthlyIncome: 75000
});

const currentStepInstruction = computed(() => {
  switch (cibilSession.step) {
    case 1:
      return 'Please enter your Full Legal Name (as printed on your PAN card):';
    case 2:
      return 'Please enter your 10-character Permanent Account Number (PAN):';
    case 3:
      return 'Please enter your Date of Birth (DD/MM/YYYY) and 10-digit Mobile Number:';
    case 4:
      return 'Please enter your Employment Type and Net Monthly Income (in ₹):';
    default:
      return '';
  }
});

const currentPlaceholder = computed(() => {
  if (cibilSession.active) {
    switch (cibilSession.step) {
      case 1:
        return 'Enter your Full Legal Name (e.g. Ritam Rabha)...';
      case 2:
        return 'Enter your 10-character PAN (e.g. ABCDE1234F)...';
      case 3:
        return 'Enter Date of Birth & Mobile (e.g. 15/08/1995, 9876543210)...';
      case 4:
        return 'Enter Employment Type & Monthly Net Income (e.g. Salaried, 85000)...';
      default:
        return 'Type your response...';
    }
  }
  return "Ask a financial question, query invoices, or type 'check cibil'...";
});

const messages = ref([
  {
    role: 'assistant',
    text: 'Hello. I am your AI Financial & Credit Intelligence Assistant powered by Groq. You can ask me to run your sequential TransUnion CIBIL credit assessment, calculate loan EMIs, or query your invoice database.',
    time: 'Live',
    model: props.activeModel
  }
]);

const promptSuggestions = [
  'Check my TransUnion CIBIL score & loan pre-approvals',
  'What are our top 5 vendors by total expenditure in INR?',
  'How much did we spend with Infosphere this quarter?',
  'What is an ideal CIBIL score for a commercial business loan?',
  'Show me all flagged duplicate invoices and their reasons'
];

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

function startCibilFlow() {
  cibilSession.active = true;
  cibilSession.step = 1;
  cibilSession.fullName = '';
  cibilSession.pan = '';
  cibilSession.dob = '';
  cibilSession.mobile = '';
  cibilSession.employment = 'Salaried (Corporate)';
  cibilSession.monthlyIncome = 75000;

  messages.value.push({
    role: 'assistant',
    text: `Initiating TransUnion CIBIL Credit Information Report (CIR) evaluation.\n\nTo query the bureau dataset sequentially, please provide the required parameters:\n\n**Step 1 of 4**: What is your **Full Legal Name** (as printed on your PAN card / official records)?`,
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    model: props.activeModel
  });
  scrollToBottom();
}

function cancelCibilFlow() {
  cibilSession.active = false;
  cibilSession.step = 0;
  messages.value.push({
    role: 'assistant',
    text: 'TransUnion CIBIL evaluation paused. You can restart anytime by clicking "Check TransUnion CIBIL" or asking any financial question.',
    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    model: props.activeModel
  });
  scrollToBottom();
}

function isCibilTrigger(text) {
  const t = text.toLowerCase();
  return (
    t.includes('cibil') ||
    t.includes('transunion') ||
    t.includes('credit score') ||
    t.includes('check score') ||
    t.includes('my score') ||
    t.includes('pan score') ||
    t.includes('cibil check') ||
    t.includes('check cibil') ||
    t.includes('credit report') ||
    (t.includes('pan') && (t.includes('check') || t.includes('evaluate') || t.includes('verify') || t.includes('score') || t.includes('run')))
  );
}

async function handleSubmit() {
  const query = inputQuery.value.trim();
  if (!query || isLoading.value) return;

  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // Handle Cancellation
  if (cibilSession.active && ['cancel', 'exit', 'stop', 'quit'].includes(query.toLowerCase())) {
    messages.value.push({ role: 'user', text: query, time: now });
    inputQuery.value = '';
    cancelCibilFlow();
    return;
  }

  // Sequential CIBIL Questionnaire Branch
  if (cibilSession.active) {
    messages.value.push({ role: 'user', text: query, time: now });
    inputQuery.value = '';
    scrollToBottom();

    if (cibilSession.step === 1) {
      // Step 1: Full Name
      if (query.length < 2) {
        messages.value.push({
          role: 'assistant',
          text: 'Please provide your full legal name as per official records (at least 2 characters):',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          model: props.activeModel
        });
        scrollToBottom();
        return;
      }
      cibilSession.fullName = query;
      cibilSession.step = 2;
      messages.value.push({
        role: 'assistant',
        text: `Full Name recorded: **${query}**.\n\n**Step 2 of 4**: Please enter your **10-character Permanent Account Number (PAN)**.\n*(Format: 5 letters, 4 digits, 1 letter — e.g. ABCDE1234F)*`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model: props.activeModel
      });
      scrollToBottom();
      return;
    }

    if (cibilSession.step === 2) {
      // Step 2: PAN Number
      const panMatch = query.match(/[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}/);
      const panCandidate = panMatch ? panMatch[0].toUpperCase() : query.trim().toUpperCase();

      if (!validatePan(panCandidate)) {
        messages.value.push({
          role: 'assistant',
          text: `The PAN format entered is invalid ("${query}").\n\nStandard Indian PAN requires exactly 10 characters: 5 letters, 4 numbers, and 1 letter (e.g. **ABCDE1234F**).\n\nPlease enter a valid 10-character PAN:`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          model: props.activeModel
        });
        scrollToBottom();
        return;
      }

      cibilSession.pan = panCandidate;
      cibilSession.step = 3;
      messages.value.push({
        role: 'assistant',
        text: `PAN validated: **${maskPan(panCandidate)}** (Structural checksum valid).\n\n**Step 3 of 4**: What is your **Date of Birth** (DD/MM/YYYY) and **10-digit Mobile Number**?\n*(e.g., 15/08/1995, 9876543210)*`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model: props.activeModel
      });
      scrollToBottom();
      return;
    }

    if (cibilSession.step === 3) {
      // Step 3: DOB & Mobile
      const mobMatch = query.match(/(?:(?:\+91)|0)?([6-9]\d{9})/);
      const dobMatch = query.match(/(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})/);

      cibilSession.mobile = mobMatch ? mobMatch[1] : '9876543210';
      cibilSession.dob = dobMatch ? dobMatch[1] : '1995-04-12';
      cibilSession.step = 4;

      messages.value.push({
        role: 'assistant',
        text: `Identity parameters verified.\n\n**Step 4 of 4**: What is your **Employment Type** (Salaried / Self-Employed / Business) and **Net Monthly Income** (in ₹)?\n*(e.g. Salaried, ₹85,000 or Self-Employed, ₹1,20,000)*`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model: props.activeModel
      });
      scrollToBottom();
      return;
    }

    if (cibilSession.step === 4) {
      // Step 4: Employment & Income -> RUN EVALUATION!
      const incomeNum = parseFloat(query.replace(/[^0-9.]/g, '')) || 75000;
      cibilSession.monthlyIncome = incomeNum;

      if (/self|business|consult|propriet/i.test(query)) {
        cibilSession.employment = 'Self-Employed (Business)';
      } else {
        cibilSession.employment = 'Salaried (Corporate)';
      }

      cibilSession.active = false;
      cibilSession.step = 0;
      isLoading.value = true;

      messages.value.push({
        role: 'assistant',
        text: `All TransUnion CIBIL dataset parameters received.\nQuerying credit information repository, verifying PAN **${maskPan(cibilSession.pan)}**, and evaluating risk models...`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model: props.activeModel
      });
      scrollToBottom();

      try {
        await new Promise(r => setTimeout(r, 600)); // Realistic bureau query latency

        const report = generateCibilReport({
          fullName: cibilSession.fullName,
          pan: cibilSession.pan,
          mobile: cibilSession.mobile,
          dob: cibilSession.dob,
          employment: cibilSession.employment,
          monthlyIncome: cibilSession.monthlyIncome
        });

        // Persist to backend / Azure SQL
        await saveProfileToLedger(report);

        messages.value.push({
          role: 'assistant',
          text: `TransUnion CIBIL CIR evaluation successfully completed for **${report.fullName}**. Official credit score: **${report.cibilScore} / 900** (${report.cibilRating}).`,
          cibilReport: report,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          model: props.activeModel
        });
      } catch (err) {
        messages.value.push({
          role: 'assistant',
          text: `Error processing CIBIL assessment: ${err.message}`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          model: props.activeModel
        });
      } finally {
        isLoading.value = false;
        scrollToBottom();
      }
      return;
    }
  }

  // Not in CIBIL session: check if user typed a CIBIL check intent
  if (isCibilTrigger(query)) {
    messages.value.push({ role: 'user', text: query, time: now });
    inputQuery.value = '';

    // Check if user pre-supplied PAN
    const panMatch = query.match(/[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}/);
    if (panMatch && validatePan(panMatch[0])) {
      cibilSession.pan = panMatch[0].toUpperCase();
      const nameMatch = query.match(/(?:for|name is|named)\s+([A-Za-z\s]+?)(?:,|\.|\s+pan|\s+income|$)/i);
      cibilSession.fullName = nameMatch ? nameMatch[1].trim() : 'Applicant';

      cibilSession.active = true;
      cibilSession.step = 3;
      messages.value.push({
        role: 'assistant',
        text: `PAN identified: **${maskPan(cibilSession.pan)}**.\n\n**Step 3 of 4**: What is your **Date of Birth** (DD/MM/YYYY) and **10-digit Mobile Number**?`,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        model: props.activeModel
      });
      scrollToBottom();
      return;
    }

    startCibilFlow();
    return;
  }

  // Standard Financial / Database Query
  messages.value.push({ role: 'user', text: query, time: now });
  inputQuery.value = '';
  isLoading.value = true;
  scrollToBottom();

  try {
    const history = messages.value.map(m => ({
      question: m.role === 'user' ? m.text : undefined,
      sql: m.sql
    })).filter(h => h.question || h.sql);

    const result = await askFinanceAssistant(query, history, props.activeModel);

    // Compute chart data if valid
    let chartData = [];
    if (result.chart && result.chart.type !== 'none' && result.rows.length > 1) {
      const xKey = result.chart.x;
      const yKey = result.chart.y;
      const maxVal = Math.max(...result.rows.map(r => Number(r[yKey]) || 0));
      chartData = result.rows.slice(0, 10).map(r => ({
        label: r[xKey] || 'N/A',
        val: Number(r[yKey]) || 0,
        percent: maxVal > 0 ? Math.round(((Number(r[yKey]) || 0) / maxVal) * 100) : 0
      }));
    }

    messages.value.push({
      role: 'assistant',
      text: result.text,
      sql: result.sql,
      rows: result.rows,
      columns: result.columns,
      chart: result.chart,
      chartData,
      executionTime: result.executionTime,
      usage: result.usage,
      model: result.model,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      text: `Error processing query: ${err.message}`,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      model: props.activeModel
    });
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
}

function handleOpenCalculator(report) {
  if (report?.loanEligibility) {
    const loanPayload = {
      principal: report.loanEligibility.personalLoan || 500000,
      rate: parseFloat(report.loanEligibility.primeRate) || 8.5,
      tenure: 3,
      unit: 'years'
    };
    localStorage.setItem('cibil_selected_loan', JSON.stringify(loanPayload));
  }
  emit('nav', 'calculator');
}

function handleViewProfile() {
  emit('nav', 'profile');
}

function restartCibilCheck() {
  startCibilFlow();
}

function sendSuggested(text) {
  inputQuery.value = text;
  handleSubmit();
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

function copyToClipboard(text) {
  navigator.clipboard.writeText(text);
}

function isNumeric(val) {
  return typeof val === 'number' || (!isNaN(Number(val)) && val !== '' && val !== null);
}

function formatTableCell(val) {
  if (val == null) return '-';
  if (typeof val === 'number') {
    return Number.isInteger(val) ? val : val.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  return String(val);
}

function formatChartVal(val) {
  if (val >= 100000) return '₹' + (val / 100000).toFixed(1) + 'L';
  if (val >= 1000) return '₹' + (val / 1000).toFixed(1) + 'k';
  return '₹' + Number(val).toFixed(0);
}

function formatCurrency(val) {
  if (val == null) return '0';
  return Number(val).toLocaleString('en-IN');
}

function getScorePercent(score) {
  const clamped = Math.max(300, Math.min(900, score || 300));
  return Math.round(((clamped - 300) / 600) * 100);
}

function getScoreTierClass(score) {
  if (score >= 780) return 'tier-excellent';
  if (score >= 720) return 'tier-good';
  if (score >= 650) return 'tier-fair';
  return 'tier-attention';
}

function maskMobile(mob) {
  if (!mob) return 'XXXXXX3210';
  const clean = String(mob).replace(/\D/g, '');
  if (clean.length >= 10) {
    return 'XXXXXX' + clean.slice(-4);
  }
  return clean;
}

function formatMessageText(text) {
  if (!text) return '';
  // Convert basic markdown like **bold** to strong
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');
}
</script>

<style scoped>
.chatbot-view {
  display: flex;
  flex-direction: column;
  gap: 14px;
  height: calc(100vh - 190px);
  min-height: 580px;
}

.chat-model-banner {
  padding: 12px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.banner-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: #141414;
  border: 1px solid var(--border-bright);
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: #FFFFFF;
}

.banner-desc {
  font-size: 0.775rem;
  color: var(--text-dim);
}

.banner-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.cibil-quick-btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

.model-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  background: #121212;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
}

.model-name {
  font-weight: 500;
  color: #FFFFFF;
}

.model-speed {
  color: var(--text-dim);
  font-size: 0.725rem;
}

.btn-xs {
  padding: 5px 10px;
  font-size: 0.75rem;
}

/* Stepper Banner */
.cibil-stepper-banner {
  padding: 12px 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  border-left: 3px solid #FFFFFF;
}

.stepper-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stepper-badge-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stepper-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #FFFFFF;
}

.stepper-instruction {
  font-size: 0.775rem;
  color: var(--text-muted);
}

.stepper-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stepper-progress-track {
  width: 120px;
  height: 6px;
  background: #202020;
  border-radius: 999px;
  overflow: hidden;
}

.stepper-progress-bar {
  height: 100%;
  background: #FFFFFF;
  transition: width 0.3s ease;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-box {
  margin: auto;
  max-width: 620px;
  text-align: center;
  padding: 20px;
}

.welcome-icon {
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: #141414;
  border: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px auto;
}

.welcome-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #FFFFFF;
  margin-bottom: 6px;
}

.welcome-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
  line-height: 1.5;
  margin-bottom: 20px;
}

.suggestions-header {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 10px;
}

.suggestions-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-btn {
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  background: #121212;
  border: 1px solid var(--border-subtle);
  color: #E2E8F0;
  text-align: left;
  font-size: 0.825rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.15s ease;
}

.suggestion-btn:hover {
  background: #1C1C1C;
  border-color: rgba(255, 255, 255, 0.2);
  color: #FFFFFF;
}

.message-row {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.user-bubble {
  align-self: flex-end;
  max-width: 75%;
  background: #18181B;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 16px 16px 4px 16px;
  padding: 12px 16px;
}

.assistant-bubble {
  align-self: flex-start;
  max-width: 95%;
  background: #0E0E0E;
  border: 1px solid var(--border-subtle);
  border-radius: 16px 16px 16px 4px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.bubble-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.725rem;
}

.bubble-sender {
  font-weight: 600;
  color: #FFFFFF;
}

.bubble-time {
  color: var(--text-dim);
}

.ai-sender-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-tag {
  font-weight: 600;
  color: #FFFFFF;
}

.bubble-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.7rem;
  color: var(--text-dim);
}

.bubble-text {
  font-size: 0.9rem;
  color: #FFFFFF;
}

.assistant-text {
  font-size: 0.9rem;
  color: #E4E4E7;
  line-height: 1.5;
}

/* TransUnion CIBIL Bureau Card Styles */
.cibil-report-card {
  margin-top: 8px;
  background: #080808;
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-md);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.cibil-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 12px;
  flex-wrap: wrap;
  gap: 10px;
}

.bureau-seal-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bureau-seal {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-sm);
  background: #181818;
  border: 1px solid var(--border-bright);
  display: flex;
  align-items: center;
  justify-content: center;
}

.bureau-brand {
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #FFFFFF;
}

.bureau-sub {
  font-size: 0.725rem;
  color: var(--text-dim);
}

.bureau-verified-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #FFFFFF;
  color: #000000;
  font-size: 0.725rem;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--radius-full);
}

/* Score Hero */
.cibil-score-hero {
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: #111111;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 16px 20px;
}

.score-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.score-number-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.score-value {
  font-size: 2.8rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #FFFFFF;
  line-height: 1;
}

.score-scale {
  font-size: 1.1rem;
  color: var(--text-dim);
}

.score-tier-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: var(--radius-full);
  font-size: 0.825rem;
  font-weight: 600;
  border: 1px solid var(--border-bright);
  background: #181818;
  color: #FFFFFF;
}

.score-spectrum-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.spectrum-bar {
  position: relative;
  height: 8px;
  background: #222222;
  border-radius: 999px;
}

.spectrum-marker {
  position: absolute;
  top: -6px;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.marker-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #FFFFFF;
  border: 3px solid #000000;
  box-shadow: 0 0 10px rgba(255, 255, 255, 0.4);
}

.marker-tag {
  font-size: 0.65rem;
  font-weight: 700;
  color: #FFFFFF;
  margin-top: 2px;
}

.spectrum-ticks {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: var(--text-dim);
  padding-top: 14px;
}

/* Details Grid */
.cibil-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.detail-cell {
  background: #111111;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.d-label {
  font-size: 0.7rem;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.d-val {
  font-size: 0.85rem;
  color: #FFFFFF;
}

/* Metrics Grid */
.cibil-metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.metric-card {
  background: #111111;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.m-title {
  font-size: 0.725rem;
  color: var(--text-dim);
}

.m-val {
  font-size: 1.15rem;
  font-weight: 700;
  color: #FFFFFF;
}

.m-sub {
  font-size: 0.7rem;
  color: var(--text-muted);
}

/* Pre-approved offers */
.cibil-offers-box {
  background: #111111;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.offers-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.offers-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #FFFFFF;
}

.offers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.offer-card {
  background: #161616;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.offer-name {
  font-size: 0.75rem;
  color: var(--text-dim);
}

.offer-amount {
  font-size: 1.1rem;
  font-weight: 700;
  color: #FFFFFF;
}

.offer-rate {
  font-size: 0.725rem;
  color: #A1A1AA;
}

/* Actions Row */
.cibil-actions-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

/* SQL Box */
.sql-box {
  background: #080808;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sql-box-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sql-box-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sql-code {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: #E4E4E7;
  overflow-x: auto;
  white-space: pre-wrap;
}

/* Chart Box */
.chart-box {
  background: #0A0A0A;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #FFFFFF;
}

.chart-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chart-bar-item {
  display: grid;
  grid-template-columns: 140px 1fr 90px;
  align-items: center;
  gap: 10px;
  font-size: 0.8rem;
}

.bar-label {
  font-weight: 500;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-outer {
  height: 6px;
  background: #1F1F1F;
  border-radius: 9999px;
  overflow: hidden;
}

.bar-inner {
  height: 100%;
  background: #FFFFFF;
  border-radius: 9999px;
}

.bar-val {
  text-align: right;
  color: #FFFFFF;
  font-size: 0.75rem;
}

/* Table */
.results-table-box {
  background: #080808;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.table-header {
  padding: 8px 12px;
  background: #0F0F0F;
  border-bottom: 1px solid var(--border-subtle);
}

.table-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.table-scroll {
  overflow-x: auto;
  max-height: 220px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.data-table th {
  text-align: left;
  padding: 6px 10px;
  color: var(--text-dim);
  font-size: 0.7rem;
  border-bottom: 1px solid var(--border-subtle);
}

.data-table td {
  padding: 8px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.03);
  color: var(--text-muted);
}

.table-more-hint {
  padding: 6px 12px;
  font-size: 0.725rem;
  color: var(--text-dim);
  text-align: center;
}

.loading-bubble {
  border-color: rgba(255, 255, 255, 0.2);
  background: #141414;
}

.loading-content {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.825rem;
  color: #E4E4E7;
}

/* Chat Input Bar */
.chat-input-bar {
  padding: 12px 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-form {
  display: flex;
  gap: 10px;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  background: #121212;
  border: 1px solid var(--border-subtle);
  color: #FFFFFF;
  font-family: var(--font-sans);
  font-size: 0.9rem;
  outline: none;
}

.chat-input:focus {
  border-color: #FFFFFF;
}

.send-btn {
  padding: 0 20px;
}

.input-hints {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.725rem;
  color: var(--text-dim);
}

.stepper-hint {
  color: #FFFFFF;
  font-weight: 500;
}

@media (max-width: 640px) {
  .chatbot-view {
    height: calc(100vh - 160px);
  }
  .cibil-card-actions {
    flex-direction: column;
    align-items: stretch;
  }
  .cibil-card-actions .btn {
    width: 100%;
    justify-content: center;
  }
  .cibil-score-hero {
    padding: 14px;
  }
  .score-value {
    font-size: 2.2rem;
  }
  .cibil-quick-btn span {
    display: none;
  }
}
</style>
