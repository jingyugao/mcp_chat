<template>
  <div id="app">
    <nav class="navbar" v-if="isAuthenticated">
      <router-link to="/" class="nav-link">Home</router-link>
      <router-link to="/chat" class="nav-link">Chat</router-link>
      <router-link to="/server-manager" class="nav-link">Server Manager</router-link>
      <button @click="logout" class="logout-btn">Logout</button>
    </nav>
    <router-view></router-view>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'App',
  setup() {
    const store = useStore()
    const router = useRouter()

    const isAuthenticated = computed(() => store.getters.isAuthenticated)

    const logout = () => {
      store.dispatch('logout')
      router.push('/login')
    }

    return {
      isAuthenticated,
      logout
    }
  }
}
</script>

<style>
#app {
  font-family: Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  margin: 0;
  min-height: 100vh;
  background-color: #f8f9fa;
}

.navbar {
  background-color: #ffffff;
  padding: 1rem 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.nav-link {
  color: #2c3e50;
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.nav-link:hover {
  background-color: #f8f9fa;
}

.nav-link.router-link-active {
  color: #1976d2;
  background-color: #e3f2fd;
}

.logout-btn {
  margin-left: auto;
  padding: 0.5rem 1rem;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.logout-btn:hover {
  background-color: #c82333;
}
</style>
