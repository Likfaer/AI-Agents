# 🚀 LM Studio AI Platform

Полноценная локальная multi-agent AI платформа на базе LM Studio. Автономная система агентов, которая работает **полностью локально** — никакие данные не покидают ваш компьютер.

---

## ✨ Возможности

| Возможность | Описание |
|---|---|
| 🤖 **Multi-agent система** | 6 специализированных агентов + Orchestrator |
| 💻 **Генерация кода** | Любые языки, полные реализации, тесты |
| 🔍 **Веб-поиск** | DuckDuckGo + scraping страниц |
| 📁 **Файловая система** | Создание, чтение, редактирование файлов |
| 🖥️ **VS Code интеграция** | Открытие проектов, создание структур |
| ⚡ **Terminal** | Безопасное выполнение команд в sandbox |
| 🧠 **Память агентов** | ChromaDB + JSON fallback |
| 🌐 **React UI** | Dark mode, WebSocket streaming |
| 🐳 **Docker ready** | Полная контейнеризация |

---

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────┐
│                    React Frontend                    │
│         Chat │ Agents │ Tasks │ Memory │ Logs        │
└──────────────────────┬──────────────────────────────┘
                       │ REST / WebSocket
┌──────────────────────▼──────────────────────────────┐
│                   FastAPI Backend                    │
│  /chat  /agents  /tasks  /memory  /models  /logs     │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│               Orchestrator Agent                     │
│          (routes tasks to right agent)               │
└──┬──────────┬──────────┬──────────┬──────────┬──────┘
   │          │          │          │          │
┌──▼──┐  ┌───▼───┐ ┌────▼───┐ ┌───▼───┐ ┌───▼────┐
│Coding│  │Research│ │  File  │ │DevOps │ │Builder │
│Agent │  │ Agent  │ │ Agent  │ │ Agent │ │ Agent  │
└──┬──┘  └───┬───┘ └────┬───┘ └───┬───┘ └───┬────┘
   │          │          │          │          │
┌──▼──────────▼──────────▼──────────▼──────────▼──────┐
│                     Tool System                      │
│  web_search │ terminal │ file │ vscode │ code_analysis│
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              LM Studio (OpenAI API)                  │
│              http://localhost:1234/v1                │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Быстрый старт

### Требования

- **Python 3.12+**
- **Node.js 20+**
- LM Studio
- Docker (опционально)

### 1. Настройка LM Studio

1. Откройте LM Studio
2. Загрузите любую модель (рекомендуется: `Llama 3.1 8B Instruct` или `Mistral 7B`)
3. Перейдите в **Local Server** → нажмите **Start Server**
4. Убедитесь, что сервер доступен: `http://localhost:1234/v1`

### 2. Установка

```bash
# Клонировать проект
git clone <repo-url>
cd lm-studio-ai-platform

# Скопировать конфиг
cp .env.example .env
# Отредактируйте .env — укажите имя вашей модели в DEFAULT_MODEL

# Установить backend зависимости
cd backend
pip install -r requirements.txt
cd ..

# Установить frontend зависимости
cd frontend
npm install
cd ..
```

### 3. Запуск (разработка)

**Terminal 1 — Backend:**
```bash
python -m backend.main
# API доступно на http://localhost:8000
# Документация: http://localhost:8000/docs
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
# UI доступно на http://localhost:5173
```

### 4. Запуск через Docker

```bash
# Скопировать и настроить .env
cp .env.example .env

# Запустить всё
docker-compose up --build

# UI: http://localhost:3000
# API: http://localhost:8000
```

---

## 🤖 Агенты

### Orchestrator Agent
Главный агент — анализирует запрос и автоматически направляет его к нужному специалисту.

### Coding Agent
Генерирует, отлаживает и рефакторит код. Умеет запускать файлы и тесты через terminal.
```
"Напиши FastAPI сервер с JWT аутентификацией"
"Исправь ошибку в этом Python коде"
"Напиши unit тесты для этого класса"
```

### Research Agent
Ищет в интернете, анализирует документацию, сравнивает технологии.
```
"Найди примеры использования LangGraph"
"Что нового в Python 3.13?"
"Сравни FastAPI и Django REST Framework"
```

### File Agent
Управляет файлами и директориями, открывает проекты в VS Code.
```
"Создай структуру проекта для микросервиса"
"Прочитай все .py файлы в директории src/"
"Открой проект в VS Code"
```

### DevOps Agent
Docker, CI/CD, deployment конфигурации.
```
"Создай Dockerfile для Python приложения"
"Настрой GitHub Actions для автодеплоя"
"Напиши docker-compose для микросервисов"
```

### Builder Agent
Создаёт новых агентов и scaffolding для проектов.
```
"Создай нового агента для работы с базами данных"
"Сгенерируй шаблон FastAPI проекта"
"Создай новый инструмент для парсинга PDF"
```

---

## 🛠️ Tool System

| Tool | Описание |
|---|---|
| `web_search` | DuckDuckGo поиск + извлечение текста страниц |
| `terminal` | Безопасное выполнение команд (sandbox) |
| `file` | Чтение/запись/удаление/поиск файлов |
| `vscode` | Открытие проектов и файлов в VS Code |
| `code_analysis` | Статический анализ кода, поиск проблем |
| `project_generator` | Scaffolding: fastapi, react, python-lib |
| `memory` | Хранение и поиск информации |

