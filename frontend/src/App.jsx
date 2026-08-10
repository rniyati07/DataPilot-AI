import ChatWindow from './components/ChatWindow'
import DatabaseUpload from './components/DatabaseUpload'

export default function App() {
  return (
    <div className="mx-auto flex h-screen max-w-5xl flex-col p-4">
      <header className="mb-4">
        <h1 className="text-xl font-bold text-slate-900">DataPilot AI</h1>
        <p className="text-sm text-slate-500">Conversational AI data analyst</p>
      </header>

      <div className="mb-4">
        <DatabaseUpload />
      </div>

      <div className="flex-1 overflow-hidden rounded-xl border border-slate-200 bg-white">
        <ChatWindow />
      </div>
    </div>
  )
}
