import { createStore } from 'vuex'
import API_URLS from '../api/config'

// Token storage utility functions
const setToken = (token) => {
  if (token) {
    localStorage.setItem('access_token', token)
  } else {
    localStorage.removeItem('access_token')
  }
}

const getToken = () => {
  return localStorage.getItem('access_token')
}

// Token validation function
const isTokenValid = (token) => {
  if (!token) return false
  try {
    // Simple JWT structure validation
    const parts = token.split('.')
    if (parts.length !== 3) return false
    
    // Check token expiration
    const payload = JSON.parse(atob(parts[1]))
    const exp = payload.exp * 1000 // Convert to milliseconds
    return Date.now() < exp
  } catch (e) {
    return false
  }
}

// API request helper with auth token
const authFetch = async (url, options = {}) => {
  const token = getToken()
  if (token) {
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  }
  return fetch(url, options)
}

export default createStore({
  state: {
    isAuthenticated: false,
    user: null,
    token: null,
    registrationError: null,
    loginError: null,
    initialized: false
  },
  mutations: {
    setAuthenticated(state, value) {
      state.isAuthenticated = value
    },
    setUser(state, user) {
      state.user = user
    },
    setToken(state, token) {
      state.token = token
      setToken(token)
    },
    setRegistrationError(state, error) {
      state.registrationError = error
    },
    setLoginError(state, error) {
      state.loginError = error
    },
    setInitialized(state, value) {
      state.initialized = value
    }
  },
  actions: {
    async register({ commit }, userData) {
      try {
        const response = await authFetch(API_URLS.auth.register, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(userData)
        })

        const data = await response.json()
        
        if (!response.ok) {
          throw new Error(data.detail || 'Registration failed')
        }

        commit('setRegistrationError', null)
        return data
      } catch (error) {
        commit('setRegistrationError', error.message)
        throw error
      }
    },
    async login({ commit }, credentials) {
      try {
        const response = await fetch(API_URLS.auth.login, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(credentials)
        })

        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.detail || 'Login failed')
        }

        const token = data.access_token
        if (!isTokenValid(token)) {
          throw new Error('Invalid token received')
        }

        // Store the token in localStorage and state
        commit('setToken', token)
        
        // Get user info
        const userResponse = await authFetch(API_URLS.auth.me)

        if (!userResponse.ok) {
          throw new Error('Failed to get user info')
        }

        const userInfo = await userResponse.json()
        commit('setUser', userInfo)
        commit('setAuthenticated', true)
        commit('setLoginError', null)
        return userInfo
      } catch (error) {
        commit('setUser', null)
        commit('setToken', null)
        commit('setAuthenticated', false)
        commit('setLoginError', error.message)
        throw error
      }
    },
    async logout({ commit }) {
      const token = getToken()
      if (token) {
        try {
          await authFetch(API_URLS.auth.logout, {
            method: 'POST'
          })
        } catch (error) {
          console.error('Logout error:', error)
        }
      }
      commit('setToken', null)
      commit('setUser', null)
      commit('setAuthenticated', false)
    },
    async initAuth({ commit, dispatch }) {
      const token = getToken()
      
      if (!token || !isTokenValid(token)) {
        dispatch('logout')
      } else {
        try {
          commit('setToken', token)
          
          const userResponse = await authFetch(API_URLS.auth.me)

          if (!userResponse.ok) {
            throw new Error('Token invalid')
          }

          const userInfo = await userResponse.json()
          commit('setUser', userInfo)
          commit('setAuthenticated', true)
        } catch (error) {
          console.error('Auth initialization error:', error)
          dispatch('logout')
        }
      }
      
      commit('setInitialized', true)
    },
    // Add automatic token refresh
    async refreshToken({ state, commit, dispatch }) {
      if (!state.token || !isTokenValid(state.token)) {
        dispatch('logout')
        return
      }

      try {
        const response = await authFetch(API_URLS.auth.refresh, {
          method: 'POST'
        })

        if (!response.ok) {
          throw new Error('Token refresh failed')
        }

        const data = await response.json()
        const newToken = data.access_token

        if (!isTokenValid(newToken)) {
          throw new Error('Invalid token received')
        }

        commit('setToken', newToken)
      } catch (error) {
        console.error('Token refresh error:', error)
        dispatch('logout')
      }
    }
  },
  getters: {
    isAuthenticated: state => state.isAuthenticated,
    user: state => state.user,
    token: state => state.token,
    registrationError: state => state.registrationError,
    loginError: state => state.loginError,
    initialized: state => state.initialized
  }
}) 