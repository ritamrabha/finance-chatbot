<template>
  <div class="groq-studio-view">
    <!-- Header -->
    <div class="studio-header glass-panel">
      <div class="header-left">
        <div class="studio-logo">
          <span>⚡</span>
        </div>
        <div>
          <h2 class="studio-title">Groq Cloud AI Model Studio</h2>
          <p class="studio-desc">
            Ultra-low latency inference powered by Groq's Tensor Streaming Processor (TSP / LPU™) architecture.
          </p>
        </div>
      </div>

      <!-- Active Model Tag -->
      <div class="active-model-tag">
        <span class="pulse-dot"></span>
        <span>Active Model: <strong>{{ activeModel }}</strong></span>
      </div>
    </div>

    <!-- API Key Configuration Box -->
    <div class="key-box glass-panel">
      <div class="key-header">
        <h3 class="box-title">GroqCloud API Key Configuration</h3>
        <span class="badge badge-clean">Active from .env</span>
      </div>
      <p class="box-desc">
        Your key is loaded from <span class="code-tag">.env</span> (<code>groq_api_key</code> / <code>VITE_GROQ_API_KEY</code>). You can also provide a custom key below:
      </p>

      <div class="key-input-row">
        <input
          v-model="apiKeyInput"
          :type="showKey ? 'text' : 'password'"
          placeholder="gsk_..."
          class="key-input"
        />
        <button class="btn btn-secondary btn-sm" @click="showKey = !showKey">
          {{ showKey ? 'Hide' : 'Show' }}
        </button>
        <button class="btn btn-primary btn-sm" @click="saveKey">
          Save Key
        </button>
        <button class="btn btn-secondary btn-sm" @click="testKey" :disabled="testingKey">
          {{ testingKey ? 'Testing...' : 'Test Connection' }}
        </button>
      </div>

      <div v-if="testResult" class="test-result-box" :class="testResult.success ? 'test-success' : 'test-fail'">
        <span>{{ testResult.success ? '✓ ' + testResult.message : '✕ ' + testResult.message }}</span>
      </div>
    </div>

    <!-- Models Grid (From Groq Docs provided by user) -->
    <div class="models-section">
      <div class="section-header">
        <h3 class="section-title">Supported Production & Flagship Models</h3>
        <p class="section-desc">Click any model below to activate it for the SQL Chatbot</p>
      </div>

      <div class="models-grid">
        <div
          v-for="model in availableModels"
          :key="model.id"
          class="model-card glass-panel"
          :class="{ 'card-active': activeModel === model.id }"
        >
          <div class="card-top">
            <div class="model-meta">
              <span class="model-id code-tag">{{ model.id }}</span>
              <span class="badge" :class="model.id.includes('120b') ? 'badge-clean' : 'badge-currency'">
                {{ model.badge }}
              </span>
            </div>
            <h4 class="model-title">{{ model.name }}</h4>
          </div>

          <p class="model-desc">{{ model.description }}</p>

          <div class="specs-grid">
            <div class="spec-item">
              <span class="spec-label">Speed:</span>
              <span class="spec-val money-val text-cyan">{{ model.speed }}</span>
            </div>
            <div class="spec-item">
              <span class="spec-label">Context:</span>
              <span class="spec-val">{{ model.context }}</span>
            </div>
          </div>

          <button
            class="btn btn-sm w-full"
            :class="activeModel === model.id ? 'btn-emerald' : 'btn-secondary'"
            @click="$emit('update:activeModel', model.id)"
          >
            {{ activeModel === model.id ? '✓ Currently Active' : 'Activate Model' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Playground Test Box -->
    <div class="playground-box glass-panel">
      <div class="panel-header">
        <div>
          <h3 class="panel-title">⚡ Live Inference Benchmark</h3>
          <p class="panel-desc">Test raw completion speed with the currently selected Groq model</p>
        </div>
      </div>

      <div class="playground-input-row">
        <input
          v-model="benchmarkPrompt"
          type="text"
          placeholder="Enter a prompt to benchmark (e.g. 'Explain 3 key metrics for auditing duplicate invoices')"
          class="bench-input"
        />
        <button class="btn btn-primary" :disabled="benchmarking || !benchmarkPrompt" @click="runBenchmark">
          {{ benchmarking ? 'Inferring...' : 'Run Benchmark →' }}
        </button>
      </div>

      <div v-if="benchmarkOutput" class="benchmark-results">
        <div class="benchmark-stats">
          <span class="stat-pill">Model: <strong>{{ activeModel }}</strong></span>
          <span class="stat-pill">Latency: <strong class="text-cyan">{{ benchStats.timeMs }}ms</strong></span>
          <span class="stat-pill">Tokens: <strong>{{ benchStats.tokens }}</strong></span>
          <span class="stat-pill">Rate: <strong class="text-emerald">{{ benchStats.tps }} tokens/sec</strong></span>
        </div>
        <div class="benchmark-text">
          {{ benchmarkOutput }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { GROQ_MODELS, getGroqApiKey, setGroqApiKey } from '../services/groq.js';

const props = defineProps({
  activeModel: {
    type: String,
    default: 'openai/gpt-oss-120b'
  }
});

defineEmits(['update:activeModel']);

const availableModels = ref(GROQ_MODELS);
const apiKeyInput = ref(getGroqApiKey());
const showKey = ref(false);
const testingKey = ref(false);
const testResult = ref(null);

const benchmarkPrompt = ref('Summarize why fuzzy duplicate detection with RapidFuzz is critical for enterprise accounting');
const benchmarking = ref(false);
const benchmarkOutput = ref('');
const benchStats = ref({});

function saveKey() {
  setGroqApiKey(apiKeyInput.value);
  alert('API Key updated successfully in session storage.');
}

async function testKey() {
  testingKey.value = true;
  testResult.value = null;

  try {
    const key = apiKeyInput.value.trim();
    const res = await fetch('/api/groq/models', {
      headers: { Authorization: `Bearer ${key}` }
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    const data = await res.json();
    testResult.value = {
      success: true,
      message: `Connected successfully! Found ${data.data?.length || 0} active models on GroqCloud.`
    };
  } catch (err) {
    testResult.value = {
      success: false,
      message: `Connection failed: ${err.message}`
    };
  } finally {
    testingKey.value = false;
  }
}

async function runBenchmark() {
  benchmarking.value = true;
  benchmarkOutput.value = '';
  const startTime = performance.now();

  try {
    const key = getGroqApiKey();
    const res = await fetch('/api/groq/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${key}`
      },
      body: JSON.stringify({
        model: props.activeModel,
        messages: [{ role: 'user', content: benchmarkPrompt.value }],
        max_tokens: 250
      })
    });

    const data = await res.json();
    const elapsed = Math.round(performance.now() - startTime);

    if (data.error) throw new Error(data.error.message);

    const completion = data.choices[0]?.message?.content || '';
    const completionTokens = data.usage?.completion_tokens || 1;
    const tps = Math.round((completionTokens / (elapsed / 1000)));

    benchStats.value = {
      timeMs: elapsed,
      tokens: data.usage?.total_tokens || 0,
      tps: tps
    };
    benchmarkOutput.value = completion;
  } catch (err) {
    benchmarkOutput.value = `Error running benchmark: ${err.message}`;
  } finally {
    benchmarking.value = false;
  }
}
</script>

<style scoped>
.groq-studio-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.studio-header {
  padding: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.studio-logo {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(249, 115, 22, 0.15);
  border: 1px solid rgba(249, 115, 22, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.studio-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #FFFFFF;
}

.studio-desc {
  font-size: 0.82rem;
  color: var(--text-dim);
}

.active-model-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: var(--radius-full);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  font-size: 0.85rem;
  color: #E2E8F0;
}

.key-box {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.key-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.box-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #FFFFFF;
}

.box-desc {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.key-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.key-input {
  flex: 1;
  min-width: 300px;
  padding: 10px 14px;
  border-radius: var(--radius-md);
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border-subtle);
  color: #38BDF8;
  font-family: var(--font-mono);
  font-size: 0.88rem;
  outline: none;
}

.key-input:focus {
  border-color: var(--primary);
}

.test-result-box {
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
}

.test-success {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #34D399;
}

.test-fail {
  background: rgba(244, 63, 94, 0.1);
  border: 1px solid rgba(244, 63, 94, 0.3);
  color: #FDA4AF;
}

.models-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: #FFFFFF;
}

.section-desc {
  font-size: 0.8rem;
  color: var(--text-dim);
}

.models-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 18px;
}

.model-card {
  padding: 22px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 16px;
  transition: all 0.2s;
}

.model-card.card-active {
  border-color: rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.04);
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
}

.model-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.model-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #FFFFFF;
}

.model-desc {
  font-size: 0.82rem;
  color: var(--text-muted);
  line-height: 1.5;
}

.specs-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  font-size: 0.8rem;
}

.spec-label {
  color: var(--text-dim);
}

.w-full {
  width: 100%;
}

.playground-box {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.playground-input-row {
  display: flex;
  gap: 12px;
}

.bench-input {
  flex: 1;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border-subtle);
  color: #FFFFFF;
  font-family: var(--font-sans);
  font-size: 0.9rem;
  outline: none;
}

.bench-input:focus {
  border-color: var(--primary);
}

.benchmark-results {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.benchmark-stats {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.stat-pill {
  font-size: 0.78rem;
  color: var(--text-dim);
}

.benchmark-text {
  font-size: 0.9rem;
  color: #F1F5F9;
  line-height: 1.6;
}
</style>
