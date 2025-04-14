<template>
  <div class="register-container">
    <div class="register-form">
      <h2>Create an Account</h2>
      <form @submit.prevent="handleSubmit" class="form">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            type="text"
            id="username"
            v-model="formData.username"
            required
            class="form-control"
          />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            type="email"
            id="email"
            v-model="formData.email"
            required
            class="form-control"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input
            type="password"
            id="password"
            v-model="formData.password"
            required
            class="form-control"
          />
        </div>

        <div class="form-group">
          <label for="confirmPassword">Confirm Password</label>
          <input
            type="password"
            id="confirmPassword"
            v-model="formData.confirmPassword"
            required
            class="form-control"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button type="submit" class="submit-button" :disabled="isLoading">
          {{ isLoading ? 'Creating Account...' : 'Create Account' }}
        </button>

        <p class="login-link">
          Already have an account? <router-link to="/login">Log in</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

export default {
  name: 'RegisterView',
  setup() {
    const store = useStore()
    const router = useRouter()
    const isLoading = ref(false)
    const error = computed(() => store.state.registrationError)

    const formData = ref({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })

    const validateForm = () => {
      if (formData.value.password.length < 6) {
        store.commit('setRegistrationError', 'Password must be at least 6 characters long')
        return false
      }

      if (formData.value.password !== formData.value.confirmPassword) {
        store.commit('setRegistrationError', 'Passwords do not match')
        return false
      }

      return true
    }

    const handleSubmit = async () => {
      if (!validateForm()) return

      isLoading.value = true
      store.commit('setRegistrationError', null)

      try {
        const userData = {
          username: formData.value.username,
          email: formData.value.email,
          password: formData.value.password
        }

        await store.dispatch('register', userData)
        router.push('/login')
      } catch (err) {
        // Error is already handled in the store
      } finally {
        isLoading.value = false
      }
    }

    return {
      formData,
      error,
      isLoading,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  background-color: #f5f5f5;
}

.register-form {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

h2 {
  text-align: center;
  color: #333;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #666;
}

.form-control {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.form-control:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.error-message {
  color: #dc3545;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.submit-button {
  width: 100%;
  padding: 0.75rem;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.submit-button:hover {
  background-color: #45a049;
}

.submit-button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}

.login-link {
  text-align: center;
  margin-top: 1rem;
  color: #666;
}

.login-link a {
  color: #4CAF50;
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}
</style> 