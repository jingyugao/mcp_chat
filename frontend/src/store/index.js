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

export default createStore({
  state: {
    isAuthenticated: false,
    user: null,
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

        // Store the token in cookie
        setCookie('access_token', data.access_token)
        
        // Get user info
        const userResponse = await fetch(API_URLS.auth.me, {
          headers: {
            'Authorization': `Bearer ${data.access_token}`
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
        commit('setAuthenticated', false)
        commit('setLoginError', error.message)
        throw error
      }
    },
    logout({ commit }) {
      deleteCookie('access_token')
      commit('setUser', null)
      commit('setAuthenticated', false)
    },
    async initAuth({ commit, dispatch }) {
      const token = getCookie('access_token')
      if (token) {
        try {
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
          dispatch('logout')
        }
      }
    }
  },
  getters: {
    isAuthenticated: state => state.isAuthenticated,
    user: state => state.user,
    registrationError: state => state.registrationError,
    loginError: state => state.loginError
  }
}) 