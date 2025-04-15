
const getToken = () => localStorage.getItem('access_token')

const createHeaders = (customHeaders = {}) => {
  const headers = {
    'Content-Type': 'application/json',
    ...customHeaders
  }

  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  return headers
}

export const httpClient = {
  async get(url, customHeaders = {}) {
    const response = await fetch(url, {
      method: 'GET',
      headers: createHeaders(customHeaders)
    })
    return response
  },

  async post(url, data = null, customHeaders = {}) {
    const response = await fetch(url, {
      method: 'POST',
      headers: createHeaders(customHeaders),
      body: data ? JSON.stringify(data) : null
    })
    return response
  },

  async delete(url, customHeaders = {}) {
    const response = await fetch(url, {
      method: 'DELETE',
      headers: createHeaders(customHeaders)
    })
    return response
  }
}

export default httpClient 