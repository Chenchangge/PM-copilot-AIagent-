<script setup>
import { computed } from 'vue'

import { CAPABILITY_LABELS, CAPABILITY_STATE_META } from '@/utils/models'

const props = defineProps({
  name: { type: String, required: true },
  state: { type: String, default: 'unknown' },
})

const meta = computed(() => CAPABILITY_STATE_META[props.state] || CAPABILITY_STATE_META.unknown)
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium"
    :class="[meta.border, meta.text]"
    :title="meta.label"
  >
    <span aria-hidden="true">{{ meta.icon }}</span>
    {{ CAPABILITY_LABELS[name] || name }}
  </span>
</template>
