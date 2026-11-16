<script setup>
defineProps({ disabled: Boolean, label: String });
defineEmits(['recent', 'all']);
</script>

<template>
  <div class="chart-tools">
    <div class="crossover-legend"><span class="positive">↑ Upward crossover</span><span class="negative">↓ Downward crossover</span><span>Signals, not fills</span></div>
    <div class="chart-view-buttons" role="group" :aria-label="label">
      <button type="button" :disabled="disabled" @click="$emit('recent')">Recent 60 candles</button>
      <button type="button" :disabled="disabled" @click="$emit('all')">Show all loaded</button>
    </div>
  </div>
</template>
