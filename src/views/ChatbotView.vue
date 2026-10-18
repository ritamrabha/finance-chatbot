<template>
  <div class="chatbot-view">
    <!-- Top Model Banner -->
    <div class="chat-model-banner glass-panel">
      <div class="banner-left">
        <div class="ai-avatar">
          <span>⚡</span>
        </div>
        <div>
          <h2 class="banner-title">Groq AI Finance Intelligence</h2>
          <p class="banner-desc">Natural language to safe SQL query engine · Executed in isolated SQLite WASM</p>
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
        <div class="welcome-icon">💬</div>
        <h3 class="welcome-title">Ask anything about your invoices & expenditure</h3>
        <p class="welcome-desc">
          Groq AI translates your question into a read-only SQL query, runs it securely on your ledger, and summarizes the financial insights with interactive charts.
        </p>

        <div class="suggestions-header">Try these example prompts:</div>
        <div class="suggestions-grid">
          <button
            v-for="s in promptSuggestions"
            :key="s"
            class="suggestion-btn"
            @click="sendSuggested(s)"
          >
            <span>👉 {{ s }}</span>
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
              <span v-if="msg.executionTime" class="meta-item">⏱️ {{ msg.executionTime }}ms</span>
              <span v-if="msg.usage?.total_tokens" class="meta-item">🔤 {{ msg.usage.total_tokens }} tokens</span>
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
                <span class="badge badge-clean">✓ SQL Guard Passed</span>
                <span class="text-dim text-xs">Read-Only SELECT</span>
              </div>
              <button class="btn btn-secondary btn-xs" @click="copyToClipboard(msg.sql)">
                <span>📋 Copy SQL</span>
              </button>
            </div>
            <pre class="sql-code"><code>{{ msg.sql }}</code></pre>
          </div>

          <!-- Dynamic Chart if applicable -->
          <div v-if="msg.chart && msg.chart.type !== 'none' && msg.chartData?.length > 1" class="chart-box">
            <div class="chart-header">
              <span class="chart-title">📊 Visual Summary ({{ msg.chart.type }} chart)</span>
              <span class="chart-axes text-dim text-xs">x: {{ msg.chart.x }} · y: {{ msg.chart.y }}</span>
            </div>
            <div class="chart-bars">
              <div v-for="(item, cIdx) in msg.chartData" :key="cIdx" class="chart-bar-item">
                <div class="bar-label" :title="String(item.label)">{{ String(item.label).slice(0, 16) }}</div>
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
                      <span :class="isNumeric(row[col]) ? 'money-val font-semibold' : ''">
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
          <span>Groq LPU™ is analyzing schema and generating safe SQL query...</span>
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
          <span v-if="!isLoading">Send Query →</span>
          <span v-else>Thinking...</span>
        </button>
      </form>
      <div class="input-hints">
        <span>💡 Enter key sends · Strictly read-only queries</span>
        <span class="text-dim">Dialect: SQLite · Today: 2026-10-18</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue';
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
    text: 'Hello! I am your AI Finance Assistant powered by Groq. Ask me any question about your invoices, vendors, tax, or duplicate flags. I will generate validated SQL, query the ledger, and provide you with instant figures and charts.',
    time: 'Just now',
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

watch(() => props.prefilledQuery, (newVal) => {
  if (newVal) {
    inputQuery.value = newVal;
    handleSubmit();
    emit('clear-prefilled');
  }
});

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
    const history = messages.value
      .filter(m => m.role === 'user' || m.sql)
      .map(m => ({ question: m.text, sql: m.sql }));

    const res = await askFinanceAssistant(query, history, props.activeModel);

    // Compute chart data if available
    let chartData = [];
    if (res.chart && res.chart.type !== 'none' && res.rows?.length > 0) {
      const xKey = res.chart.x;
      const yKey = res.chart.y;
      const maxVal = Math.max(...res.rows.map(r => Number(r[yKey]) || 0), 1);
      chartData = res.rows.slice(0, 8).map(r => ({
        label: r[xKey] ?? 'Unknown',
        val: Number(r[yKey]) || 0,
        percent: Math.min(100, Math.round(((Number(r[yKey]) || 0) / maxVal) * 100))
      }));
    }

    messages.value.push({
      role: 'assistant',
      text: res.text,
      sql: res.sql,
      rows: res.rows,
      columns: res.columns,
      chart: res.chart,
      chartData,
      executionTime: res.executionTime,
      usage: res.usage,
      model: res.model
    });
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      text: `Sorry, an error occurred while processing your query with Groq: ${err.message}`,
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
  alert('SQL copied to clipboard!');
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
  height: calc(100vh - 200px);
  min-height: 600px;
}

