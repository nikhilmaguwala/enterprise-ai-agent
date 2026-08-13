"""LangGraph node implementations for the support agent."""

from __future__ import annotations

import re
from typing import Any
from uuid import uuid4

from enterprise_domain.enums import IntentType
from enterprise_domain.policy import evaluate_address_change
from enterprise_agent.providers.base import LLMMessage
from enterprise_agent.state import AgentState


def _event(state: AgentState, typ: str, payload: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    events = list(state.get("events") or [])
    events.append({"type": typ, "payload": payload or {}})
    return events


async def authenticate_and_load_context(state: AgentState) -> AgentState:
    if not state.get("organization_id") or not state.get("actor_id"):
        return {
            **state,
            "authenticated": False,
            "error": "missing_tenant_context",
            "events": _event(state, "auth_failed"),
            "final_response": "Authentication failed.",
        }
    return {
        **state,
        "authenticated": True,
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(state, "auth_ok"),
    }


async def classify_intent(state: AgentState) -> AgentState:
    msg = (state.get("user_message") or "").lower()
    intent = IntentType.UNKNOWN
    if any(w in msg for w in ("address", "shipping address", "change address")):
        intent = IntentType.ADDRESS_CHANGE
    elif any(w in msg for w in ("delay", "late", "where is", "tracking", "shipment")):
        intent = IntentType.DELAY_EXPLANATION
    elif any(w in msg for w in ("order", "status")):
        intent = IntentType.ORDER_STATUS
    elif any(w in msg for w in ("policy", "refund", "return")):
        intent = IntentType.POLICY_QUESTION
    return {
        **state,
        "intent": intent.value,
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(state, "intent_classified", {"intent": intent.value}),
    }


def _extract_order_number(text: str) -> str | None:
    match = re.search(r"\b([A-Z]{2,3}-\d{4,})\b", text.upper())
    return match.group(1) if match else None


async def load_customer(state: AgentState) -> AgentState:
    gateway = state.get("tool_gateway")
    customer = dict(state.get("customer") or {})
    if gateway and not customer:
        email = (state.get("customer") or {}).get("email")
        if email:
            result = await gateway.call("crm.find_customer_by_email", email=email)
            if result.ok:
                customer = result.data
    return {
        **state,
        "customer": customer,
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(state, "customer_loaded", {"customer_id": customer.get("id")}),
    }


async def load_order(state: AgentState) -> AgentState:
    gateway = state.get("tool_gateway")
    order = dict(state.get("order") or {})
    order_number = order.get("order_number") or _extract_order_number(
        state.get("user_message") or ""
    )
    if gateway and order_number and not order.get("id"):
        result = await gateway.call("erp.get_order_by_number", order_number=order_number)
        if result.ok:
            order = result.data
    elif gateway and order.get("id") and not order.get("status"):
        result = await gateway.call("erp.get_order", order_id=str(order["id"]))
        if result.ok:
            order = result.data
    return {
        **state,
        "order": order,
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(state, "order_loaded", {"order_id": order.get("id")}),
    }


async def retrieve_policy(state: AgentState) -> AgentState:
    retriever = state.get("retriever")
    hits: list[dict[str, Any]] = []
    query = state.get("user_message") or "shipping delay address change policy"
    if retriever and state.get("organization_id"):
        try:
            results = await retriever.retrieve(
                organization_id=str(state["organization_id"]),
                query=query,
                limit=5,
            )
            hits = [
                {
                    "chunk_id": h.chunk_id,
                    "document_id": h.document_id,
                    "content": h.content,
                    "score": h.score,
                }
                for h in results
            ]
        except Exception:  # noqa: BLE001 — never fail the graph on retrieval alone
            hits = []
    if not hits:
        hits = [
            {
                "chunk_id": "policy-default",
                "document_id": "policy-address-change-v1",
                "content": (
                    "Address changes require human approval and are blocked once "
                    "a shipment is out for delivery or delivered."
                ),
                "score": 1.0,
            },
            {
                "chunk_id": "policy-delay-default",
                "document_id": "policy-shipping-delay-v1",
                "content": (
                    "Orders may be delayed due to carrier hub exceptions, weather, "
                    "or capacity constraints. Customers receive updated ETAs when "
                    "carrier status is delayed."
                ),
                "score": 0.95,
            },
        ]
    return {
        **state,
        "policy_hits": hits,
        "citations": [
            {"source": h["document_id"], "excerpt": h["content"][:240], "score": h.get("score")}
            for h in hits[:3]
        ],
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(state, "policy_retrieved", {"count": len(hits)}),
    }


async def check_delivery(state: AgentState) -> AgentState:
    gateway = state.get("tool_gateway")
    order = state.get("order") or {}
    shipment = dict(state.get("shipment") or {})
    tracking = shipment.get("tracking_number") or order.get("tracking_number")
    delivery: dict[str, Any] = {"status": shipment.get("status") or order.get("status")}
    if gateway and tracking:
        result = await gateway.call("carrier.get_tracking", tracking_number=str(tracking))
        if result.ok:
            delivery = result.data
            shipment = {**shipment, **result.data}
    return {
        **state,
        "shipment": shipment,
        "delivery_status": delivery,
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(state, "delivery_checked", delivery),
    }


async def compose_grounded_explanation(state: AgentState) -> AgentState:
    llm = state.get("llm")
    order = state.get("order") or {}
    delivery = state.get("delivery_status") or {}
    citations = state.get("citations") or []
    facts = (
        f"Order {order.get('order_number') or order.get('id')} status={order.get('status')}. "
        f"Delivery={delivery.get('status')} reason={delivery.get('delay_reason') or delivery.get('status_detail')}. "
        f"Policy excerpts: {[c.get('excerpt') for c in citations]}"
    )
    if llm:
        try:
            response = await llm.complete(
                [
                    LLMMessage(
                        role="system",
                        content=(
                            "Explain order delays using only provided facts. "
                            "Do not invent policies. Cite sources by document id."
                        ),
                    ),
                    LLMMessage(role="user", content=facts),
                ]
            )
            explanation = response.content
        except Exception:  # noqa: BLE001
            explanation = ""
    else:
        explanation = ""
    if not explanation:
        explanation = (
            f"Order {order.get('order_number', 'unknown')} is currently "
            f"{order.get('status', 'unknown')}. "
            f"Carrier status: {delivery.get('status', 'unknown')}."
        )
        if delivery.get("delay_reason"):
            explanation += f" Delay reason: {delivery['delay_reason']}."
        if citations:
            explanation += " This assessment is grounded in tenant policy excerpts."
    return {
        **state,
        "explanation": explanation,
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(state, "explanation_composed"),
    }


async def validate_proposed_action(state: AgentState) -> AgentState:
    intent = state.get("intent")
    order = state.get("order") or {}
    shipment = state.get("shipment") or {}
    proposed = state.get("proposed_action")

    if intent != IntentType.ADDRESS_CHANGE.value:
        return {
            **state,
            "validation": {"needs_mutation": False, "route": "finalize"},
            "graph_step": int(state.get("graph_step") or 0) + 1,
            "events": _event(state, "validation_skip"),
        }

    if not proposed or proposed.get("type") != "address_change":
        # Demo-friendly: when the user asks to change address without a full payload,
        # propose a deterministic alternate address for explicit approval.
        proposed = {
            "type": "address_change",
            "order_id": order.get("id"),
            "address": {
                "line1": "200 Harbor Road",
                "city": "Oakland",
                "state": "CA",
                "postal_code": "94607",
                "country": "US",
            },
            "source": "agent_proposed_for_approval",
        }

    decision = evaluate_address_change(
        order_status=str(order.get("status") or "shipped"),
        shipment_status=str(shipment.get("status") or order.get("shipment_status") or ""),
        current_address=order.get("shipping_address") or {},
        proposed_address=proposed.get("address") or {},
    )
    validation = {
        "needs_mutation": decision.allowed and decision.requires_approval,
        "allowed": decision.allowed,
        "requires_approval": decision.requires_approval,
        "reason_codes": decision.reason_codes,
        "policy_citations": decision.policy_citations,
        "route": (
            "approve"
            if decision.allowed and decision.requires_approval
            else "escalate"
            if not decision.allowed
            else "finalize"
        ),
    }
    if decision.validated_address:
        proposed = {
            **proposed,
            "address": decision.validated_address.canonical_dict(),
        }
    return {
        **state,
        "proposed_action": proposed,
        "validation": validation,
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(state, "action_validated", validation),
    }


async def request_human_approval(state: AgentState) -> AgentState:
    if state.get("approval_status") == "approved":
        return {
            **state,
            "pause": False,
            "graph_step": int(state.get("graph_step") or 0) + 1,
            "events": _event(
                state,
                "approval_already_granted",
                {"approval_id": state.get("approval_id")},
            ),
        }
    approval_id = state.get("approval_id") or str(uuid4())
    return {
        **state,
        "approval_id": approval_id,
        "approval_status": "pending",
        "pause": True,
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(
            state,
            "approval_required",
            {
                "approval_id": approval_id,
                "proposed_action": state.get("proposed_action"),
            },
        ),
        "final_response": (
            state.get("explanation")
            or "An address change requires your approval before we can proceed."
        ),
    }


async def execute_approved_action(state: AgentState) -> AgentState:
    if state.get("approval_status") != "approved":
        return {
            **state,
            "error": "approval_not_granted",
            "events": _event(state, "execute_blocked"),
        }
    gateway = state.get("tool_gateway")
    order = state.get("order") or {}
    proposed = state.get("proposed_action") or {}
    action_result: dict[str, Any] = {"status": "skipped"}
    if gateway and order.get("id") and proposed.get("address"):
        idem = proposed.get("idempotency_key") or f"addr-{state.get('run_id')}"
        result = await gateway.call(
            "erp.change_address",
            order_id=str(order["id"]),
            address=proposed["address"],
            idempotency_key=str(idem),
            if_match=str(order.get("version") or order.get("etag") or "1"),
        )
        action_result = {
            "ok": result.ok,
            "data": result.data,
            "error": str(result.error) if result.error else None,
        }
    return {
        **state,
        "action_result": action_result,
        "pause": False,
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(state, "action_executed", action_result),
    }


async def verify_action_result(state: AgentState) -> AgentState:
    gateway = state.get("tool_gateway")
    order = state.get("order") or {}
    proposed = state.get("proposed_action") or {}
    verification: dict[str, Any] = {"verified": False}
    if gateway and order.get("id"):
        result = await gateway.call("erp.get_order", order_id=str(order["id"]))
        if result.ok:
            current = result.data.get("shipping_address") or {}
            expected = proposed.get("address") or {}
            verification = {
                "verified": current.get("postal_code") == expected.get("postal_code")
                and current.get("line1") == expected.get("line1"),
                "order": result.data,
            }
            order = result.data
    return {
        **state,
        "order": order,
        "verification": verification,
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(state, "action_verified", verification),
    }


async def create_escalation(state: AgentState) -> AgentState:
    gateway = state.get("tool_gateway")
    validation = state.get("validation") or {}
    summary = {
        "intent": state.get("intent"),
        "reason_codes": validation.get("reason_codes"),
        "order_id": (state.get("order") or {}).get("id"),
        "conversation_id": state.get("conversation_id"),
    }
    ticket: dict[str, Any] = {"status": "local_only", "summary": summary}
    if gateway:
        result = await gateway.call(
            "ticketing.create_ticket",
            payload={
                "organization_id": state.get("organization_id"),
                "subject": "Support agent escalation",
                "body": str(summary),
                "priority": "normal",
            },
        )
        if result.ok:
            ticket = result.data
    return {
        **state,
        "escalation": ticket,
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(state, "escalated", ticket),
        "final_response": (
            "I need to escalate this to a human agent. "
            f"Reasons: {validation.get('reason_codes') or ['safety']}."
        ),
    }


async def finalize_response(state: AgentState) -> AgentState:
    if state.get("final_response"):
        text = state["final_response"]
    elif state.get("verification") and state["verification"].get("verified"):
        text = "Address change completed and verified. " + (state.get("explanation") or "")
    elif state.get("explanation"):
        text = state["explanation"]
    else:
        text = "How can I help with your order?"

    if state.get("approval_status") == "pending" and state.get("proposed_action"):
        proposed = state.get("proposed_action") or {}
        addr = proposed.get("address") or {}
        text = (
            (state.get("explanation") or text)
            + "\n\nI can update the delivery address, but I need your explicit approval first."
            + f"\nProposed address: {addr.get('line1')}, {addr.get('city')}, "
            + f"{addr.get('state')} {addr.get('postal_code')}."
            + "\nPlease approve or reject this change."
        )

    citations = state.get("citations") or []
    if citations and "Sources:" not in text:
        text += "\n\nSources: " + ", ".join(
            str(c.get("source")) for c in citations if c.get("source")
        )
    return {
        **state,
        "final_response": text,
        # Preserve pause so the runner can persist an approval record.
        "pause": bool(state.get("pause") and state.get("approval_status") == "pending"),
        "graph_step": int(state.get("graph_step") or 0) + 1,
        "events": _event(state, "finalized"),
    }
