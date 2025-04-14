import { createStore } from 'vuex'
import API_URLS from '../api/config'

// Cookie utility functions
const setCookie = (name, value, days = 7) => {
  const date = new Date()
  date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000))
  const expires = `expires=${date.toUTCString()}`
  document.cookie = `${name}=${value};${expires};path=/`
}

const getCookie = (name) => {
  const nameEQ = `${name}=`
  const ca = document.cookie.split(';')
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i]
    while (c.charAt(0) === ' ') c = c.substring(1, c.length)
    if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length)
  }
  return null
}

const deleteCookie = (name) => {
  document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:01 GMT;path=/`
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

export default createStore({
  state: {
    isAuthenticated: false,
    user: null,
    token: null,
    registrationError: null,
    loginError: null
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
    },
    setRegistrationError(state, error) {
      state.registrationError = error
    },
    setLoginError(state, error) {
      state.loginError = error
    }
  },
  actions: {
    async register({ commit }, userData) {
      try {
        const response = await fetch(API_URLS.auth.register, {
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

        // Store the token in cookie and state
        setCookie('access_token', token)
        commit('setToken', token)
        
        // Get user info
        const userResponse = await fetch(API_URLS.auth.me, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

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
      const token = getCookie('access_token')
      if (token) {
        try {
          await fetch(API_URLS.auth.logout, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
        } catch (error) {
          console.error('Logout error:', error)
        }
      }
      deleteCookie('access_token')
      commit('setToken', null)
      commit('setUser', null)
      commit('setAuthenticated', false)
    },
    async initAuth({ commit, dispatch }) {
      const token = getCookie('access_token')
      
      if (!token || !isTokenValid(token)) {
        dispatch('logout')
        return
      }

      try {
        commit('setToken', token)
        
        const userResponse = await fetch(API_URLS.auth.me, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

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
    },
    // Add automatic token refresh
    async refreshToken({ state, commit, dispatch }) {
      if (!state.token || !isTokenValid(state.token)) {
        dispatch('logout')
        return
      }

      try {
        const response = await fetch(API_URLS.auth.refresh, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${state.token}`
          }
        })

        if (!response.ok) {
          throw new Error('Token refresh failed')
        }

        const data = await response.json()
        const newToken = data.access_token

        if (!isTokenValid(newToken)) {
          throw new Error('Invalid token received')
        }

        setCookie('access_token', newToken)
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
    loginError: state => state.loginError
  }
}) 