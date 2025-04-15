const API_BASE_URL = process.env.VITE_API_URL || 'http://localhost:14000'

export const API_URLS = {
  auth: {
    register: `${API_BASE_URL}/api/auth/register`,
    login: `${API_BASE_URL}/api/auth/login`,
    logout: `${API_BASE_URL}/api/auth/logout`,
    me: `${API_BASE_URL}/api/auth/me`
  }
}

export default API_URLS
export { API_BASE_URL }
