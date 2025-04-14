import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'

const app = createApp(App)
app.use(router)
app.use(store)

// Initialize authentication state
store.dispatch('initAuth').finally(() => {
  app.mount('#app')
})
