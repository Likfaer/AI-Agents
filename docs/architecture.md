# Architecture Overview

## Core Design Principles

1. **Modularity** — каждый агент и tool независимы и заменяемы
2. **Async-first** — весь код асинхронный (asyncio + FastAPI)
3. **Tool calling loop** — агенты работают в петле до достижения результата
4. **Separation of concerns** — agents, tools, memory, API разделены

## Agent Tool Calling Loop

```
User Request
     │
     ▼
BaseAgent.run(task)
     │
     ├─► Build messages (system + history + task)
     │
     ▼
LM Studio API (chat completion with tools)
     │
     ├─► [No tool calls] ──► Return final answer
     │
     └─► [Tool calls] ──► Execute tools in parallel
                               │
                               ▼
                         Append tool results to messages
                               │
                               ▼
                         Loop back to LM Studio API
                         (max_iterations=10)
```

## Memory Architecture

```
MemoryManager
├── JSONMemoryStore (always available)
│   ├── long_term.json
│   ├── short_term.json
│   ├── project.json
│   └── agent_*.json
└── ChromaDB (optional, for vector search)
    └── Embeddings for semantic recall
```

## Request Flow

```
Browser ──HTTP──► FastAPI ──► AgentRegistry
                                  │
                              route to agent
                                  │
                              BaseAgent.run()
                                  │
                          ┌───────┴───────┐
                          │               │
                    LM Studio API    Tool Execution
                          │               │
                          └───────┬───────┘
                                  │
                              AgentResult
                                  │
                              JSON Response
```

## Security Model

- **Allowlist**: только явно разрешённые команды выполняются
- **Blocklist**: паттерны опасных команд заблокированы
- **Timeout**: каждая команда имеет максимальное время выполнения
- **Logging**: все вызовы инструментов логируются с полным контекстом
- **Sandboxing**: workspace изолирован от системных директорий
