<script setup>
defineProps({
  options: { type: Array, default: () => [] },
  modelValue: { type: String, default: '' },
})
defineEmits(['update:modelValue'])
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <button
      v-for="o in options"
      :key="o"
      type="button"
      class="rounded-full border px-4 py-2 text-sm transition-colors"
      :class="modelValue === o ? 'border-brand-600 bg-brand-600 text-white' : 'border-gray-200 bg-white text-gray-600 active:bg-gray-50'"
      @click="$emit('update:modelValue', o)"
    >
      {{ o }}
    </button>
  </div>
</template>
