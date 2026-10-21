<script setup>
import { useRouter } from 'vue-router'

import PageHeader from '@/components/layout/PageHeader.vue'

const router = useRouter()
</script>

<template>
  <div>
    <PageHeader title="页面不存在" />
    <div class="px-6 py-24 text-center">
      <p class="text-5xl font-bold text-brand-600">404</p>
      <p class="mt-3 text-sm text-gray-500">你访问的页面不存在，或者链接已经失效。</p>
      <div class="mt-6 flex flex-col gap-2">
        <button
          type="button"
          class="rounded-2xl bg-brand-600 px-5 py-3 text-sm font-medium text-white"
          @click="router.push('/home')"
        >
          回到首页
        </button>
        <button
          type="button"
          class="rounded-2xl border border-gray-200 bg-white px-5 py-3 text-sm text-gray-600"
          @click="router.back()"
        >
          返回上一页
        </button>
      </div>
    </div>
  </div>
</template>
