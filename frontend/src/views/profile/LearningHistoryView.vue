<script setup>
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
</script>

<template>
  <div>
    <PageHeader title="学习记录" />
    <EmptyState title="还没有学习记录" description="开始学习后，你的学习记录会显示在这里" />
  </div>
</template>
