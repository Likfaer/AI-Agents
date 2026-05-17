"""
LM Studio Client — OpenAI-compatible API.
Handles Qwen3/reasoning models:
- reasoning_content field (separate from content)
- <think> tags in content (fallback)
- finish_reason: length detection
"""

import asyncio
import logging
import re
from typing import Any, AsyncGenerator, Optional

import httpx
from openai import AsyncOpenAI

from backend.core.config import settings

logger = logging.getLogger(__name__)

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def strip_thinking(text: str) -> str:
    """Remove <think>...</think> tags if present in content."""
    if not text:
        return text
    cleaned = _THINK_RE.sub("", text)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_clean_content(message: Any) -> str:
    """
    Extract clean response from LM Studio message.
    
    Qwen3 in LM Studio sends reasoning separately in `reasoning_content`.
    The `content` field should already be clean — but if finish_reason=length
    or the model leaked thinking into content, we clean it up.
    """
    # Получаем основной контент
    content = getattr(message, "content", "") or ""
    
    # Убираем <think> теги если они попали в content (fallback)
    content = strip_thinking(content)
    
    return content.strip()


class LMStudioClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.LM_STUDIO_BASE_URL,
            api_key=settings.LM_STUDIO_API_KEY,
            timeout=httpx.Timeout(settings.LM_STUDIO_TIMEOUT),
        )
        self.current_model = settings.DEFAULT_MODEL

    async def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 16384,
        stream: bool = False,
    ) -> Any:
        model = model or self.current_model

        for attempt in range(settings.MAX_RETRIES):
            try:
                kwargs: dict[str, Any] = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": stream,
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = await self.client.chat.completions.create(**kwargs)

                # Очищаем content от утечек thinking
                if response.choices:
                    choice = response.choices[0]
                    if choice.message.content:
                        choice.message.content = extract_clean_content(choice.message)
                    
                    # Логируем если модель обрезалась
                    if choice.finish_reason == "length":
                        logger.warning(
                            f"Response truncated (finish_reason=length), "
                            f"max_tokens={max_tokens}. Consider increasing max_tokens."
                        )

                return response

            except Exception as e:
                logger.warning(f"LM Studio attempt {attempt + 1} failed: {e}")
                if attempt == settings.MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def stream_chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 16384,
    ) -> AsyncGenerator[str, None]:
        model = model or self.current_model
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        inside_think = False
        buffer = ""

        async with self.client.chat.completions.stream(**kwargs) as stream:  # type: ignore
            async for chunk in stream:
                if not (chunk.choices and chunk.choices[0].delta.content):
                    continue
                token = chunk.choices[0].delta.content
                buffer += token

                if not inside_think and "<think>" in buffer.lower():
                    inside_think = True
                    before = re.split(r"<think>", buffer, flags=re.IGNORECASE)[0]
                    if before:
                        yield before
                    buffer = ""
                    continue

                if inside_think and "</think>" in buffer.lower():
                    inside_think = False
                    after = re.split(r"</think>", buffer, flags=re.IGNORECASE)[-1]
                    buffer = after
                    continue

                if inside_think:
                    buffer = ""
                    continue

                if len(buffer) > 15:
                    yield buffer
                    buffer = ""

        if buffer and not inside_think:
            yield buffer

    async def list_models(self) -> list[str]:
        try:
            models = await self.client.models.list()
            return [m.id for m in models.data]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return [self.current_model]

    async def switch_model(self, model_id: str) -> bool:
        available = await self.list_models()
        if model_id in available:
            self.current_model = model_id
            logger.info(f"Switched to model: {model_id}")
            return True
        logger.warning(f"Model {model_id} not available")
        return False

    async def health_check(self) -> bool:
        try:
            await self.list_models()
            return True
        except Exception:
            return False


lm_client = LMStudioClient()
