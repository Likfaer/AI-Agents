import React, { useEffect, useState } from 'react'
import { Bot, RefreshCw, Wrench, Cpu, Play, CheckCircle, XCircle, Clock, Loader, X, Database, Trash2, Search, Terminal, AlertCircle } from 'lucide-react'
import { useStore } from '../store'
import { api } from '../services/api'

// ─── Agents Page ──────────────────────────────────────────────────────────────

export function AgentsPage() {
  const { agents, setAgents } = useStore()
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try { const { agents } = await api.listAgents(); setAgents(agents) } catch {}
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  const AGENT_COLORS = {
    Orchestrator: 'from-purple-500/20 to-purple-500/5 border-purple-500/30',
    'Coding Agent': 'from-blue-500/20 to-blue-500/5 border-blue-500/30',
    'Research Agent': 'from-green-500/20 to-green-500/5 border-green-500/30',
    'File Agent': 'from-yellow-500/20 to-yellow-500/5 border-yellow-500/30',
    'DevOps Agent': 'from-orange-500/20 to-orange-500/5 border-orange-500/30',
    'Builder Agent': 'from-pink-500/20 to-pink-500/5 border-pink-500/30',
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-4 border-b border-[#1e1e2e] flex items-center justify-between">
        <div>
          <h1 className="text-white font-semibold">Agents</h1>
          <p className="text-xs text-gray-500 mt-0.5">{agents.length} agents registered</p>
        </div>
        <button onClick={load} disabled={loading} className="btn-ghost text-xs flex items-center gap-1.5">
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {agents.map(agent => (
            <div key={agent.agent_id}
              className={`bg-gradient-to-br ${AGENT_COLORS[agent.name] || 'from-gray-500/20 to-gray-500/5 border-gray-500/30'} border rounded-xl p-5 hover:border-opacity-60 transition-all`}>
              <div className="flex items-start gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-[#1a1a24] flex items-center justify-center flex-shrink-0">
                  <Bot size={20} className="text-accent" />
                </div>
                <div>
                  <h3 className="text-white font-medium text-sm">{agent.name}</h3>
                  <p className="text-gray-400 text-xs mt-0.5 leading-relaxed">{agent.description}</p>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-white/5">
                <p className="text-xs text-gray-500 mb-2 flex items-center gap-1"><Wrench size={11} /> Tools</p>
                <div className="flex flex-wrap gap-1.5">
                  {(agent.tools || []).map(tool => (
                    <span key={tool} className="text-xs bg-[#1a1a24] border border-[#2d2d3e] px-2 py-0.5 rounded text-gray-400 font-mono">
                      {tool}
                    </span>
                  ))}
                </div>
              </div>

              <div className="mt-3 flex items-center gap-2">
                <Cpu size={11} className="text-gray-500" />
                <span className="text-xs text-gray-500 font-mono">{agent.model || 'local-model'}</span>
                <div className="ml-auto flex items-center gap-1.5">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-400" />
                  <span className="text-xs text-green-400">Ready</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Tasks Page ───────────────────────────────────────────────────────────────

const STATUS_ICONS = {
  pending: <Clock size={13} className="text-yellow-400" />,
  running: <Loader size={13} className="text-blue-400 animate-spin" />,
  completed: <CheckCircle size={13} className="text-green-400" />,
  failed: <XCircle size={13} className="text-red-400" />,
  cancelled: <X size={13} className="text-gray-400" />,
}

export function TasksPage() {
  const { tasks, setTasks, addTask } = useStore()
  const [loading, setLoading] = useState(false)
  const [prompt, setPrompt] = useState('')
  const [agent, setAgent] = useState('orchestrator')
  const [selected, setSelected] = useState(null)

  const load = async () => {
    setLoading(true)
    try { const { tasks } = await api.listTasks(30); setTasks(tasks) } catch {}
    setLoading(false)
  }

  useEffect(() => { load(); const i = setInterval(load, 3000); return () => clearInterval(i) }, [])

  const submit = async () => {
    if (!prompt.trim()) return
    const task = await api.createTask(prompt, agent)
    addTask({ task_id: task.task_id, prompt, agent_name: agent, status: 'pending', created_at: new Date().toISOString() })
    setPrompt('')
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-4 border-b border-[#1e1e2e] flex items-center justify-between">
        <div>
          <h1 className="text-white font-semibold">Tasks</h1>
          <p className="text-xs text-gray-500 mt-0.5">Async task management</p>
        </div>
        <button onClick={load} disabled={loading} className="btn-ghost text-xs flex items-center gap-1.5">
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      <div className="p-6 border-b border-[#1e1e2e]">
        <div className="flex gap-3">
          <input
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && submit()}
            placeholder="Task description..."
            className="flex-1 bg-[#1a1a24] border border-[#2d2d3e] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 outline-none focus:border-accent/50"
          />
          <select
            value={agent}
            onChange={e => setAgent(e.target.value)}
            className="bg-[#1a1a24] border border-[#2d2d3e] rounded-lg px-3 py-2 text-sm text-gray-300 outline-none"
          >
            {['orchestrator', 'coding', 'research', 'file', 'devops', 'builder'].map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
          <button onClick={submit} className="btn-primary flex items-center gap-2">
            <Play size={14} /> Run
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <div className="w-1/2 border-r border-[#1e1e2e] overflow-y-auto">
          {tasks.map(task => (
            <div
              key={task.task_id}
              onClick={() => setSelected(task)}
              className={`px-5 py-4 border-b border-[#1e1e2e] cursor-pointer hover:bg-[#1a1a24] transition-colors ${selected?.task_id === task.task_id ? 'bg-[#1a1a24]' : ''}`}
            >
              <div className="flex items-center gap-2 mb-1">
                {STATUS_ICONS[task.status]}
                <span className="text-xs font-mono text-gray-500">{task.task_id}</span>
                <span className="text-xs text-gray-500 ml-auto">{task.agent_name}</span>
              </div>
              <p className="text-sm text-gray-300 truncate">{task.prompt}</p>
            </div>
          ))}
          {tasks.length === 0 && (
            <div className="p-8 text-center text-gray-500 text-sm">No tasks yet. Submit one above.</div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {selected ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                {STATUS_ICONS[selected.status]}
                <span className="text-white font-medium capitalize">{selected.status}</span>
                <span className="text-xs font-mono text-gray-500 ml-auto">#{selected.task_id}</span>
              </div>
              <div className="glass p-4">
                <p className="text-xs text-gray-500 mb-1">Prompt</p>
                <p className="text-sm text-gray-200">{selected.prompt}</p>
              </div>
              {selected.result?.content && (
                <div className="glass p-4">
                  <p className="text-xs text-gray-500 mb-2">Result</p>
                  <div className="prose-dark text-sm">
                    <ReactMarkdown>{selected.result.content}</ReactMarkdown>
                  </div>
                </div>
              )}
              {selected.error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
                  <p className="text-xs text-red-400 font-medium mb-1 flex items-center gap-1"><AlertCircle size={12} /> Error</p>
                  <p className="text-sm text-red-300">{selected.error}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500 text-sm">
              Select a task to view details
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Need ReactMarkdown in TasksPage
import ReactMarkdown from 'react-markdown'

// ─── Memory Page ──────────────────────────────────────────────────────────────

export function MemoryPage() {
  const [query, setQuery] = useState('')
  const [collection, setCollection] = useState('long_term')
  const [results, setResults] = useState('')
  const [storeText, setStoreText] = useState('')
  const [overview, setOverview] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api.listMemory().then(r => setOverview(r.result)).catch(() => {})
  }, [])

  const search = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const r = await api.queryMemory(query, collection)
      setResults(r.result)
    } catch (e) { setResults('Error: ' + e.message) }
    setLoading(false)
  }

  const store = async () => {
    if (!storeText.trim()) return
    await api.storeMemory(storeText, collection)
    setStoreText('')
    const r = await api.listMemory()
    setOverview(r.result)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-4 border-b border-[#1e1e2e]">
        <h1 className="text-white font-semibold">Memory</h1>
        <p className="text-xs text-gray-500 mt-0.5">Agent knowledge store</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {overview && (
          <div className="glass p-4">
            <p className="text-xs text-gray-500 mb-2 flex items-center gap-1"><Database size={12} /> Collections</p>
            <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap">{overview}</pre>
          </div>
        )}

        <div className="glass p-4 space-y-3">
          <p className="text-sm font-medium text-white">Store Memory</p>
          <div className="flex gap-3">
            <textarea
              value={storeText}
              onChange={e => setStoreText(e.target.value)}
              placeholder="Enter information to store..."
              className="flex-1 bg-[#0a0a0f] border border-[#2d2d3e] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 outline-none focus:border-accent/50 resize-none"
              rows={2}
            />
            <select value={collection} onChange={e => setCollection(e.target.value)}
              className="bg-[#0a0a0f] border border-[#2d2d3e] rounded-lg px-3 py-2 text-sm text-gray-300 outline-none self-start">
              {['long_term', 'short_term', 'project', 'agent'].map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <button onClick={store} className="btn-primary text-sm">Store</button>
        </div>

        <div className="glass p-4 space-y-3">
          <p className="text-sm font-medium text-white">Search Memory</p>
          <div className="flex gap-3">
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && search()}
              placeholder="Search query..."
              className="flex-1 bg-[#0a0a0f] border border-[#2d2d3e] rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 outline-none focus:border-accent/50"
            />
            <button onClick={search} disabled={loading} className="btn-primary flex items-center gap-2">
              <Search size={14} /> {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
          {results && (
            <div className="bg-[#0a0a0f] border border-[#2d2d3e] rounded-lg p-4">
              <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap">{results}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ─── Logs Page ────────────────────────────────────────────────────────────────

export function LogsPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [filter, setFilter] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const { logs } = await api.getLogs(200)
      setLogs(logs)
    } catch {}
    setLoading(false)
  }

  useEffect(() => { load(); const i = setInterval(load, 5000); return () => clearInterval(i) }, [])

  const filtered = filter
    ? logs.filter(l => JSON.stringify(l).toLowerCase().includes(filter.toLowerCase()))
    : logs

  const LEVEL_COLORS = {
    ERROR: 'text-red-400 bg-red-400/10',
    WARNING: 'text-yellow-400 bg-yellow-400/10',
    INFO: 'text-blue-400 bg-blue-400/10',
    DEBUG: 'text-gray-500 bg-gray-500/10',
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-6 py-4 border-b border-[#1e1e2e] flex items-center justify-between">
        <div>
          <h1 className="text-white font-semibold">Logs</h1>
          <p className="text-xs text-gray-500 mt-0.5">{filtered.length} entries</p>
        </div>
        <div className="flex items-center gap-3">
          <input
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="Filter logs..."
            className="bg-[#1a1a24] border border-[#2d2d3e] rounded-lg px-3 py-1.5 text-xs text-gray-300 placeholder-gray-600 outline-none focus:border-accent/50 w-48"
          />
          <button onClick={load} disabled={loading} className="btn-ghost text-xs flex items-center gap-1.5">
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto font-mono">
        {filtered.slice().reverse().map((log, i) => (
          <div key={i} className="px-5 py-2 border-b border-[#1a1a24] hover:bg-[#1a1a24] transition-colors text-xs flex items-start gap-3">
            <span className={`flex-shrink-0 px-1.5 py-0.5 rounded text-xs font-medium ${LEVEL_COLORS[log.level] || 'text-gray-400'}`}>
              {log.level || 'LOG'}
            </span>
            <span className="text-gray-600 flex-shrink-0">{(log.timestamp || '').slice(11, 19)}</span>
            <span className="text-gray-500 flex-shrink-0 w-24 truncate">{log.logger || log.module || ''}</span>
            <span className="text-gray-300 flex-1 break-all">{log.message}</span>
          </div>
        ))}
        {filtered.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-500 text-sm gap-2">
            <Terminal size={16} />
            No logs found
          </div>
        )}
      </div>
    </div>
  )
}