.chat-model-banner {
  padding: 16px 20px;
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
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.2), rgba(14, 165, 233, 0.2));
  border: 1px solid rgba(249, 115, 22, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

.banner-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #FFFFFF;
}

.banner-desc {
  font-size: 0.78rem;
  color: var(--text-dim);
}

.banner-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  font-size: 0.8rem;
}

.model-name {
  font-weight: 600;
  color: #F8FAFC;
}

.model-speed {
  color: #38BDF8;
  font-size: 0.75rem;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.welcome-box {
  margin: auto;
  max-width: 680px;
  text-align: center;
  padding: 30px;
}

.welcome-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
}

.welcome-title {
  font-size: 1.4rem;
  font-weight: 700;
  color: #FFFFFF;
  margin-bottom: 8px;
}

.welcome-desc {
  font-size: 0.9rem;
  color: var(--text-muted);
  line-height: 1.6;
  margin-bottom: 24px;
}

.suggestions-header {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}

.suggestions-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.suggestion-btn {
  padding: 11px 16px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-subtle);
  color: #E2E8F0;
  text-align: left;
  font-size: 0.88rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.suggestion-btn:hover {
  background: rgba(14, 165, 233, 0.1);
  border-color: rgba(14, 165, 233, 0.4);
  color: #38BDF8;
  transform: translateX(3px);
}

.message-row {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.user-bubble {
  align-self: flex-end;
  max-width: 75%;
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.25) 0%, rgba(2, 132, 199, 0.2) 100%);
  border: 1px solid rgba(14, 165, 233, 0.4);
  border-radius: 18px 18px 4px 18px;
  padding: 14px 18px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
}

.assistant-bubble {
  align-self: flex-start;
  max-width: 90%;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid var(--border-subtle);
  border-radius: 18px 18px 18px 4px;
  padding: 18px 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
}

.bubble-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  margin-bottom: 4px;
}

.bubble-sender {
  font-weight: 700;
  color: #38BDF8;
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
  font-weight: 700;
  color: #F97316;
}

.bubble-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.72rem;
  color: var(--text-dim);
}

.bubble-text {
  font-size: 0.95rem;
  color: #FFFFFF;
}

.assistant-text {
  font-size: 0.95rem;
  color: #F1F5F9;
  line-height: 1.6;
}

.sql-box {
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-md);
  padding: 12px 16px;
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

.text-xs {
  font-size: 0.75rem;
}

.sql-code {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  color: #38BDF8;
  overflow-x: auto;
  white-space: pre-wrap;
}

.chart-box {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: #FFFFFF;
}

.chart-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chart-bar-item {
  display: grid;
  grid-template-columns: 140px 1fr 100px;
  align-items: center;
  gap: 12px;
  font-size: 0.82rem;
}

.bar-label {
  font-weight: 500;
  color: #CBD5E1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bar-outer {
  height: 8px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  overflow: hidden;
}

.bar-inner {
  height: 100%;
  background: linear-gradient(90deg, #0EA5E9, #10B981);
  border-radius: 4px;
  transition: width 0.5s ease-out;
}

.bar-val {
  text-align: right;
  color: #38BDF8;
  font-size: 0.8rem;
}

.results-table-box {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.table-header {
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid var(--border-subtle);
}

.table-title {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.table-scroll {
  overflow-x: auto;
  max-height: 240px;
}

.table-more-hint {
  padding: 8px 14px;
  font-size: 0.75rem;
  color: var(--text-dim);
  text-align: center;
  background: rgba(255, 255, 255, 0.01);
}

.loading-bubble {
  border-color: rgba(249, 115, 22, 0.35);
  background: rgba(249, 115, 22, 0.05);
}

.loading-content {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.88rem;
  color: #FB923C;
  font-weight: 500;
}

.chat-input-bar {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.input-form {
  display: flex;
  gap: 12px;
}

.chat-input {
  flex: 1;
  padding: 14px 18px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  color: #FFFFFF;
  font-family: var(--font-sans);
  font-size: 0.95rem;
  outline: none;
  transition: all 0.2s;
}

.chat-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 16px var(--primary-glow);
}

.send-btn {
  padding: 0 24px;
}

.input-hints {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  color: var(--text-dim);
}
</style>
