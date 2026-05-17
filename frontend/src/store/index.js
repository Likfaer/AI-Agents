import { create } from 'zustand'

export const useStore = create((set) => ({
  // Chat
  messages: [],
  selectedAgent: 'orchestrator',
  isLoading: false,

  addMessage: (msg) => set(s => ({ messages: [...s.messages, msg] })),
  clearMessages: () => set({ messages: [] }),
  setAgent: (agent) => set({ selectedAgent: agent }),
  setLoading: (loading) => set({ isLoading: loading }),

  // FIXED: принимает объект с полями и мёржит их в последнее сообщение
  // раньше весь объект записывался в поле content
  updateLastMessage: (fields) => set(s => {
    const msgs = [...s.messages]
    if (msgs.length > 0) {
      const last = msgs[msgs.length - 1]
      // Если content — строка, обрезаем пробелы и \n в начале/конце
      const cleaned = typeof fields.content === 'string'
        ? fields.content.trim()
        : fields.content
      msgs[msgs.length - 1] = { ...last, ...fields, content: cleaned }
    }
    return { messages: msgs }
  }),

  // Agents
  agents: [],
  setAgents: (agents) => set({ agents }),

  // Tasks
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set(s => ({ tasks: [task, ...s.tasks] })),
  updateTask: (taskId, data) => set(s => ({
    tasks: s.tasks.map(t => t.task_id === taskId ? { ...t, ...data } : t),
  })),

  // Logs
  logs: [],
  setLogs: (logs) => set({ logs }),

  // Health
  health: null,
  setHealth: (health) => set({ health }),

  // Models
  models: [],
  currentModel: '',
  setModels: (models, current) => set({ models, currentModel: current }),
}))
