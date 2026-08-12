const SESSION_STORAGE_KEY = 'datapilot_session_id'

// The frontend issues a session id on first load and reuses it for every
// request (TRD §3, Architecture §7). It is never LLM-facing — purely an
// HTTP-layer concern between the browser and FastAPI.
//
// Conversations own their session id (see lib/conversations.js): each one gets
// its own so the backend's per-session memory doesn't bleed between threads.
// This module keeps the "current" pointer that api/client.js reads.
export function getSessionId() {
  let sessionId = localStorage.getItem(SESSION_STORAGE_KEY)
  if (!sessionId) {
    sessionId = crypto.randomUUID()
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId)
  }
  return sessionId
}

export function setSessionId(sessionId) {
  if (!sessionId) return
  try {
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId)
  } catch {
    // Non-persistent storage; requests still carry the id for this page life.
  }
}

export function newSessionId() {
  const sessionId = crypto.randomUUID()
  setSessionId(sessionId)
  return sessionId
}
