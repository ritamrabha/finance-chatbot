<template>
  <div class="loan-calc-container">
    <!-- Header -->
    <div class="calc-header glass-panel">
      <div class="header-left">
        <div class="icon-box">
          <HugeiconsIcon :icon="Calculator01Icon" :size="24" :stroke-width="1.8" color="#FFFFFF" />
        </div>
        <div>
          <div class="title-row">
            <h2 class="title">Loan & EMI Calculator</h2>
            <span class="badge">Financial Planning</span>
          </div>
          <p class="subtitle">Compute monthly installments, interest burden, and amortization schedules with zero clutter.</p>
        </div>
      </div>

      <!-- Quick Preset Selector -->
      <div class="presets-group">
        <button
          v-for="preset in presets"
          :key="preset.id"
          class="preset-btn"
          :class="{ active: selectedPreset === preset.id }"
          @click="applyPreset(preset)"
        >
          {{ preset.name }}
        </button>
      </div>
    </div>

    <!-- Main Grid: Controls Left, Summary Right -->
    <div class="calc-grid">
      <!-- Input Controls Card -->
      <div class="controls-card glass-panel">
        <h3 class="card-title">Loan Parameters</h3>

        <!-- Principal Amount -->
        <div class="form-group">
          <div class="label-row">
            <label class="label">Principal Loan Amount</label>
            <div class="input-display">
              <span class="currency-prefix">₹</span>
              <input
                type="number"
                v-model.number="principal"
                min="10000"
                max="100000000"
                step="10000"
                class="num-input"
              />
            </div>
          </div>
          <input
            type="range"
            v-model.number="principal"
            min="50000"
            max="10000000"
            step="25000"
            class="range-slider"
          />
          <div class="quick-amounts">
            <button
              v-for="amt in [500000, 1000000, 2500000, 5000000]"
              :key="amt"
              class="chip-btn"
              :class="{ selected: principal === amt }"
              @click="principal = amt"
            >
              {{ formatInrShort(amt) }}
            </button>
          </div>
        </div>

        <!-- Interest Rate -->
        <div class="form-group">
          <div class="label-row">
            <label class="label">Annual Interest Rate (% p.a.)</label>
            <div class="input-display">
              <input
                type="number"
                v-model.number="rate"
                min="1"
                max="30"
                step="0.1"
                class="num-input text-right"
              />
              <span class="currency-suffix">%</span>
            </div>
          </div>
          <input
            type="range"
            v-model.number="rate"
            min="4"
            max="24"
            step="0.25"
            class="range-slider"
          />
          <div class="slider-ticks">
            <span>4%</span>
            <span>10%</span>
            <span>16%</span>
            <span>24%</span>
          </div>
        </div>

        <!-- Loan Tenure -->
        <div class="form-group">
          <div class="label-row">
            <label class="label">Loan Tenure</label>
            <div class="tenure-unit-toggle">
              <button
                class="unit-btn"
                :class="{ active: tenureUnit === 'years' }"
                @click="tenureUnit = 'years'"
              >
                Years
              </button>
              <button
                class="unit-btn"
                :class="{ active: tenureUnit === 'months' }"
                @click="tenureUnit = 'months'"
              >
                Months
              </button>
            </div>
          </div>
          <div class="input-display w-full-input">
            <input
              type="number"
              v-model.number="tenureValue"
              :min="1"
              :max="tenureUnit === 'years' ? 30 : 360"
              class="num-input"
            />
            <span class="currency-suffix">{{ tenureUnit === 'years' ? 'Years' : 'Months' }}</span>
          </div>
          <input
            type="range"
            v-model.number="tenureValue"
            :min="1"
            :max="tenureUnit === 'years' ? 30 : 360"
            step="1"
            class="range-slider"
          />
        </div>
      </div>

      <!-- Result Summary Card -->
      <div class="results-card glass-panel">
        <h3 class="card-title">Repayment Summary</h3>

        <!-- Primary Output: Monthly EMI -->
        <div class="emi-highlight">
          <span class="emi-label">Monthly EMI Payment</span>
          <div class="emi-amount">₹{{ formatInr(emi) }}</div>
          <span class="emi-sub">Estimated monthly installment</span>
        </div>

        <!-- Metric Details -->
        <div class="metrics-grid">
          <div class="metric-row">
            <span class="m-label">Principal Amount</span>
            <span class="m-val">₹{{ formatInr(principal) }}</span>
          </div>
          <div class="metric-row">
            <span class="m-label">Total Interest Payable</span>
            <span class="m-val">₹{{ formatInr(totalInterest) }}</span>
          </div>
          <div class="metric-row total-row">
            <span class="m-label">Total Repayment Amount</span>
            <span class="m-val">₹{{ formatInr(totalPayment) }}</span>
          </div>
        </div>

        <!-- Ratio Bar (Principal vs Interest) -->
        <div class="ratio-section">
          <div class="ratio-labels">
            <span>Principal: {{ principalPercent }}%</span>
            <span>Interest: {{ interestPercent }}%</span>
          </div>
          <div class="ratio-bar">
            <div class="bar-principal" :style="{ width: principalPercent + '%' }"></div>
            <div class="bar-interest" :style="{ width: interestPercent + '%' }"></div>
          </div>
        </div>

        <!-- Consult AI Action -->
        <div class="ai-consult-box">
          <button class="btn btn-primary w-full" @click="consultAiAssistant">
            <HugeiconsIcon :icon="AiChat02Icon" :size="18" :stroke-width="1.8" color="#000000" />
            <span>Consult Groq AI on this Loan</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Amortization Schedule Table -->
    <div class="schedule-section glass-panel">
      <div class="schedule-header">
        <div>
          <h3 class="card-title">Annual Amortization Breakdown</h3>
          <p class="subtitle">Year-by-year principal reduction and interest amortized over the tenure.</p>
        </div>
        <button class="btn btn-secondary btn-sm" @click="showAllYears = !showAllYears">
          {{ showAllYears ? 'Show Fewer Years' : 'View Full Schedule' }}
        </button>
      </div>

      <div class="table-container">
        <table class="schedule-table">
          <thead>
            <tr>
              <th>Year</th>
              <th>Opening Balance</th>
              <th>Principal Paid</th>
              <th>Interest Paid</th>
              <th>Total Payment</th>
              <th>Closing Balance</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in displayedSchedule" :key="row.year">
              <td class="font-semibold text-white">Year {{ row.year }}</td>
              <td class="font-mono">₹{{ formatInr(row.openingBalance) }}</td>
              <td class="font-mono">₹{{ formatInr(row.principalPaid) }}</td>
              <td class="font-mono">₹{{ formatInr(row.interestPaid) }}</td>
              <td class="font-mono">₹{{ formatInr(row.totalPaid) }}</td>
              <td class="font-mono">₹{{ formatInr(row.closingBalance) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { HugeiconsIcon } from '@hugeicons/vue';
import {
  Calculator01Icon,
  AiChat02Icon
} from '@hugeicons/core-free-icons';

const emit = defineEmits(['ask-query']);

// Presets
const presets = [
  { id: 'home', name: 'Home Loan', principal: 4000000, rate: 8.5, tenure: 20, unit: 'years' },
  { id: 'business', name: 'Business Loan', principal: 1500000, rate: 10.5, tenure: 3, unit: 'years' },
  { id: 'personal', name: 'Personal Loan', principal: 500000, rate: 12.0, tenure: 3, unit: 'years' },
  { id: 'auto', name: 'Vehicle Loan', principal: 800000, rate: 9.0, tenure: 5, unit: 'years' }
];

const selectedPreset = ref('business');
const principal = ref(1500000);
const rate = ref(10.5);
const tenureValue = ref(3);
const tenureUnit = ref('years');
const showAllYears = ref(false);

function applyPreset(p) {
  selectedPreset.value = p.id;
  principal.value = p.principal;
  rate.value = p.rate;
  tenureValue.value = p.tenure;
  tenureUnit.value = p.unit;
}

// Tenure in months
const totalMonths = computed(() => {
  return tenureUnit.value === 'years' ? tenureValue.value * 12 : tenureValue.value;
});

// EMI Calculation
const emi = computed(() => {
  const p = principal.value || 0;
  const n = totalMonths.value || 1;
  const r = (rate.value || 0) / (12 * 100);

  if (p <= 0 || n <= 0) return 0;
  if (r === 0) return Math.round(p / n);

  const factor = Math.pow(1 + r, n);
  const monthly = (p * r * factor) / (factor - 1);
  return Math.round(monthly);
});

const totalPayment = computed(() => {
  return emi.value * totalMonths.value;
});

const totalInterest = computed(() => {
  const diff = totalPayment.value - principal.value;
  return diff > 0 ? diff : 0;
});

const principalPercent = computed(() => {
  if (totalPayment.value <= 0) return 100;
  return Math.round((principal.value / totalPayment.value) * 100);
});

const interestPercent = computed(() => {
  return 100 - principalPercent.value;
});

// Amortization Schedule
const annualSchedule = computed(() => {
  const schedule = [];
  let balance = principal.value;
  const monthlyRate = (rate.value || 0) / (12 * 100);
  const monthlyPayment = emi.value;
  const totalYears = Math.ceil(totalMonths.value / 12);

  for (let year = 1; year <= totalYears; year++) {
    const opening = balance;
    let yearPrincipal = 0;
    let yearInterest = 0;

    for (let m = 1; m <= 12; m++) {
      if (balance <= 0) break;
      const interestForMonth = balance * monthlyRate;
      let principalForMonth = monthlyPayment - interestForMonth;
      if (principalForMonth > balance) {
        principalForMonth = balance;
      }
      yearInterest += interestForMonth;
      yearPrincipal += principalForMonth;
      balance -= principalForMonth;
    }

    schedule.push({
      year,
      openingBalance: Math.round(opening),
      principalPaid: Math.round(yearPrincipal),
      interestPaid: Math.round(yearInterest),
      totalPaid: Math.round(yearPrincipal + yearInterest),
      closingBalance: Math.max(0, Math.round(balance))
    });

    if (balance <= 0) break;
  }

  return schedule;
});

const displayedSchedule = computed(() => {
  if (showAllYears.value) return annualSchedule.value;
  return annualSchedule.value.slice(0, 5);
});

function formatInr(val) {
  if (!val && val !== 0) return '0';
  return Math.round(val).toLocaleString('en-IN');
}

function formatInrShort(val) {
  if (val >= 10000000) return `₹${(val / 10000000).toFixed(1)} Cr`;
  if (val >= 100000) return `₹${(val / 100000).toFixed(0)} Lakh`;
  return `₹${val.toLocaleString('en-IN')}`;
}

function consultAiAssistant() {
  const prompt = `Analyze this loan scenario: Principal amount ₹${formatInr(principal.value)} at ${rate.value}% annual interest rate for ${tenureValue.value} ${tenureUnit.value}. The calculated monthly EMI is ₹${formatInr(emi.value)} and total interest payable is ₹${formatInr(totalInterest.value)}. Is this viable against our recent company invoice cash flows?`;
  emit('ask-query', prompt);
}
</script>

<style scoped>
.loan-calc-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.calc-header {
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-box {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  background: #171717;
  border: 1px solid var(--border-bright);
  display: flex;
  align-items: center;
  justify-content: center;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #FFFFFF;
}

.subtitle {
  font-size: 0.85rem;
  color: var(--text-dim);
  margin-top: 2px;
}

.presets-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.preset-btn {
  background: #141414;
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  padding: 6px 14px;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s ease;
}

.preset-btn:hover {
  background: #1F1F1F;
  color: #FFFFFF;
}

.preset-btn.active {
  background: #FFFFFF;
  color: #000000;
  border-color: #FFFFFF;
  font-weight: 600;
}

.calc-grid {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 20px;
}

@media (max-width: 900px) {
  .calc-grid {
    grid-template-columns: 1fr;
  }
}

.controls-card, .results-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.card-title {
  font-size: 0.95rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #E4E4E7;
}

.input-display {
  display: flex;
  align-items: center;
  background: #141414;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 4px 10px;
  gap: 4px;
}

.w-full-input {
  width: 100%;
}

.currency-prefix, .currency-suffix {
  font-size: 0.85rem;
  color: var(--text-dim);
  font-family: var(--font-mono);
}

.num-input {
  background: transparent;
  border: none;
  outline: none;
  color: #FFFFFF;
  font-family: var(--font-mono);
  font-size: 0.95rem;
  font-weight: 600;
  width: 140px;
}

.num-input.text-right {
  text-align: right;
  width: 60px;
}

.range-slider {
  -webkit-appearance: none;
  width: 100%;
  height: 4px;
  border-radius: 2px;
  background: #27272A;
  outline: none;
}

.range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #FFFFFF;
  cursor: pointer;
  border: 2px solid #000000;
  box-shadow: 0 0 6px rgba(255, 255, 255, 0.4);
}

.quick-amounts {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.chip-btn {
  background: #121212;
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 0.75rem;
  padding: 4px 10px;
  border-radius: var(--radius-xs);
  cursor: pointer;
}

.chip-btn:hover {
  background: #1C1C1C;
  color: #FFFFFF;
}

.chip-btn.selected {
  border-color: #FFFFFF;
  color: #FFFFFF;
}

.slider-ticks {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
  color: var(--text-dim);
  font-family: var(--font-mono);
}

.tenure-unit-toggle {
  display: flex;
  background: #141414;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xs);
  padding: 2px;
}

.unit-btn {
  background: transparent;
  border: none;
  color: var(--text-dim);
  font-size: 0.75rem;
  padding: 3px 8px;
  border-radius: 4px;
  cursor: pointer;
}

.unit-btn.active {
  background: #27272A;
  color: #FFFFFF;
  font-weight: 500;
}

/* Results */
.emi-highlight {
  background: #141414;
  border: 1px solid var(--border-bright);
  border-radius: var(--radius-md);
  padding: 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.emi-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.emi-amount {
  font-size: 2.2rem;
  font-weight: 700;
  font-family: var(--font-mono);
  color: #FFFFFF;
  letter-spacing: -0.03em;
}

.emi-sub {
  font-size: 0.75rem;
  color: var(--text-dim);
}

.metrics-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-subtle);
}

.metric-row.total-row {
  border-bottom: none;
  padding-top: 4px;
}

.m-label {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.m-val {
  font-family: var(--font-mono);
  font-size: 0.95rem;
  font-weight: 600;
  color: #FFFFFF;
}

.total-row .m-val {
  font-size: 1.1rem;
}

/* Ratio Bar */
.ratio-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ratio-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.ratio-bar {
  height: 6px;
  border-radius: 9999px;
  background: #27272A;
  display: flex;
  overflow: hidden;
}

.bar-principal {
  background: #FFFFFF;
  transition: width 0.2s ease;
}

.bar-interest {
  background: #52525B;
  transition: width 0.2s ease;
}

.schedule-section {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.schedule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.table-container {
  overflow-x: auto;
}

.schedule-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.schedule-table th {
  text-align: left;
  padding: 10px 14px;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-dim);
  border-bottom: 1px solid var(--border-subtle);
}

.schedule-table td {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  color: var(--text-muted);
}

.schedule-table tr:hover td {
  background: rgba(255, 255, 255, 0.02);
}
</style>
