"""
Base Agent class — all agents inherit from this.
Handles tool calling loop, memory, streaming.
Includes early-stop on repeated errors and <think> stripping.
"""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Optional

from backend.core.lm_studio_client import lm_client, strip_thinking
from backend.core.config import settings

logger = logging.getLogger(__name__)


class AgentResult:
    def __init__(
        self,
        content: str,
        agent_id: str,
        task_id: str,
        tools_used: list[str],
        execution_time: float,
        error: Optional[str] = None,
    ):
        self.content = content
        self.agent_id = agent_id
        self.task_id = task_id
        self.tools_used = tools_used
        self.execution_time = execution_time
        self.error = error
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "tools_used": self.tools_used,
            "execution_time": self.execution_time,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class BaseAgent(ABC):
    """Abstract base for all platform agents."""

    def __init__(
        self,
        agent_id: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.6,
        max_iterations: int = 8,
    ):
        self.agent_id = agent_id or str(uuid.uuid4())[:8]
        self.model = model or settings.DEFAULT_MODEL
        self.temperature = temperature
        self.max_iterations = max_iterations
        self.messages: list[dict] = []
        self._tools: dict[str, Any] = {}
        self._tool_schemas: list[dict] = []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}.{self.agent_id}")

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...

    def register_tool(self, tool_fn: Any, schema: dict) -> None:
        self._tools[schema["function"]["name"]] = tool_fn
        self._tool_schemas.append(schema)

    def _build_messages(self, user_input: str) -> list[dict]:
        msgs = [{"role": "system", "content": self.system_prompt}]
        # Ограничиваем историю последними 10 сообщениями чтобы не раздувать контекст
        msgs.extend(self.messages[-10:])
        msgs.append({"role": "user", "content": user_input})
        return msgs

    async def _execute_tool_call(self, tool_name: str, tool_args: dict) -> str:
        if tool_name not in self._tools:
            return f"Error: unknown tool '{tool_name}'"
        try:
            tool_fn = self._tools[tool_name]
            self.logger.info(f"Executing tool: {tool_name} args={tool_args}")
            if asyncio.iscoroutinefunction(tool_fn):
                result = await tool_fn(**tool_args)
            else:
                result = tool_fn(**tool_args)
            return str(result) if not isinstance(result, str) else result
        except Exception as e:
            self.logger.error(f"Tool {tool_name} failed: {e}")
            return f"Tool error: {e}"

    async def run(self, task: str, task_id: Optional[str] = None) -> AgentResult:
        """Execute agent task with tool calling loop and early-stop on errors."""
        task_id = task_id or str(uuid.uuid4())[:8]
        start = asyncio.get_event_loop().time()
        tools_used: list[str] = []
        consecutive_errors = 0       # счётчик ошибок подряд
        last_tool_calls: list[str] = []  # для детектирования зацикливания

        self.logger.info(f"Starting task={task_id}: {task[:120]}")
        messages = self._build_messages(task)

        for iteration in range(self.max_iterations):
            try:
                response = await lm_client.chat(
                    messages=messages,
                    model=self.model,
                    tools=self._tool_schemas or None,
                    temperature=self.temperature,
                )

                choice = response.choices[0]
                msg = choice.message

                # Строим assistant сообщение для истории
                assistant_msg: dict[str, Any] = {
                    "role": "assistant",
                    "content": msg.content or "",
                }
                if msg.tool_calls:
                    assistant_msg["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ]
                messages.append(assistant_msg)

                # Нет tool calls → финальный ответ
                if not msg.tool_calls:
                    final = strip_thinking(msg.content or "")
                    elapsed = asyncio.get_event_loop().time() - start
                    self.messages.append({"role": "user", "content": task})
                    self.messages.append({"role": "assistant", "content": final})
                    return AgentResult(
                        content=final,
                        agent_id=self.agent_id,
                        task_id=task_id,
                        tools_used=tools_used,
                        execution_time=round(elapsed, 2),
                    )

                # Проверяем зацикливание: если те же инструменты вызываются 3+ раз подряд
                current_calls = [tc.function.name for tc in msg.tool_calls]
                if current_calls == last_tool_calls:
                    consecutive_errors += 1
                    if consecutive_errors >= 3:
                        self.logger.warning(f"Tool loop detected after {iteration} iterations, stopping")
                        elapsed = asyncio.get_event_loop().time() - start
                        return AgentResult(
                            content="Не удалось выполнить задачу: агент зациклился на одних и тех же вызовах инструментов. Попробуйте переформулировать запрос.",
                            agent_id=self.agent_id,
                            task_id=task_id,
                            tools_used=tools_used,
                            execution_time=round(elapsed, 2),
                            error="Tool loop detected",
                        )
                else:
                    consecutive_errors = 0
                last_tool_calls = current_calls

                # Выполняем все tool calls
                for tool_call in msg.tool_calls:
                    fn_name = tool_call.function.name
                    try:
                        fn_args = json.loads(tool_call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        fn_args = {}

                    tools_used.append(fn_name)
                    result = await self._execute_tool_call(fn_name, fn_args)

                    # Если tool вернул ошибку — увеличиваем счётчик
                    if result.startswith("[ERROR]") or result.startswith("[BLOCKED]") or result.startswith("[TIMEOUT]"):
                        consecutive_errors += 1
                        self.logger.warning(f"Tool error #{consecutive_errors}: {result[:100]}")
                        if consecutive_errors >= 3:
                            self.logger.warning("Too many consecutive tool errors, stopping")
                            elapsed = asyncio.get_event_loop().time() - start
                            return AgentResult(
                                content=f"Выполнение остановлено из-за повторяющихся ошибок инструментов.\nПоследняя ошибка: {result}",
                                agent_id=self.agent_id,
                                task_id=task_id,
                                tools_used=tools_used,
                                execution_time=round(elapsed, 2),
                                error=result,
                            )

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })

            except Exception as e:
                self.logger.error(f"Agent iteration {iteration} error: {e}")
                consecutive_errors += 1
                if consecutive_errors >= 3:
                    elapsed = asyncio.get_event_loop().time() - start
                    return AgentResult(
                        content="",
                        agent_id=self.agent_id,
                        task_id=task_id,
                        tools_used=tools_used,
                        execution_time=round(elapsed, 2),
                        error=str(e),
                    )

        elapsed = asyncio.get_event_loop().time() - start
        return AgentResult(
            content="Достигнут лимит итераций без финального ответа.",
            agent_id=self.agent_id,
            task_id=task_id,
            tools_used=tools_used,
            execution_time=round(elapsed, 2),
        )

    async def stream(self, task: str) -> AsyncGenerator[str, None]:
        """Stream agent response (no tool calling), with <think> filtering."""
        messages = self._build_messages(task)
        async for token in lm_client.stream_chat(messages=messages, model=self.model):
            yield token

    def reset_memory(self) -> None:
        self.messages = []

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "tools": list(self._tools.keys()),
        }
