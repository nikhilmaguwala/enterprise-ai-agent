"""Build LLM providers from Settings-like objects."""

from __future__ import annotations

from typing import Any

from enterprise_agent.providers.base import LLMProvider
from enterprise_agent.providers.fake import FakeLLMProvider
from enterprise_agent.providers.gemini import GeminiLLMProvider
from enterprise_agent.providers.groq_provider import GroqLLMProvider
from enterprise_agent.providers.ollama import OllamaLLMProvider


def build_llm_provider(settings: Any) -> LLMProvider:
    """Select primary LLM provider; empty keys fall back inside providers to Fake."""
    provider = str(
        getattr(settings, "llm_primary_provider", None)
        or getattr(settings, "LLM_PRIMARY_PROVIDER", None)
        or "fake"
    ).lower()

    if provider == "groq":
        return GroqLLMProvider(
            api_key=str(getattr(settings, "groq_api_key", "") or ""),
            model=str(
                getattr(settings, "llm_primary_model", None)
                or "openai/gpt-oss-20b"
            ),
        )
    if provider == "gemini":
        return GeminiLLMProvider(
            api_key=str(getattr(settings, "gemini_api_key", "") or ""),
            model=str(
                getattr(settings, "llm_fallback_model", None)
                or getattr(settings, "llm_primary_model", None)
                or "gemini-2.0-flash"
            ),
        )
    if provider == "ollama":
        return OllamaLLMProvider(
            base_url=str(
                getattr(settings, "ollama_base_url", None) or "http://localhost:11434"
            ),
            model=str(getattr(settings, "ollama_model", None) or "llama3.2"),
        )
    return FakeLLMProvider()
