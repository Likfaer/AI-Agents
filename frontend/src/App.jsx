import React, { useEffect } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import {
  MessageSquare, Bot, ListTodo, Database, Terminal,
  Activity, Cpu, ChevronRight, Zap
} from 'lucide-react'
import { useStore } from './store'
import { api } from './services/api'
import ChatPage from './pages/ChatPage'
import { AgentsPage, TasksPage, MemoryPage, LogsPage } from './pages/index.jsx'

const NAV_ITEMS = [
  { to: '/', icon: MessageSquare, label: 'Chat' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/tasks', icon: ListTodo, label: 'Tasks' },
  { to: '/memory', icon: Database, label: 'Memory' },
  { to: '/logs', icon: Terminal, label: 'Logs' },
]

export default function App() {
  const { health, setHealth, setAgents, currentModel } = useStore()

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const h = await api.health()
        setHealth(h)
      } catch {
        setHealth({ status: 'offline', lm_studio: false })
      }
    }
    const loadAgents = async () => {
      try {
        const { agents } = await api.listAgents()
        setAgents(agents)
      } catch {}
    }
    checkHealth()
    loadAgents()
    const interval = setInterval(checkHealth, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex h-screen bg-[#0a0a0f] overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 bg-[#111118] border-r border-[#1e1e2e] flex flex-col">
        {/* Logo */}
        <div className="px-4 py-5 border-b border-[#1e1e2e]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <div>
              <div className="text-sm font-semibold text-white leading-none">LM Studio</div>
              <div className="text-xs text-gray-500 mt-0.5">AI Platform</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-3 space-y-0.5">
          {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `nav-item ${isActive ? 'active text-white bg-[#2d2d3e]' : ''}`
              }
            >
              <Icon size={16} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Status bar */}
        <div className="px-3 py-3 border-t border-[#1e1e2e] space-y-2">
          <div className="flex items-center gap-2 text-xs">
            <div className={`status-dot ${health?.lm_studio ? 'completed' : 'failed'}`} />
            <span className="text-gray-400">LM Studio</span>
            <span className={`ml-auto font-medium ${health?.lm_studio ? 'text-green-400' : 'text-red-400'}`}>
              {health?.lm_studio ? 'Online' : 'Offline'}
            </span>
          </div>
          {health?.agents !== undefined && (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Cpu size={12} />
              <span>{health.agents} agents loaded</span>
            </div>
          )}
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/agents" element={<AgentsPage />} />
          <Route path="/tasks" element={<TasksPage />} />
          <Route path="/memory" element={<MemoryPage />} />
          <Route path="/logs" element={<LogsPage />} />
        </Routes>
      </main>
    </div>
  )
}
