<template>
  <nav class="mobile-dock-wrapper" aria-label="Mobile Navigation Dock">
    <div class="dock-pill">
      <button
        v-for="item in dockItems"
        :key="item.id"
        class="dock-item"
        :class="{ active: currentTab === item.id }"
        @click="$emit('select-tab', item.id)"
        :aria-label="item.label"
        :title="item.label"
      >
        <div class="icon-tile">
          <HugeiconsIcon
            :icon="item.icon"
            :size="22"
            :stroke-width="1.8"
            :color="currentTab === item.id ? '#FFFFFF' : '#71717A'"
          />
          <!-- Active Pill Indicator (matching user screenshot) -->
          <span v-if="currentTab === item.id" class="active-indicator"></span>
        </div>
        <span class="dock-label">{{ item.label }}</span>
      </button>
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
  User02Icon
} from '@hugeicons/core-free-icons';

defineProps({
  currentTab: {
    type: String,
    default: 'dashboard'
  }
});

defineEmits(['select-tab']);

const dockItems = computed(() => [
  {
    id: 'dashboard',
    label: 'Home',
    icon: Home01Icon
  },
  {
    id: 'calculator',
    label: 'Loan Calculator',
    icon: Calculator01Icon
  },
  {
    id: 'chat',
    label: 'AI Chat Assistant',
    icon: AiChat02Icon
  },
  {
    id: 'profile',
    label: 'Profile',
    icon: User02Icon
  }
]);
</script>

<style scoped>
.mobile-dock-wrapper {
  position: fixed;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 999;
  pointer-events: none;
  width: max-content;
  max-width: calc(100vw - 32px);
  animation: floatUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes floatUp {
  from {
    opacity: 0;
    transform: translate(-50%, 15px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

/* Floating dark pill container matching user reference screenshot */
.dock-pill {
  pointer-events: auto;
  display: flex;
  align-items: center;
  background: rgba(13, 15, 18, 0.94);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 9999px;
  padding: 6px 8px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.8), 0 0 1px rgba(255, 255, 255, 0.18);
  gap: 6px;
}

.dock-item {
  background: transparent;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  position: relative;
  outline: none;
  transition: transform 0.15s ease;
}

.dock-item:active {
  transform: scale(0.94);
}

/* Rounded tile container for active state */
.icon-tile {
  width: 52px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  position: relative;
  transition: background-color 0.2s ease, color 0.2s ease;
}

.dock-item.active .icon-tile {
  background: #1E232E;
}

.dock-item:not(.active):hover .icon-tile {
  background: rgba(255, 255, 255, 0.05);
}

/* Mint / Cyan Active Indicator bar at the bottom of active tile */
.active-indicator {
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 20px;
  height: 3px;
  background: #2DD4BF;
  border-radius: 9999px;
  box-shadow: 0 0 8px rgba(45, 212, 191, 0.7);
  animation: pulsePill 2s infinite ease-in-out;
}

@keyframes pulsePill {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.75; }
}

.dock-label {
  display: none; /* Icon-focused sleek dock as shown in user screenshot */
}

/* Extra media queries to ensure comfortable bottom padding */
@media (min-width: 1024px) {
  /* On wide desktop screens, dock remains visible as an alternative floating quick-switcher or can sit smoothly */
  .mobile-dock-wrapper {
    bottom: 22px;
  }
}
</style>
