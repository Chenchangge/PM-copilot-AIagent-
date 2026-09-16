<script setup>
defineProps({
  title: { type: String, required: true },
})
</script>

<template>
  <div class="flex items-center justify-between">
    <h2 class="text-sm font-semibold text-gray-900">{{ title }}</h2>
    <slot name="right" />
  </div>
</template>
