"""LangGraph workflow for delayed-order + address-change approval."""

from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, StateGraph

from enterprise_agent import nodes as N
from enterprise_agent.state import AgentState


def route_after_auth(state: AgentState) -> Literal["classify_intent", "stop"]:
    if not state.get("authenticated"):
        return "stop"
    return "classify_intent"


def route_after_validate(
    state: AgentState,
) -> Literal["request_human_approval", "create_escalation", "finalize_response"]:
    validation = state.get("validation") or {}
    route = validation.get("route") or "finalize"
    if route == "approve":
        return "request_human_approval"
    if route == "escalate":
        return "create_escalation"
    return "finalize_response"


def route_after_approval(
    state: AgentState,
) -> Literal["execute_approved_action", "finalize_response"]:
    if state.get("pause") and state.get("approval_status") == "pending":
        return "finalize_response"
    if state.get("approval_status") == "approved":
        return "execute_approved_action"
    return "finalize_response"


def build_support_graph() -> Any:
    graph: StateGraph = StateGraph(AgentState)

    graph.add_node("authenticate_and_load_context", N.authenticate_and_load_context)
    graph.add_node("classify_intent", N.classify_intent)
    graph.add_node("load_customer", N.load_customer)
    graph.add_node("load_order", N.load_order)
    graph.add_node("retrieve_policy", N.retrieve_policy)
    graph.add_node("check_delivery", N.check_delivery)
    graph.add_node("compose_grounded_explanation", N.compose_grounded_explanation)
    graph.add_node("validate_proposed_action", N.validate_proposed_action)
    graph.add_node("request_human_approval", N.request_human_approval)
    graph.add_node("execute_approved_action", N.execute_approved_action)
    graph.add_node("verify_action_result", N.verify_action_result)
    graph.add_node("create_escalation", N.create_escalation)
    graph.add_node("finalize_response", N.finalize_response)

    graph.set_entry_point("authenticate_and_load_context")
    graph.add_conditional_edges(
        "authenticate_and_load_context",
        route_after_auth,
        {"classify_intent": "classify_intent", "stop": "finalize_response"},
    )
    graph.add_edge("classify_intent", "load_customer")
    graph.add_edge("load_customer", "load_order")
    graph.add_edge("load_order", "retrieve_policy")
    graph.add_edge("retrieve_policy", "check_delivery")
    graph.add_edge("check_delivery", "compose_grounded_explanation")
    graph.add_edge("compose_grounded_explanation", "validate_proposed_action")
    graph.add_conditional_edges(
        "validate_proposed_action",
        route_after_validate,
        {
            "request_human_approval": "request_human_approval",
            "create_escalation": "create_escalation",
            "finalize_response": "finalize_response",
        },
    )
    graph.add_conditional_edges(
        "request_human_approval",
        route_after_approval,
        {
            "execute_approved_action": "execute_approved_action",
            "finalize_response": "finalize_response",
        },
    )
    graph.add_edge("execute_approved_action", "verify_action_result")
    graph.add_edge("verify_action_result", "finalize_response")
    graph.add_edge("create_escalation", "finalize_response")
    graph.add_edge("finalize_response", END)

    return graph.compile()
