const BASE_URL = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  // Health
  health: () => request('/health'),

  // Chat
  chat: (message, agent = 'orchestrator') =>
    request('/chat', { method: 'POST', body: JSON.stringify({ message, agent }) }),

  // Agents
  listAgents: () => request('/agents'),
  getAgent: (name) => request(`/agents/${name}`),

  // Tasks
  createTask: (prompt, agent = 'orchestrator') =>
    request('/tasks', { method: 'POST', body: JSON.stringify({ prompt, agent }) }),
  listTasks: (limit = 20) => request(`/tasks?limit=${limit}`),
  getTask: (id) => request(`/tasks/${id}`),
  cancelTask: (id) => request(`/tasks/${id}`, { method: 'DELETE' }),

  // Memory
  storeMemory: (text, collection = 'long_term', metadata = null) =>
    request('/memory', { method: 'POST', body: JSON.stringify({ text, collection, metadata }) }),
  queryMemory: (query, collection = 'long_term', n_results = 5) =>
    request('/memory/query', { method: 'POST', body: JSON.stringify({ query, collection, n_results }) }),
  listMemory: () => request('/memory'),
  clearMemory: (collection) => request(`/memory/${collection}`, { method: 'DELETE' }),

  // Models
  listModels: () => request('/models'),
  switchModel: (modelId) =>
    request(`/models/switch?model_id=${encodeURIComponent(modelId)}`, { method: 'POST' }),

  // Logs
  getLogs: (lines = 100) => request(`/logs?lines=${lines}`),
}

// WebSocket helper
export function createWebSocket(onToken, onEnd, onError) {
  const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws`
  const ws = new WebSocket(wsUrl)

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'token') onToken(data.content)
    else if (data.type === 'end') onEnd(data.content)
    else if (data.error) onError(data.error)
  }

  ws.onerror = () => onError('WebSocket connection failed')
  return ws
}
