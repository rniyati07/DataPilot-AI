import AgentMessage from './AgentMessage'

// Routes a message to its presentation: right-aligned user bubble or the
// left-aligned DataPilot response card stack (frontend batch §Batch 3/4).
export default function MessageBubble({ role, content, isLight }) {
  if (role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] animate-fade-up rounded-2xl rounded-br-sm bg-brand-gradient px-4 py-2.5 text-sm leading-relaxed text-white shadow-[0_4px_20px_rgb(99_102_241_/_0.3)] sm:max-w-[70%]">
          {content.message}
        </div>
      </div>
    )
  }

  return <AgentMessage content={content} isLight={isLight} />
}
