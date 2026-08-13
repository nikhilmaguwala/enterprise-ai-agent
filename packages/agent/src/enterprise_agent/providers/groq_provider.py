"""Groq LLM provider."""

from __future__ import annotations

from enterprise_agent.providers.base import LLMMessage, LLMResponse


class GroqLLMProvider:
    name = "groq"

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-20b") -> None:
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
            from enterprise_agent.providers.fake import FakeLLMProvider

            return await FakeLLMProvider().complete(
                messages, max_tokens=max_tokens, temperature=temperature
            )
        try:
            from groq import AsyncGroq
        except ImportError:
            from enterprise_agent.providers.fake import FakeLLMProvider

            return await FakeLLMProvider().complete(
                messages, max_tokens=max_tokens, temperature=temperature
            )

        client = AsyncGroq(api_key=self.api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        choice = response.choices[0].message.content or ""
        usage = {
            "prompt_tokens": getattr(response.usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(response.usage, "completion_tokens", 0) or 0,
        }
        return LLMResponse(
            content=choice,
            model=self.model,
            provider=self.name,
            usage=usage,
            raw={"id": getattr(response, "id", None)},
        )
