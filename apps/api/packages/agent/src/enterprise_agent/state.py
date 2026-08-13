"""Agent state for LangGraph."""

from __future__ import annotations

from typing import Any, TypedDict

from enterprise_domain.enums import IntentType


class AgentState(TypedDict, total=False):
    organization_id: str
    actor_id: str
    conversation_id: str
    run_id: str
    user_message: str
    intent: str
    customer: dict[str, Any]
    order: dict[str, Any]
    shipment: dict[str, Any]
    policy_hits: list[dict[str, Any]]
    delivery_status: dict[str, Any]
    explanation: str
    citations: list[dict[str, Any]]
    proposed_action: dict[str, Any] | None
    validation: dict[str, Any]
    approval_id: str | None
    approval_status: str | None
    action_result: dict[str, Any] | None
    verification: dict[str, Any] | None
    escalation: dict[str, Any] | None
    final_response: str
    events: list[dict[str, Any]]
    pause: bool
    error: str | None
    graph_step: int
    max_steps: int
    authenticated: bool
    tool_gateway: Any
    retriever: Any
    llm: Any


def default_state() -> AgentState:
    return AgentState(
        intent=IntentType.UNKNOWN.value,
        policy_hits=[],
        citations=[],
        proposed_action=None,
        validation={},
        approval_id=None,
        approval_status=None,
        action_result=None,
        verification=None,
        escalation=None,
        final_response="",
        events=[],
        pause=False,
        error=None,
        graph_step=0,
        max_steps=8,
        authenticated=False,
    )
