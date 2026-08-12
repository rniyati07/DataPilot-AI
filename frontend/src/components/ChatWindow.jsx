import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'
import StatusIndicator from './StatusIndicator'
import ErrorBanner from './ErrorBanner'
import WelcomeState from './WelcomeState'
import ChatInput from './ChatInput'
import { sendChatMessage, ApiError } from '../api/client'

// The conversation, not a query editor (frontend batch §Batch 3). Holds the
// thread in memory, sends real requests through the existing API, and keeps
// the newest content in view.
export default function ChatWindow({
  database,
  dbState,
  initialMessages = [],
  onMessagesChange,
  isLight = false,
}) {
  const [messages, setMessages] = useState(initialMessages)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const scrollAnchorRef = useRef(null)

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isLoading])

  function commit(updater) {
    setMessages((prev) => {
      const next = updater(prev)
      onMessagesChange?.(next)
      return next
    })
  }

  async function ask(text) {
    const trimmed = text.trim()
    if (!trimmed || isLoading) return

    commit((prev) => [...prev, { role: 'user', content: { message: trimmed } }])
    setInput('')
    setIsLoading(true)
    setError(null)

    try {
      const response = await sendChatMessage(trimmed)
      commit((prev) => [...prev, { role: 'agent', content: response }])
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : 'Something went wrong. Please try again.'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="min-h-0 flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <WelcomeState database={database} dbState={dbState} onAsk={ask} isLoading={isLoading} />
        ) : (
          <div className="mx-auto max-w-3xl space-y-6 px-4 py-6 sm:px-6">
            {messages.map((msg, index) => (
              // eslint-disable-next-line react/no-array-index-key
              <MessageBubble key={index} role={msg.role} content={msg.content} isLight={isLight} />
            ))}
            {isLoading && <StatusIndicator />}
          </div>
        )}
        <div ref={scrollAnchorRef} />
      </div>

      {error && (
        <div className="px-4 pb-3 sm:px-6">
          <ErrorBanner message={error} onDismiss={() => setError(null)} />
        </div>
      )}

      <ChatInput value={input} onChange={setInput} onSubmit={ask} disabled={isLoading} />
    </div>
  )
}
