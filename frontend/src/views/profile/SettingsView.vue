<script setup>
import PageHeader from '@/components/layout/PageHeader.vue'

const settings = [
  { label: '外观', value: '浅色' },
  { label: '关于 PM Copilot', value: 'v0.1.0' },
]
</script>

<template>
  <div>
    <PageHeader title="设置" />
    <div class="px-5 py-4">
      <div class="overflow-hidden rounded-2xl border border-gray-100 bg-white">
        <div
          v-for="(s, i) in settings"
          :key="s.label"
          class="flex items-center justify-between px-4 py-3.5"
          :class="i > 0 ? 'border-t border-gray-50' : ''"
        >
          <span class="text-sm text-gray-900">{{ s.label }}</span>
          <span class="text-sm text-gray-400">{{ s.value }}</span>
        </div>
      </div>
      <p class="mt-4 text-xs text-gray-400">
        DeepSeek API Key 仅在后端环境变量中配置，前端不存储任何密钥。
      </p>
    </div>
  </div>
</template>
