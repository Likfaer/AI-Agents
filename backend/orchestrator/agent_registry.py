"""
Agent Registry and Task Manager.
Tasks persist to disk (JSON) so they survive backend restarts.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

TASKS_FILE = Path("./data/tasks.json")


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    def __init__(self, task_id: str, prompt: str, agent_name: str):
        self.task_id = task_id
        self.prompt = prompt
        self.agent_name = agent_name
        self.status = TaskStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        result_str = ""
        if self.result is not None:
            if hasattr(self.result, "to_dict"):
                result_str = self.result.to_dict()
            else:
                result_str = str(self.result)

        return {
            "task_id": self.task_id,
            "prompt": self.prompt[:500],
            "agent_name": self.agent_name,
            "status": self.status.value,
            "result": result_str,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        t = cls(data["task_id"], data["prompt"], data["agent_name"])
        t.status = TaskStatus(data.get("status", "completed"))
        t.result = data.get("result")
        t.error = data.get("error")
        t.created_at = data.get("created_at", "")
        t.started_at = data.get("started_at")
        t.completed_at = data.get("completed_at")
        return t


class AgentRegistry:
    """Central registry for all platform agents with persistent task storage."""

    MAX_TASKS_IN_MEMORY = 200   # держим последние N задач в памяти
    MAX_TASKS_ON_DISK = 500     # и N на диске

    def __init__(self):
        self._agents: dict[str, Any] = {}
        self._tasks: dict[str, Task] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._load_tasks_from_disk()

    # ── Persistence ────────────────────────────────────────────────────────

    def _load_tasks_from_disk(self) -> None:
        """Load completed tasks from previous sessions."""
        try:
            TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
            if TASKS_FILE.exists():
                raw = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
                for d in raw[-self.MAX_TASKS_IN_MEMORY:]:
                    t = Task.from_dict(d)
                    self._tasks[t.task_id] = t
                logger.info(f"Loaded {len(self._tasks)} tasks from disk")
        except Exception as e:
            logger.warning(f"Could not load tasks from disk: {e}")

    def _save_tasks_to_disk(self) -> None:
        """Persist completed tasks to JSON."""
        try:
            TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
            completed = [
                t.to_dict() for t in self._tasks.values()
                if t.status not in (TaskStatus.PENDING, TaskStatus.RUNNING)
            ]
            # Оставляем последние MAX_TASKS_ON_DISK
            completed = completed[-self.MAX_TASKS_ON_DISK:]
            TASKS_FILE.write_text(
                json.dumps(completed, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"Could not save tasks: {e}")

    # ── Agent management ────────────────────────────────────────────────────

    def register(self, agent: Any, name: Optional[str] = None) -> str:
        key = name or agent.name.lower().replace(" ", "_").replace("agent", "").strip("_")
        self._agents[key] = agent
        logger.info(f"Registered agent: {key} ({agent.__class__.__name__})")
        return key

    def get(self, name: str) -> Optional[Any]:
        return self._agents.get(name)

    def list_agents(self) -> list[dict]:
        return [agent.to_dict() for agent in self._agents.values()]

    def get_all(self) -> dict:
        return dict(self._agents)

    # ── Task management ─────────────────────────────────────────────────────

    async def submit_task(self, prompt: str, agent_name: str = "orchestrator") -> str:
        task_id = str(uuid.uuid4())[:8]
        task = Task(task_id=task_id, prompt=prompt, agent_name=agent_name)
        self._tasks[task_id] = task

        async_task = asyncio.create_task(self._execute_task(task))
        self._running_tasks[task_id] = async_task
        logger.info(f"Task submitted: {task_id} → {agent_name}")
        return task_id

    async def _execute_task(self, task: Task) -> None:
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc).isoformat()

        agent = self._agents.get(task.agent_name)
        if not agent:
            task.status = TaskStatus.FAILED
            task.error = f"Agent '{task.agent_name}' not found"
            task.completed_at = datetime.now(timezone.utc).isoformat()
            self._save_tasks_to_disk()
            return

        try:
            if task.agent_name == "orchestrator" and hasattr(agent, "orchestrate"):
                result = await agent.orchestrate(task.prompt, self.get_all(), task_id=task.task_id)
            else:
                result = await agent.run(task.prompt, task_id=task.task_id)

            task.result = result
            task.status = TaskStatus.COMPLETED
            logger.info(f"Task {task.task_id} completed")

        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.error = "Cancelled by user"
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Task {task.task_id} failed: {e}")
        finally:
            task.completed_at = datetime.now(timezone.utc).isoformat()
            self._running_tasks.pop(task.task_id, None)
            self._save_tasks_to_disk()  # ← сохраняем после каждой задачи

    async def run_task_sync(self, prompt: str, agent_name: str = "orchestrator") -> Any:
        task_id = await self.submit_task(prompt, agent_name)
        task = self._tasks[task_id]
        while task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            await asyncio.sleep(0.1)
        return task.result

    def get_task(self, task_id: str) -> Optional[dict]:
        task = self._tasks.get(task_id)
        return task.to_dict() if task else None

    def list_tasks(self, limit: int = 50) -> list[dict]:
        # Сортируем: сначала активные, потом по дате создания (новые первыми)
        all_tasks = list(self._tasks.values())
        running = [t for t in all_tasks if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)]
        done = [t for t in all_tasks if t.status not in (TaskStatus.PENDING, TaskStatus.RUNNING)]
        done_sorted = sorted(done, key=lambda t: t.created_at, reverse=True)
        merged = running + done_sorted
        return [t.to_dict() for t in merged[:limit]]

    async def cancel_task(self, task_id: str) -> bool:
        async_task = self._running_tasks.get(task_id)
        if async_task and not async_task.done():
            async_task.cancel()
            task = self._tasks.get(task_id)
            if task:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now(timezone.utc).isoformat()
                self._save_tasks_to_disk()
            return True
        return False


agent_registry = AgentRegistry()
