"""Graph routing unit tests."""

from __future__ import annotations

from enterprise_agent.graph import route_after_auth, route_after_validate
from enterprise_agent.state import AgentState


def test_route_after_auth_stops_when_unauthenticated() -> None:
    state: AgentState = {"authenticated": False}
    assert route_after_auth(state) == "stop"


def test_route_after_validate_approve() -> None:
    state: AgentState = {"validation": {"route": "approve"}}
    assert route_after_validate(state) == "request_human_approval"


def test_route_after_validate_escalate() -> None:
    state: AgentState = {"validation": {"route": "escalate"}}
    assert route_after_validate(state) == "create_escalation"
