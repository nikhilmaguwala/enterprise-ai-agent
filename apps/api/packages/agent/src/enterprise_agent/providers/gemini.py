"""Gemini LLM provider (optional fallback — never used silently for mutations)."""

from __future__ import annotations

import httpx

from enterprise_agent.providers.base import LLMMessage, LLMResponse
from enterprise_agent.providers.fake import FakeLLMProvider


class GeminiLLMProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self.api_key = api_key
        self.model = model

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 600,
        temperature: float = 0.2,
    ) -> LLMResponse:
        if not self.api_key:
            return await FakeLLMProvider().complete(
                messages, max_tokens=max_tokens, temperature=temperature
            )
        prompt = "\n".join(f"{m.role}: {m.content}" for m in messages)
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                url,
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": temperature,
                    },
                },
            )
        if response.status_code >= 400:
            return await FakeLLMProvider().complete(
                messages, max_tokens=max_tokens, temperature=temperature
            )
        data = response.json()
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        return LLMResponse(
            content=text,
            model=self.model,
            provider=self.name,
            raw=data,
        )
