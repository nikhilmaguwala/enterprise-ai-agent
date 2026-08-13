"""Fake LLM for tests and offline demos."""

from __future__ import annotations

from enterprise_agent.providers.base import LLMMessage, LLMResponse


class FakeLLMProvider:
    name = "fake"

    def __init__(self, scripted: dict[str, str] | None = None) -> None:
        self.scripted = scripted or {}

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 600,
        temperature: float = 0.2,
    ) -> LLMResponse:
        last = messages[-1].content if messages else ""
        for key, value in self.scripted.items():
            if key.lower() in last.lower():
                return LLMResponse(content=value, model="fake", provider=self.name)
        # Intent hints
        lower = last.lower()
        if "address" in lower:
            content = "I can help change the delivery address after approval."
        elif "delay" in lower or "late" in lower:
            content = (
                "Your order is delayed due to a carrier hub exception. "
                "Expected delivery has been updated."
            )
        else:
            content = "I can help with order status, delays, and address changes."
        return LLMResponse(
            content=content[:max_tokens],
            model="fake",
            provider=self.name,
            usage={"prompt_tokens": 10, "completion_tokens": 20},
        )
