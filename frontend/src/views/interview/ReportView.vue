<script setup>
import { useRouter } from 'vue-router'

import PageHeader from '@/components/layout/PageHeader.vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { mockReport } from '@/mock'

const router = useRouter()
</script>

<template>
  <div>
    <PageHeader title="面试报告" />
    <div class="px-5 py-6">
      <section class="text-center">
        <p class="text-sm font-semibold text-gray-900">面试完成</p>
        <p class="mt-1 text-xs text-gray-400">{{ mockReport.meta.direction }} · {{ mockReport.meta.difficulty }}</p>
        <p class="mt-6 text-5xl font-bold text-brand-600">
          {{ mockReport.overall }}<span class="text-lg font-normal text-gray-400"> / 100</span>
        </p>
        <p class="mt-1 text-sm text-gray-500">综合表现</p>
      </section>

      <section class="mt-8">
        <SectionTitle title="能力维度" />
        <div class="mt-3 space-y-3">
          <div v-for="d in mockReport.dimensions" :key="d.name">
            <div class="flex justify-between text-sm">
              <span class="text-gray-600">{{ d.name }}</span>
              <span class="font-medium text-gray-900">{{ d.score }}</span>
            </div>
            <ProgressBar :value="d.score" size="sm" class="mt-1.5" />
          </div>
        </div>
      </section>

      <section class="mt-8">
        <SectionTitle title="表现较好" />
        <ul class="mt-2 space-y-2 text-sm text-gray-600">
          <li v-for="s in mockReport.strengths" :key="s" class="flex items-center gap-2">
            <svg class="h-4 w-4 shrink-0 text-green-500" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
            {{ s }}
          </li>
        </ul>
      </section>

      <section class="mt-8">
        <SectionTitle title="需要提升" />
        <ul class="mt-2 space-y-2 text-sm text-gray-600">
          <li v-for="w in mockReport.weakPoints" :key="w" class="flex items-center gap-2">
            <svg class="h-4 w-4 shrink-0 text-amber-500" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 2.874 1.448 2.874h15.71c1.23 0 2.314-1.374 1.448-2.874L13.448 3.376a1.5 1.5 0 00-2.896 0L2.697 16.126zM12 15.75h.008v.008H12v-.008z" />
            </svg>
            {{ w }}
          </li>
        </ul>
      </section>

      <section class="mt-8">
        <SectionTitle title="推荐学习" />
        <div class="mt-3 space-y-2">
          <RouterLink
            v-for="k in mockReport.recommendedKnowledge"
            :key="k.id"
            :to="`/learning/knowledge/${k.id}`"
            class="card flex items-center justify-between p-4 transition-colors hover:border-gray-200"
          >
            <span class="text-sm font-medium text-gray-900">{{ k.title }}</span>
            <svg class="h-4 w-4 text-gray-300" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </RouterLink>
        </div>
      </section>

      <div class="mt-8">
        <PrimaryButton @click="router.push('/interview/setup')">再来一次面试</PrimaryButton>
      </div>
    </div>
  </div>
</template>
