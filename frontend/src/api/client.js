import { getSessionId } from '../lib/session'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'X-Session-Id': getSessionId(),
      ...options.headers,
    },
  })

  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const body = await response.json()
      message = body?.detail?.message || body?.detail || message
    } catch {
      // response body wasn't JSON — fall back to the generic message
    }
    throw new ApiError(message, response.status)
  }

  return response.json()
}

export function sendChatMessage(message) {
  return request('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })
}

export function getCurrentDatabase() {
  return request('/api/database/current')
}

export function uploadDatabase(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request('/api/database/upload', {
    method: 'POST',
    body: formData,
  })
}

export function clearDatabase() {
  return request('/api/database/current', { method: 'DELETE' })
}
