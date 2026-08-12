import { useCallback, useEffect, useState } from 'react'
import AmbientBackground from '../components/AmbientBackground'
import Sidebar from '../components/Sidebar'
import TopBar from '../components/TopBar'
import DatabaseModal from '../components/DatabaseModal'
import ChatWindow from '../components/ChatWindow'
import { getCurrentDatabase } from '../api/client'
import {
  activateConversation,
  createConversation,
  listConversations,
  saveConversation,
  titleFrom,
} from '../lib/conversations'

// Dashboard shell. Owns the active-database state (from the real backend), the
// conversation history, and the theme; passes them down so the sidebar, header
// and chat share one source of truth.
export default function DashboardPage({ onBackHome, theme, onThemeChange }) {
  const [database, setDatabase] = useState(null)
  const [dbState, setDbState] = useState('loading') // loading | ready | error
  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const [conversations, setConversations] = useState(() => listConversations())
  const [current, setCurrent] = useState(() => createConversation())

  useEffect(() => {
    getCurrentDatabase()
      .then((info) => {
        setDatabase(info)
        setDbState('ready')
      })
      .catch(() => setDbState('error'))
  }, [])

  // Persist the live conversation as it grows, so a reload or a switch never
  // loses a thread that actually happened.
  const handleMessagesChange = useCallback((messages) => {
    setCurrent((conversation) => {
      const updated = { ...conversation, messages, title: titleFrom(messages) }
      setConversations(saveConversation(updated))
      return updated
    })
  }, [])

  function handleNewChat() {
    // The live conversation is already persisted by handleMessagesChange; a new
    // one gets its own session id, so the backend starts a fresh context rather
    // than continuing the previous thread's memory.
    setCurrent(createConversation())
  }

  function handleSelectConversation(id) {
    if (id === current.id) return
    const restored = activateConversation(id) // re-points X-Session-Id
    if (restored) setCurrent(restored)
  }

  return (
    <div className="relative flex h-screen overflow-hidden text-slate-200">
      <AmbientBackground />
      <Sidebar
        database={database}
        dbState={dbState}
        onNewChat={handleNewChat}
        onBackHome={onBackHome}
        onUploadClick={() => setIsUploadOpen(true)}
        conversations={conversations}
        activeConversationId={current.id}
        onSelectConversation={handleSelectConversation}
        theme={theme}
        onThemeChange={onThemeChange}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          database={database}
          dbState={dbState}
          onNewChat={handleNewChat}
          onBackHome={onBackHome}
          onUploadClick={() => setIsUploadOpen(true)}
        />

        <main className="min-h-0 flex-1">
          <ChatWindow
            // Remounting on conversation change gives each thread a clean slate.
            key={current.id}
            database={database}
            dbState={dbState}
            initialMessages={current.messages}
            onMessagesChange={handleMessagesChange}
            isLight={theme === 'light'}
          />
        </main>
      </div>

      <DatabaseModal
        open={isUploadOpen}
        database={database}
        onClose={() => setIsUploadOpen(false)}
        onDatabaseChange={setDatabase}
      />
    </div>
  )
}
