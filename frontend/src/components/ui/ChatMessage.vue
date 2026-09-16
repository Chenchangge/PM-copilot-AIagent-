<script setup>
defineProps({
  role: { type: String, default: 'ai' }, // 'ai' | 'user'
  references: { type: Array, default: () => [] },
})
</script>

<template>
  <div class="flex" :class="role === 'user' ? 'justify-end' : 'justify-start'">
    <div
      class="max-w-[85%] px-4 py-2.5 text-sm leading-relaxed"
      :class="role === 'user' ? 'rounded-2xl rounded-br-md bg-brand-600 text-white' : 'card rounded-bl-md'"
    >
      <slot />
      <div v-if="role === 'ai' && references.length" class="mt-2 border-t border-gray-100 pt-2">
        <p class="text-xs text-gray-400">参考知识</p>
        <div class="mt-1 flex flex-wrap gap-1.5">
          <span v-for="r in references" :key="r" class="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs text-brand-600">{{ r }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
