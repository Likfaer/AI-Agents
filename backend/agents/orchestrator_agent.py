"""
Orchestrator Agent — routes tasks, handles chat directly.
"""

import json
import logging
import time
from typing import Optional

from backend.agents.base_agent import AgentResult, BaseAgent
from backend.core.lm_studio_client import lm_client, strip_thinking
from backend.core.config import settings

logger = logging.getLogger(__name__)

ROUTING_PROMPT = """You are the AI Platform Orchestrator. Analyze the user request and route it.

Available agents:
- coding: code generation, debugging, refactoring, technical implementation
- research: web search, documentation lookup, information gathering
- file: file creation, editing, reading, directory management
- devops: Docker, deployment, CI/CD, infrastructure
- builder: creating new AI agents, project scaffolding, automation
- chat: greetings, small talk, general conversation, questions about the platform

RULES:
- Greetings, casual questions, small talk → always "chat"
- "Привет", "Как дела", "Ты тут?", "Что умеешь", "Hello" → always "chat"
- Only route to coding/research/file/devops/builder for CONCRETE technical tasks

Respond with ONLY a JSON object, no other text:
{"agent": "<name>", "reason": "<why>", "enhanced_task": "<task for agent>"}"""

CHAT_SYSTEM_PROMPT = """Ты помощник AI-платформы на базе LM Studio. Отвечай кратко и дружелюбно на русском языке.
Твои возможности: генерация кода, веб-поиск, управление файлами, создание проектов, работа с VS Code.
Отвечай сразу без вступлений."""


class OrchestratorAgent(BaseAgent):

    @property
    def name(self) -> str:
        return "Orchestrator"

    @property
    def description(self) -> str:
        return "Routes tasks to specialized agents and manages multi-agent workflows"

    @property
    def system_prompt(self) -> str:
        return "You are the master AI Orchestrator. Coordinate specialized agents."

    async def route(self, task: str) -> dict:
        messages = [
            {"role": "system", "content": ROUTING_PROMPT},
            {"role": "user", "content": task},
        ]
        try:
            # Низкий max_tokens для роутинга — только JSON нужен
            response = await lm_client.chat(
                messages=messages,
                temperature=0.1,
                max_tokens=450,
            )
            content = response.choices[0].message.content or ""
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(content[start:end])
        except Exception as e:
            logger.error(f"Routing failed: {e}")

        return {"agent": "chat", "reason": "Fallback", "enhanced_task": task}

    async def _handle_chat(self, task: str, task_id: str = "chat") -> AgentResult:
        """Handle small talk directly without tool loop."""
        start = time.time()
        messages = [
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ]
        try:
            response = await lm_client.chat(
                messages=messages,
                temperature=0.7,
                max_tokens=2048,  # достаточно для чата, не огромно
            )
            content = response.choices[0].message.content or ""

            # Если пустой content — проверяем finish_reason
            finish_reason = response.choices[0].finish_reason
            if not content.strip():
                if finish_reason == "length":
                    content = "Ответ был обрезан из-за лимита токенов. Попробуйте ещё раз."
                else:
                    content = "Привет! Чем могу помочь? Я умею писать код, искать информацию, управлять файлами и создавать проекты."

        except Exception as e:
            logger.error(f"Chat handler error: {e}")
            content = f"Произошла ошибка: {e}"

        return AgentResult(
            content=content,
            agent_id=self.agent_id,
            task_id=task_id,
            tools_used=[],
            execution_time=round(time.time() - start, 2),
        )

    async def orchestrate(
        self,
        task: str,
        agent_registry: dict,
        task_id: Optional[str] = None,
    ) -> AgentResult:
        routing = await self.route(task)
        agent_name = routing.get("agent", "chat")
        enhanced_task = routing.get("enhanced_task", task)

        logger.info(f"Routing to '{agent_name}': {routing.get('reason', '')}")

        # Small talk — обрабатываем здесь, не гоняем через tool loop
        if agent_name == "chat":
            return await self._handle_chat(task, task_id=task_id or "chat")

        agent = agent_registry.get(agent_name) or agent_registry.get("coding")

        if agent:
            result = await agent.run(enhanced_task, task_id=task_id)
            if result.content:
                result.content = f"**[{agent_name.upper()}]**\n\n{result.content}"
            return result

        # Крайний fallback
        return await self._handle_chat(task, task_id=task_id or "chat")
