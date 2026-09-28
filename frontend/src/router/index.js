import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/home' },
  {
    path: '/home',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '首页' },
  },
  {
    path: '/learning/knowledge',
    name: 'knowledge',
    component: () => import('@/views/learning/KnowledgeView.vue'),
    meta: { title: '知识库' },
  },
  {
    path: '/learning/knowledge/:id',
    name: 'knowledge-detail',
    component: () => import('@/views/learning/KnowledgeDetailView.vue'),
    meta: { title: '知识详情', tab: false },
  },
  {
    path: '/learning/qa',
    name: 'qa',
    component: () => import('@/views/learning/QaView.vue'),
    meta: { title: '知识问答' },
  },
  {
    path: '/learning/plan',
    name: 'plan',
    component: () => import('@/views/learning/PlanView.vue'),
    meta: { title: '学习计划' },
  },
  {
    path: '/learning/plan/:id',
    name: 'plan-detail',
    component: () => import('@/views/learning/PlanDetailView.vue'),
    meta: { title: '学习计划详情', tab: false },
  },
  {
    path: '/interview/setup',
    name: 'interview-setup',
    component: () => import('@/views/interview/SetupView.vue'),
    meta: { title: '模拟面试' },
  },
  {
    path: '/interview/session/:id',
    name: 'interview-session',
    component: () => import('@/views/interview/SessionView.vue'),
    meta: { title: '面试进行中', tab: false },
  },
  {
    path: '/interview/:sessionId/evaluation',
    name: 'interview-evaluation',
    component: () => import('@/views/interview/EvaluationView.vue'),
    meta: { title: '面试评价', tab: false },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/profile/ProfileView.vue'),
    meta: { title: '我的' },
  },
  {
    path: '/profile/learning-history',
    name: 'learning-history',
    component: () => import('@/views/profile/LearningHistoryView.vue'),
    meta: { title: '学习记录' },
  },
  {
    path: '/profile/interview-history',
    name: 'interview-history',
    component: () => import('@/views/profile/InterviewHistoryView.vue'),
    meta: { title: '面试记录' },
  },
  {
    path: '/profile/settings',
    name: 'settings',
    component: () => import('@/views/profile/SettingsView.vue'),
    meta: { title: '设置' },
  },
  {
    path: '/profile/ai-models',
    name: 'ai-models',
    component: () => import('@/views/profile/AiModelsView.vue'),
    meta: { title: 'AI 模型 / API' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · PM Copilot` : 'PM Copilot'
})

export default router
