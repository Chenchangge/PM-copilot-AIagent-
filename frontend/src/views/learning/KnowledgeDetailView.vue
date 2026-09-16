<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import PageHeader from '@/components/layout/PageHeader.vue'
import PrimaryButton from '@/components/ui/PrimaryButton.vue'
import SectionTitle from '@/components/ui/SectionTitle.vue'
import { knowledgeDetails, knowledgeList } from '@/mock'

const route = useRoute()
const router = useRouter()

const id = computed(() => Number(route.params.id))
const item = computed(() => knowledgeList.find((k) => k.id === id.value))
const detail = computed(() => knowledgeDetails[id.value])
</script>

<template>
  <div>
    <PageHeader :title="item?.title || '知识详情'" />
    <article v-if="item && detail" class="px-5 py-6">
      <p class="text-xs font-medium text-brand-600">{{ item.category }}</p>
      <h1 class="mt-1 text-xl font-bold leading-snug text-gray-900">{{ item.title }}</h1>

      <section class="mt-6">
        <SectionTitle title="知识定义" />
        <p class="mt-2 text-sm leading-relaxed text-gray-600">{{ detail.definition }}</p>
      </section>

      <section class="mt-8">
        <SectionTitle title="核心内容" />
        <ul class="mt-2 space-y-1.5 text-sm text-gray-600">
          <li v-for="c in detail.coreContent" :key="c">· {{ c }}</li>
        </ul>
      </section>

      <section class="mt-8">
        <SectionTitle title="产品经理需要关注什么" />
        <ul class="mt-2 space-y-1.5 text-sm text-gray-600">
          <li v-for="c in detail.pmFocus" :key="c">· {{ c }}</li>
        </ul>
      </section>

      <section class="mt-8">
        <SectionTitle title="常见面试问题" />
        <ul class="mt-2 space-y-1.5 text-sm text-gray-600">
          <li v-for="q in detail.interviewQuestions" :key="q">· {{ q }}</li>
        </ul>
      </section>

      <section class="mt-8">
        <SectionTitle title="参考回答" />
        <ul class="mt-2 space-y-1.5 text-sm text-gray-600">
          <li v-for="a in detail.referenceAnswers" :key="a">· {{ a }}</li>
        </ul>
      </section>

      <div class="mt-8">
        <PrimaryButton @click="router.push('/learning/qa')">用 AI 问问这个知识</PrimaryButton>
      </div>
    </article>
  </div>
</template>
