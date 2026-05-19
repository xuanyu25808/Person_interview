import { createRouter, createWebHistory } from 'vue-router'
import InterviewPage from '../pages/interview/InterviewPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'interview',
      component: InterviewPage,
    },
  ],
})

export default router
