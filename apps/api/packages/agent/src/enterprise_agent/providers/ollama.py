"""Ollama local LLM provider."""

from __future__ import annotations

import httpx

from enterprise_agent.providers.base import LLMMessage, LLMResponse
from enterprise_agent.providers.fake import FakeLLMProvider


class OllamaLLMProvider:
    name = "ollama"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 600,
        temperature: float = 0.2,
    ) -> LLMResponse:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": m.role, "content": m.content} for m in messages
                        ],
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens,
                        },
                    },
                )
            if response.status_code >= 400:
                return await FakeLLMProvider().complete(
                    messages, max_tokens=max_tokens, temperature=temperature
                )
            data = response.json()
            content = data.get("message", {}).get("content", "")
            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.name,
                raw=data,
            )
        except Exception:  # noqa: BLE001
            return await FakeLLMProvider().complete(
                messages, max_tokens=max_tokens, temperature=temperature
            )
