<script setup>
defineProps({
  disabled: { type: Boolean, default: false },
  full: { type: Boolean, default: true },
})
defineEmits(['click'])
</script>

<template>
  <button
    type="button"
    :disabled="disabled"
    class="inline-flex items-center justify-center rounded-2xl bg-brand-600 px-5 py-3.5 text-sm font-medium text-white transition-colors hover:bg-brand-700 active:bg-brand-700 disabled:cursor-not-allowed disabled:bg-gray-200 disabled:text-gray-400"
    :class="full ? 'w-full' : ''"
    @click="$emit('click')"
  >
    <slot />
  </button>
</template>