---

## 🔒 Безопасность

- **Command sandbox**: только разрешённые команды (whitelist)
- **Blocklist**: опасные паттерны заблокированы (`rm -rf /`, fork bomb и др.)
- **Таймаут**: все команды ограничены по времени (30 сек по умолчанию)
- **Filesystem**: операции логируются

Список разрешённых команд (`.env`):
```
ALLOWED_COMMANDS=python,pip,npm,node,git,ls,cat,echo,mkdir,touch,cp,mv,find,grep,curl,docker,uvicorn,pytest
```

---

## 📡 API Reference

| Endpoint | Метод | Описание |
|---|---|---|
| `/health` | GET | Статус системы |
| `/chat` | POST | Отправить сообщение агенту |
| `/ws` | WS | WebSocket стриминг |
| `/agents` | GET | Список всех агентов |
| `/agents/{name}` | GET | Информация об агенте |
| `/tasks` | POST | Создать асинхронную задачу |
| `/tasks` | GET | Список задач |
| `/tasks/{id}` | GET | Статус задачи |
| `/tasks/{id}` | DELETE | Отменить задачу |
| `/memory` | POST | Сохранить в память |
| `/memory/query` | POST | Поиск по памяти |
| `/memory` | GET | Список коллекций |
| `/memory/{col}` | DELETE | Очистить коллекцию |
| `/models` | GET | Список моделей LM Studio |
| `/models/switch` | POST | Сменить модель |
| `/logs` | GET | Просмотр логов |

Полная документация: `http://localhost:8000/docs`

---

## 🧪 Тесты

```bash
# Все тесты
pytest

# Только unit тесты
pytest tests/unit/

# Только integration тесты
pytest tests/integration/

# С покрытием
pytest --cov=backend --cov-report=html
```

---

## 📁 Структура проекта

```
lm-studio-ai-platform/
├── backend/
│   ├── agents/
│   │   ├── base_agent.py          # Базовый класс всех агентов
│   │   ├── orchestrator_agent.py  # Роутинг задач
│   │   ├── coding_agent.py        # Генерация кода
│   │   ├── research_agent.py      # Веб-поиск
│   │   └── specialized_agents.py  # File, DevOps, Builder
│   ├── tools/
│   │   ├── web_search_tool.py     # DuckDuckGo + scraping
│   │   ├── terminal_tool.py       # Sandbox выполнение команд
│   │   ├── file_tool.py           # Файловые операции
│   │   ├── vscode_tool.py         # VS Code интеграция
│   │   ├── code_analysis_tool.py  # Статический анализ
│   │   └── project_generator_tool.py # Scaffolding
│   ├── memory/
│   │   └── memory_manager.py      # ChromaDB + JSON fallback
│   ├── orchestrator/
│   │   └── agent_registry.py      # Реестр агентов и задач
│   ├── core/
│   │   ├── config.py              # Pydantic Settings
│   │   ├── lm_studio_client.py    # OpenAI-совместимый клиент
│   │   └── logging_config.py      # Структурированное логирование
│   ├── api/
│   │   └── app.py                 # FastAPI приложение
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── ChatPage.jsx       # Чат с агентами
│       │   └── index.jsx          # Agents, Tasks, Memory, Logs
│       ├── services/api.js        # REST клиент
│       ├── store/index.js         # Zustand store
│       ├── App.jsx
│       └── main.jsx
├── tests/
│   ├── unit/test_tools.py         # Unit тесты инструментов
│   └── integration/test_api.py   # API интеграционные тесты
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## ⚙️ Конфигурация

Все настройки через `.env` файл:

```env
# Основное
LM_STUDIO_BASE_URL=http://localhost:1234/v1
DEFAULT_MODEL=local-model          # Имя модели из LM Studio
LM_STUDIO_TIMEOUT=120.0

# Безопасность
ENABLE_SANDBOX=true
COMMAND_TIMEOUT=30

# Память
MEMORY_DIR=./data/memory

# Логирование
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR
```

---

## 🔧 Расширение платформы

### Добавить нового агента

```python
# backend/agents/my_agent.py
from backend.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "My Agent"

    @property
    def description(self) -> str:
        return "Does something specific"

    @property
    def system_prompt(self) -> str:
        return "You are a specialized AI that..."
```

Зарегистрировать в `backend/api/app.py`:
```python
from backend.agents.my_agent import MyAgent
agent_registry.register(MyAgent(), "my_agent")
```

### Добавить новый tool

```python
class MyTool:
    async def my_function(self, param: str) -> str:
        # логика
        return result

# Зарегистрировать в агенте:
self.register_tool(my_tool.my_function, {
    "type": "function",
    "function": {
        "name": "my_function",
        "description": "What this tool does",
        "parameters": {
            "type": "object",
            "properties": {"param": {"type": "string"}},
            "required": ["param"],
        },
    },
})
```

---

## 📜 Лицензия

MIT License — используйте и модифицируйте свободно.
