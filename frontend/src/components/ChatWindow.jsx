import { useState } from 'react'
import MessageBubble from './MessageBubble'
import StatusIndicator from './StatusIndicator'
import ErrorBanner from './ErrorBanner'
import { sendChatMessage, ApiError } from '../api/client'

export default function ChatWindow() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(event) {
    event.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || isLoading) return

    setMessages((prev) => [...prev, { role: 'user', content: { message: trimmed } }])
    setInput('')
    setIsLoading(true)
    setError(null)

    try {
      const response = await sendChatMessage(trimmed)
      setMessages((prev) => [...prev, { role: 'agent', content: response }])
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Something went wrong. Please try again.'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.length === 0 && (
          <p className="text-center text-sm text-slate-400">
            Ask a question about your data to get started.
          </p>
        )}
        {messages.map((msg, index) => (
          // eslint-disable-next-line react/no-array-index-key
          <MessageBubble key={index} role={msg.role} content={msg.content} />
        ))}
        {isLoading && <StatusIndicator label="Thinking…" />}
      </div>

      {error && (
        <div className="px-4 pb-2">
          <ErrorBanner message={error} onDismiss={() => setError(null)} />
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-slate-200 p-4">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your data…"
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          Send
        </button>
      </form>
    </div>
  )
}
