const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:14000'

export const API_URLS = {
  auth: {
    register: `${API_BASE_URL}/api/auth/register`,
    login: `${API_BASE_URL}/api/auth/login`,
    me: `${API_BASE_URL}/api/auth/me`
  }
}

export default API_URLS 