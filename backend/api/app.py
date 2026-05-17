"""
FastAPI Application — REST API + WebSocket for the AI Platform.
"""

import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core.config import settings
from backend.core.logging_config import setup_logging
from backend.orchestrator.agent_registry import agent_registry
from backend.memory.memory_manager import memory_manager

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LM Studio AI Platform",
    description="Local multi-agent AI platform powered by LM Studio",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── WebSocket connection manager ────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active_connections.remove(ws)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

ws_manager = ConnectionManager()


# ─── Request / Response Models ───────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    agent: str = "orchestrator"
    stream: bool = False

class TaskRequest(BaseModel):
    prompt: str
    agent: str = "orchestrator"

class MemoryRequest(BaseModel):
    text: str
    collection: str = "long_term"
    metadata: Optional[dict] = None

class MemoryQueryRequest(BaseModel):
    query: str
    collection: str = "long_term"
    n_results: int = 5


# ─── Startup ─────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialize all agents on startup."""
    logger.info("Starting LM Studio AI Platform...")
    _init_agents()
    logger.info(f"Platform ready — {len(agent_registry.list_agents())} agents loaded")


def _init_agents():
    """Initialize and register all platform agents."""
    from backend.agents.orchestrator_agent import OrchestratorAgent
    from backend.agents.coding_agent import CodingAgent
    from backend.agents.research_agent import ResearchAgent
    from backend.agents.specialized_agents import FileAgent, DevOpsAgent, BuilderAgent

    orchestrator = OrchestratorAgent()
    coding = CodingAgent()
    research = ResearchAgent()
    file_agent = FileAgent()
    devops = DevOpsAgent()
    builder = BuilderAgent()

    agent_registry.register(orchestrator, "orchestrator")
    agent_registry.register(coding, "coding")
    agent_registry.register(research, "research")
    agent_registry.register(file_agent, "file")
    agent_registry.register(devops, "devops")
    agent_registry.register(builder, "builder")


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    from backend.core.lm_studio_client import lm_client
    lm_ok = await lm_client.health_check()
    return {
        "status": "ok" if lm_ok else "degraded",
        "lm_studio": lm_ok,
        "agents": len(agent_registry.list_agents()),
    }


# ─── Chat ─────────────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat(request: ChatRequest) -> dict:
    """Send a message to an agent and get a response."""
    agent = agent_registry.get(request.agent)
    if not agent:
        raise HTTPException(404, f"Agent '{request.agent}' not found")

    try:
        if request.agent == "orchestrator":
            result = await agent.orchestrate(request.message, agent_registry.get_all())
        else:
            result = await agent.run(request.message)

        response_data = {
            "content": result.content if result else "",
            "agent": request.agent,
            "tools_used": result.tools_used if result else [],
            "execution_time": result.execution_time if result else 0,
            "error": result.error if result else None,
        }

        # Broadcast to WebSocket clients
        await ws_manager.broadcast({"type": "chat_response", "data": response_data})
        return response_data

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(500, str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for streaming chat."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg = data.get("message", "")
            agent_name = data.get("agent", "orchestrator")

            agent = agent_registry.get(agent_name)
            if not agent:
                await websocket.send_json({"error": f"Agent '{agent_name}' not found"})
                continue

            await websocket.send_json({"type": "start", "agent": agent_name})

            # Stream tokens
            full_response = ""
            async for token in agent.stream(msg):
                full_response += token
                await websocket.send_json({"type": "token", "content": token})

            await websocket.send_json({"type": "end", "content": full_response})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ─── Agents ───────────────────────────────────────────────────────────────────

@app.get("/agents")
async def list_agents() -> dict:
    return {"agents": agent_registry.list_agents()}


@app.get("/agents/{agent_name}")
async def get_agent(agent_name: str) -> dict:
    agent = agent_registry.get(agent_name)
    if not agent:
        raise HTTPException(404, f"Agent '{agent_name}' not found")
    return agent.to_dict()


# ─── Tasks ────────────────────────────────────────────────────────────────────

@app.post("/tasks")
async def create_task(request: TaskRequest) -> dict:
    """Submit a task for async execution."""
    task_id = await agent_registry.submit_task(request.prompt, request.agent)
    return {"task_id": task_id, "status": "pending"}


@app.get("/tasks")
async def list_tasks(limit: int = 20) -> dict:
    return {"tasks": agent_registry.list_tasks(limit)}


@app.get("/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    task = agent_registry.get_task(task_id)
    if not task:
        raise HTTPException(404, f"Task '{task_id}' not found")
    return task


@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str) -> dict:
    cancelled = await agent_registry.cancel_task(task_id)
    return {"cancelled": cancelled}


# ─── Memory ───────────────────────────────────────────────────────────────────

@app.post("/memory")
async def store_memory(request: MemoryRequest) -> dict:
    result = await memory_manager.remember(request.text, request.collection, request.metadata)
    return {"result": result}


@app.post("/memory/query")
async def query_memory(request: MemoryQueryRequest) -> dict:
    result = await memory_manager.recall(request.query, request.collection, request.n_results)
    return {"result": result}


@app.get("/memory")
async def list_memory_collections() -> dict:
    result = await memory_manager.list_collections()
    return {"result": result}


@app.delete("/memory/{collection}")
async def clear_memory(collection: str) -> dict:
    result = await memory_manager.clear_collection(collection)
    return {"result": result}


# ─── Models ───────────────────────────────────────────────────────────────────

@app.get("/models")
async def list_models() -> dict:
    from backend.core.lm_studio_client import lm_client
    models = await lm_client.list_models()
    return {"models": models, "current": lm_client.current_model}


@app.post("/models/switch")
async def switch_model(model_id: str) -> dict:
    from backend.core.lm_studio_client import lm_client
    success = await lm_client.switch_model(model_id)
    return {"success": success, "current": lm_client.current_model}


# ─── Logs ─────────────────────────────────────────────────────────────────────

@app.get("/logs")
async def get_logs(lines: int = 100) -> dict:
    import os
    log_file = settings.LOG_FILE
    if not os.path.exists(log_file):
        return {"logs": []}
    with open(log_file, encoding="utf-8") as f:
        all_lines = f.readlines()
    recent = all_lines[-lines:]
    parsed = []
    for line in recent:
        try:
            import json as _json
            parsed.append(_json.loads(line))
        except Exception:
            parsed.append({"message": line.strip()})
    return {"logs": parsed}
