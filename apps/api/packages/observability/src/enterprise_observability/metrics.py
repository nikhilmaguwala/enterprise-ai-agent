"""Prometheus metric helpers."""

from __future__ import annotations

from contextlib import contextmanager
from time import perf_counter
from typing import Iterator

from prometheus_client import Counter, Histogram

MODEL_CALLS = Counter(
    "enterprise_ai_model_calls_total",
    "LLM model calls",
    ["provider", "model", "outcome"],
)
TOOL_CALLS = Counter(
    "enterprise_ai_tool_calls_total",
    "Integration tool calls",
    ["tool", "outcome"],
)
AGENT_RUNS = Counter(
    "enterprise_ai_agent_runs_total",
    "Agent runs",
    ["status"],
)
LATENCY = Histogram(
    "enterprise_ai_operation_latency_seconds",
    "Operation latency",
    ["operation"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30),
)


@contextmanager
def observe_latency(operation: str) -> Iterator[None]:
    start = perf_counter()
    try:
        yield
    finally:
        LATENCY.labels(operation=operation).observe(perf_counter() - start)
