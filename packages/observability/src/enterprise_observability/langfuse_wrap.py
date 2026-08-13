"""Optional Langfuse tracing with safe no-op fallback."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class Tracer(Protocol):
    def start_span(self, name: str, **attrs: Any) -> Any:
        ...

    def end_span(self, span: Any, **attrs: Any) -> None:
        ...


@dataclass
class NullTracer:
    def start_span(self, name: str, **attrs: Any) -> dict[str, Any]:
        return {"name": name, "attrs": attrs}

    def end_span(self, span: Any, **attrs: Any) -> None:
        return None


@dataclass
class LangfuseTracer:
    public_key: str | None
    secret_key: str | None
    host: str = "https://cloud.langfuse.com"
    _client: Any = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.public_key and self.secret_key:
            try:
                from langfuse import Langfuse

                self._client = Langfuse(
                    public_key=self.public_key,
                    secret_key=self.secret_key,
                    host=self.host,
                )
            except Exception:  # noqa: BLE001
                self._client = None

    def start_span(self, name: str, **attrs: Any) -> Any:
        if self._client is None:
            return {"name": name, "attrs": attrs}
        try:
            return self._client.trace(name=name, metadata=attrs)
        except Exception:  # noqa: BLE001
            return {"name": name, "attrs": attrs}

    def end_span(self, span: Any, **attrs: Any) -> None:
        if self._client is None:
            return
        try:
            if hasattr(span, "update"):
                span.update(metadata=attrs)
        except Exception:  # noqa: BLE001
            return
