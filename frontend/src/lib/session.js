const SESSION_STORAGE_KEY = 'datapilot_session_id'

// The frontend issues a session id on first load and reuses it for every
// request (TRD §3, Architecture §7). It is never LLM-facing — purely an
// HTTP-layer concern between the browser and FastAPI.
export function getSessionId() {
  let sessionId = localStorage.getItem(SESSION_STORAGE_KEY)
  if (!sessionId) {
    sessionId = crypto.randomUUID()
    localStorage.setItem(SESSION_STORAGE_KEY, sessionId)
  }
  return sessionId
}
