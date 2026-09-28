<script setup>
import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
</script>

<template>
  <div>
    <PageHeader title="面试记录" />
    <EmptyState title="还没有面试记录" description="完成一次模拟面试后，可以在这里查看记录" />
  </div>
</template>
