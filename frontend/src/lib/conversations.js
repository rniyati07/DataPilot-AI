// Conversation history (refinement Part A).
//
// The backend has no conversation-list endpoint and no session-reset endpoint —
// its session store is process-local and keyed by X-Session-Id. So history is
// kept client-side in localStorage, which is honest about what exists: these
// are this browser's real past conversations, not a simulated server feature.
//
// Each conversation owns its own `sessionId`. That is what makes switching
// threads correct rather than cosmetic: the backend keeps separate memory per
// session id, so restoring a conversation also restores the context the agent
// reasons over, and starting a new chat genuinely begins a fresh context
// instead of silently continuing the previous one.
import { newSessionId, setSessionId } from './session'

const STORAGE_KEY = 'datapilot_conversations'
export const MAX_STORED_CONVERSATIONS = 12
export const MAX_VISIBLE_CONVERSATIONS = 5
const MAX_TITLE_LENGTH = 46

function read() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function write(conversations) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations.slice(0, MAX_STORED_CONVERSATIONS)))
  } catch {
    // Quota or private mode — history just won't persist across reloads.
  }
}

export function titleFrom(messages) {
  const firstUser = messages.find((message) => message.role === 'user')
  const text = (firstUser?.content?.message || '').trim()
  if (!text) return 'New conversation'
  return text.length > MAX_TITLE_LENGTH ? `${text.slice(0, MAX_TITLE_LENGTH - 1)}…` : text
}

export function createConversation() {
  const conversation = {
    id: crypto.randomUUID(),
    sessionId: newSessionId(),
    title: 'New conversation',
    messages: [],
    updatedAt: Date.now(),
  }
  return conversation
}

export function listConversations() {
  // Newest first, and only ones that actually contain a turn.
  return read()
    .filter((conversation) => conversation.messages?.length)
    .sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0))
}

/** Inserts or updates a conversation. Empty conversations are never stored. */
export function saveConversation(conversation) {
  if (!conversation?.messages?.length) return listConversations()

  const entry = {
    ...conversation,
    title: conversation.title && conversation.title !== 'New conversation'
      ? conversation.title
      : titleFrom(conversation.messages),
    updatedAt: Date.now(),
  }

  const others = read().filter((item) => item.id !== entry.id)
  write([entry, ...others].sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0)))
  return listConversations()
}

export function getConversation(id) {
  return read().find((conversation) => conversation.id === id) || null
}

/** Makes an existing conversation current, restoring its backend session. */
export function activateConversation(id) {
  const conversation = getConversation(id)
  if (!conversation) return null
  setSessionId(conversation.sessionId)
  return conversation
}

export function deleteConversation(id) {
  write(read().filter((conversation) => conversation.id !== id))
  return listConversations()
}
