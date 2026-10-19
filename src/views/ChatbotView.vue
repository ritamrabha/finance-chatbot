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
          <p class="banner-desc">Natural language to safe SQLite query execution · Powered by Groq LPU™</p>
        </div>
      </div>

      <div class="banner-right">
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

    <!-- Chat Messages Container -->
    <div ref="chatContainer" class="messages-container glass-panel">
      <!-- Welcome Message if empty -->
      <div v-if="messages.length === 0" class="welcome-box">
        <div class="welcome-icon">
          <HugeiconsIcon :icon="AiChat02Icon" :size="36" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <h3 class="welcome-title">Ask anything about your invoices & expenditure</h3>
        <p class="welcome-desc">
          Groq AI translates questions into read-only SQL queries, executes them securely in isolated WebAssembly, and delivers financial summaries and charts.
        </p>

        <div class="suggestions-header">Example prompts:</div>
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

          <!-- Explanation Text -->
          <div class="assistant-text">
            {{ msg.text }}
          </div>

          <!-- Generated SQL Guard Box -->
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
          <span>Groq LPU™ analyzing financial schema and compiling safe SQL...</span>
        </div>
      </div>
    </div>

    <!-- Input Bar -->
    <div class="chat-input-bar glass-panel">
      <form class="input-form" @submit.prevent="handleSubmit">
        <input
          v-model="inputQuery"
          type="text"
          placeholder="Ask a question about your invoices (e.g. 'How much did we spend with Infosphere this quarter?')..."
          class="chat-input"
          :disabled="isLoading"
        />
        <button
          type="submit"
          class="btn btn-primary send-btn"
          :disabled="!inputQuery.trim() || isLoading"
        >
          <span v-if="!isLoading">Send Query</span>
          <span v-else>Thinking...</span>
        </button>
      </form>
      <div class="input-hints">
        <span>Press Enter to send · Read-only queries</span>
        <span class="text-dim">Engine: Groq Cloud · Isolation: In-Browser WASM</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  AiChat02Icon,
  ArrowRight01Icon,
  Copy01Icon
} from '@hugeicons/core-free-icons';
import { askFinanceAssistant, GROQ_MODELS } from '../services/groq.js';

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

const emit = defineEmits(['clear-prefilled']);

const chatContainer = ref(null);
const inputQuery = ref('');
const isLoading = ref(false);

const activeModelObj = computed(() => {
  return GROQ_MODELS.find(m => m.id === props.activeModel);
});

const messages = ref([
  {
    role: 'assistant',
    text: 'Hello. I am your AI Finance Assistant powered by Groq. Ask any question about your company invoices, vendors, tax, loan affordability, or duplicate flags. I will generate validated SQL, query the ledger, and provide you with instant figures and charts.',
    time: 'Live',
    model: props.activeModel
  }
]);

const promptSuggestions = [
  'How much did we spend with Infosphere this quarter?',
  'Show me all flagged duplicate invoices and their reasons',
  'What are our top 5 vendors by total expenditure in INR?',
  'What is the spending breakdown by currency?',
  'Show all invoices with total above ₹20,000'
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

async function handleSubmit() {
  const query = inputQuery.value.trim();
  if (!query || isLoading.value) return;

  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  messages.value.push({
    role: 'user',
    text: query,
    time: now
  });

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
  alert('SQL copied to clipboard');
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
</script>

<style scoped>
.chatbot-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: calc(100vh - 190px);
  min-height: 580px;
}

.chat-model-banner {
  padding: 14px 20px;
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

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
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
  max-width: 90%;
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

.chat-input-bar {
  padding: 14px 18px;
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
</style>
