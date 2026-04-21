import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: 'cultural-products',
        name: 'CulturalProducts',
        component: () => import('@/views/CulturalProducts.vue')
      },
      {
        path: 'video-management',
        name: 'Videos',
        component: () => import('@/views/Videos.vue')
      },
      {
        path: 'skus',
        name: 'SKUs',
        component: () => import('@/views/SKUs.vue')
      },
      {
        path: 'nfc-tags',
        name: 'NFCTags',
        component: () => import('@/views/NFCTags.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth !== false && !authStore.token) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && authStore.token) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
