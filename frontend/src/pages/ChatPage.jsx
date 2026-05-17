import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Square, RefreshCw, ChevronDown, Bot, User, Wrench, Clock } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { useStore } from '../store'
import { api } from '../services/api'

const AGENTS = [
  { id: 'orchestrator', label: 'Orchestrator', color: 'text-purple-400' },
  { id: 'coding', label: 'Coding', color: 'text-blue-400' },
  { id: 'research', label: 'Research', color: 'text-green-400' },
  { id: 'file', label: 'File', color: 'text-yellow-400' },
  { id: 'devops', label: 'DevOps', color: 'text-orange-400' },
  { id: 'builder', label: 'Builder', color: 'text-pink-400' },
]

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-3 animate-slide-in ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center text-xs font-bold
        ${isUser ? 'bg-accent' : 'bg-[#2d2d3e]'}`}>
        {isUser ? <User size={14} /> : <Bot size={14} />}
      </div>

      {/* Bubble */}
      <div className={`max-w-[80%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        {/* Meta */}
        <div className={`flex items-center gap-2 text-xs text-gray-500 ${isUser ? 'flex-row-reverse' : ''}`}>
          <span>{isUser ? 'You' : msg.agent || 'Assistant'}</span>
          {msg.execution_time && (
            <span className="flex items-center gap-1">
              <Clock size={10} />
              {msg.execution_time}s
            </span>
          )}
          {msg.tools_used?.length > 0 && (
            <span className="flex items-center gap-1 text-accent">
              <Wrench size={10} />
              {msg.tools_used.join(', ')}
            </span>
          )}
        </div>

        {/* Content */}
        <div className={`rounded-xl px-4 py-3 text-sm
          ${isUser
            ? 'bg-accent text-white rounded-tr-sm'
            : 'bg-[#1a1a24] border border-[#2d2d3e] text-gray-200 rounded-tl-sm'
          }`}>
          {msg.loading ? (
            <div className="flex items-center gap-2 text-gray-400">
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1.5 h-1.5 rounded-full bg-accent animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <span>Thinking...</span>
            </div>
          ) : isUser ? (
            <p className="whitespace-pre-wrap">{msg.content}</p>
          ) : (
            <div className="prose-dark">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {msg.error && (
          <div className="text-xs text-red-400 bg-red-400/10 border border-red-400/20 rounded px-2 py-1">
            Error: {msg.error}
          </div>
        )}
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { messages, addMessage, updateLastMessage, clearMessages, selectedAgent, setAgent, isLoading, setLoading } = useStore()
  const [input, setInput] = useState('')
  const [showAgentMenu, setShowAgentMenu] = useState(false)
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const selectedAgentInfo = AGENTS.find(a => a.id === selectedAgent) || AGENTS[0]

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback(async () => {
    const text = input.trim()
    if (!text || isLoading) return

    setInput('')
    setLoading(true)

    addMessage({ id: Date.now(), role: 'user', content: text })
    const loadingId = Date.now() + 1
    addMessage({ id: loadingId, role: 'assistant', agent: selectedAgent, content: '', loading: true })

    try {
      const result = await api.chat(text, selectedAgent)
      updateLastMessage({ loading: false, content: result.content, tools_used: result.tools_used, execution_time: result.execution_time, error: result.error })
    } catch (err) {
      updateLastMessage({ loading: false, content: '', error: err.message })
    } finally {
      setLoading(false)
    }
  }, [input, isLoading, selectedAgent, addMessage, updateLastMessage, setLoading])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[#1e1e2e] flex items-center justify-between">
        <div>
          <h1 className="text-white font-semibold">Chat</h1>
          <p className="text-xs text-gray-500 mt-0.5">Talk to your AI agents</p>
        </div>
        <button onClick={clearMessages} className="btn-ghost text-xs flex items-center gap-1.5">
          <RefreshCw size={13} />
          Clear
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-[#1a1a24] border border-[#2d2d3e] flex items-center justify-center">
              <Bot size={28} className="text-accent" />
            </div>
            <div>
              <p className="text-gray-300 font-medium">Start a conversation</p>
              <p className="text-gray-500 text-sm mt-1">Ask the AI to write code, search the web, manage files, and more</p>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {[
                'Write a FastAPI REST API with authentication',
                'Search the web for latest Python 3.13 features',
                'Create a React component for a dashboard',
                'Explain Docker multi-stage builds',
              ].map(suggestion => (
                <button
                  key={suggestion}
                  onClick={() => { setInput(suggestion); inputRef.current?.focus() }}
                  className="text-left text-xs text-gray-400 bg-[#1a1a24] border border-[#2d2d3e] rounded-lg px-3 py-2 hover:border-accent/40 hover:text-gray-200 transition-all"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => (
          <MessageBubble key={msg.id} msg={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t border-[#1e1e2e]">
        <div className="flex items-end gap-3 bg-[#1a1a24] border border-[#2d2d3e] rounded-xl p-3 focus-within:border-accent/50 transition-colors">
          {/* Agent selector */}
          <div className="relative">
            <button
              onClick={() => setShowAgentMenu(!showAgentMenu)}
              className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1.5 rounded-lg bg-[#2d2d3e] hover:bg-[#3d3d50] transition-colors ${selectedAgentInfo.color}`}
            >
              <Bot size={12} />
              {selectedAgentInfo.label}
              <ChevronDown size={11} />
            </button>

            {showAgentMenu && (
              <div className="absolute bottom-full mb-2 left-0 bg-[#1a1a24] border border-[#2d2d3e] rounded-xl shadow-2xl py-1 min-w-36 z-10">
                {AGENTS.map(agent => (
                  <button
                    key={agent.id}
                    onClick={() => { setAgent(agent.id); setShowAgentMenu(false) }}
                    className={`w-full text-left px-3 py-2 text-xs hover:bg-[#2d2d3e] transition-colors ${agent.color} ${agent.id === selectedAgent ? 'bg-[#2d2d3e]' : ''}`}
                  >
                    {agent.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Text area */}
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything... (Enter to send, Shift+Enter for newline)"
            className="flex-1 bg-transparent text-gray-200 text-sm placeholder-gray-600 resize-none outline-none max-h-40 leading-relaxed"
            rows={1}
            style={{ minHeight: '24px' }}
            onInput={e => {
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px'
            }}
          />

          {/* Send */}
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="w-8 h-8 rounded-lg bg-accent hover:bg-accent-hover disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors flex-shrink-0"
          >
            {isLoading ? <Square size={13} className="text-white" /> : <Send size={13} className="text-white" />}
          </button>
        </div>
        <p className="text-xs text-gray-600 mt-2 text-center">
          Powered by LM Studio • Local AI • No data leaves your machine
        </p>
      </div>
    </div>
  )
}
