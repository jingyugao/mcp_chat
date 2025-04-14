import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/Home.vue'
import ChatView from '../views/ChatView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import ServerManagerView from '../views/ServerManagerView.vue'
import store from '../store'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { requiresAuth: true }
  },
  {
    path: '/chat',
    name: 'chat',
    component: ChatView,
    meta: { requiresAuth: true }
  },
  {
    path: '/server-manager',
    name: 'server-manager',
    component: ServerManagerView,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: { guest: true }
  },
  // Add catch-all route for 404
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  // Try to initialize auth state if not already done
  if (!store.state.initialized) {
    await store.dispatch('initAuth')
  }

  const isAuthenticated = store.getters.isAuthenticated

  // Routes that require authentication
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!isAuthenticated) {
      // Save the intended destination
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
    } else {
      next()
    }
  }
  // Routes for guests only (like login and register)
  else if (to.matched.some(record => record.meta.guest)) {
    if (isAuthenticated) {
      // If user is already logged in, redirect to home
      next({ path: '/' })
    } else {
      next()
    }
  }
  // Public routes
  else {
    next()
  }
})

export default router 