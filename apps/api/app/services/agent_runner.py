"""Run LangGraph support agent and persist events/messages."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.logging import get_logger
from app.core.security import ExecutionContext
from app.db import models as m
from enterprise_agent.graph import build_support_graph
from enterprise_agent.providers.factory import build_llm_provider
from enterprise_domain.seed_ids import SeedIds
from enterprise_integrations.gateway import ToolGateway
from enterprise_knowledge.retrieval import HybridRetriever

logger = get_logger(__name__)


EVENT_TYPE_MAP = {
    "auth_ok": "run_started",
    "intent_classified": "intent_identified",
    "policy_retrieved": "searching_knowledge",
    "customer_loaded": "reading_customer",
    "order_loaded": "reading_order",
    "delivery_checked": "checking_shipment",
    "approval_required": "approval_required",
    "tool_executing": "tool_executing",
    "tool_completed": "tool_completed",
    "escalated": "escalated",
    "finalized": "completed",
    "auth_failed": "failed",
}


class AgentRunner:
    def __init__(self, db: AsyncSession, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.graph = build_support_graph()

    async def run_turn(
        self,
        *,
        ctx: ExecutionContext,
        conversation: m.Conversation,
        user_message: m.Message,
        run: m.AgentRun,
        order_id: UUID | None = None,
        proposed_action: dict[str, Any] | None = None,
        resume_approval: m.Approval | None = None,
    ) -> dict[str, Any]:
        llm = build_llm_provider(self.settings)
        gateway = ToolGateway.from_settings(self.settings)
        retriever = HybridRetriever.from_settings(self.settings)

        customer_id = None
        customer_email = ctx.email
        default_order: dict[str, Any] = {}

        db_customer = (
            await self.db.execute(
                select(m.Customer).where(
                    m.Customer.organization_id == ctx.organization_id,
                    m.Customer.user_id == ctx.actor_id,
                )
            )
        ).scalar_one_or_none()
        if db_customer is not None:
            customer_id = str(db_customer.id)
            customer_email = db_customer.email
            db_order = (
                await self.db.execute(
                    select(m.Order)
                    .where(
                        m.Order.organization_id == ctx.organization_id,
                        m.Order.customer_id == db_customer.id,
                    )
                    .order_by(m.Order.created_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            if db_order is not None:
                default_order = {
                    "id": str(db_order.id),
                    "order_number": db_order.order_number,
                    "tracking_number": db_order.tracking_number,
                }

        if ctx.organization_id == SeedIds.ORG_ACME:
            customer_id = customer_id or str(SeedIds.CUSTOMER_ACME)
        elif ctx.organization_id == SeedIds.ORG_GLOBEX:
            customer_id = customer_id or str(SeedIds.CUSTOMER_GLOBEX)

        if order_id:
            default_order = {"id": str(order_id)}
        elif not default_order and ctx.organization_id == SeedIds.ORG_ACME:
            default_order = {
                "id": str(SeedIds.ORDER_ACME_DELAYED),
                "order_number": SeedIds.ORDER_NUMBER_ACME_DELAYED,
                "tracking_number": SeedIds.TRACKING_ACME_DELAYED,
            }

        initial: dict[str, Any] = {
            "organization_id": str(ctx.organization_id),
            "actor_id": str(ctx.actor_id),
            "user_id": str(ctx.actor_id),
            "customer_id": customer_id,
            "conversation_id": str(conversation.id),
            "agent_run_id": str(run.id),
            "run_id": str(run.id),
            "user_message": user_message.content,
            "roles": list(ctx.roles),
            "permissions": list(ctx.permissions),
            "order": default_order,
            "customer": {"id": customer_id, "email": customer_email},
            "proposed_action": proposed_action or {},
            "llm": llm,
            "tool_gateway": gateway,
            "retriever": retriever,
            "events": [],
            "graph_step": 0,
            "retry_count": 0,
        }

        if resume_approval is not None:
            initial["approval_id"] = str(resume_approval.id)
            initial["approval_status"] = resume_approval.status
            initial["pause"] = False
            initial["proposed_action"] = resume_approval.payload or {}
            # Jump into approval continuation by setting status approved
            if resume_approval.status == "approved":
                initial["approval_status"] = "approved"
                initial["validation"] = {"route": "approve"}

        try:
            final_state: dict[str, Any] = await self.graph.ainvoke(initial)
        except Exception as exc:  # noqa: BLE001
            logger.exception("agent_run_failed", error=str(exc), agent_run_id=str(run.id))
            final_state = {
                "error": "agent_failed",
                "final_response": (
                    "I hit a temporary issue while processing your request. "
                    "Please retry, or I can escalate to a human agent."
                ),
                "events": [{"type": "failed", "payload": {"error_class": type(exc).__name__}}],
                "escalation": True,
            }

        await self._persist_events(ctx, conversation, run, final_state.get("events") or [])

        approval_row: m.Approval | None = None
        if final_state.get("pause") and final_state.get("approval_status") == "pending":
            approval_row = await self._create_approval(
                ctx, conversation, run, final_state
            )
            conversation.status = "waiting_approval"
            run.status = "paused"
        elif final_state.get("escalation"):
            conversation.status = "escalated"
            run.status = "escalated"
            await self._create_handoff(ctx, conversation, run, final_state)
        else:
            run.status = "completed"
            if conversation.status == "open":
                conversation.status = "resolved"

        response_text = (
            final_state.get("final_response")
            or final_state.get("explanation")
            or "I've finished reviewing your request."
        )
        citations = final_state.get("citations") or []
        for c in citations:
            self.db.add(
                m.Citation(
                    organization_id=ctx.organization_id,
                    agent_run_id=run.id,
                    document_id=None,
                    chunk_id=None,
                    source_label=str(c.get("source") or c.get("title") or "policy")[:200],
                    excerpt=str(c.get("excerpt") or c.get("content") or "")[:2000],
                    score=float(c.get("score") or 0),
                )
            )

        assistant = m.Message(
            organization_id=ctx.organization_id,
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            agent_run_id=run.id,
            metadata_={
                "citations": citations,
                "approval_id": str(approval_row.id) if approval_row else None,
                "intent": final_state.get("intent"),
                "confidence": final_state.get("confidence"),
            },
        )
        self.db.add(assistant)

        run.state = {
            k: v
            for k, v in final_state.items()
            if k not in {"llm", "tool_gateway", "retriever"}
        }
        run.intent = final_state.get("intent")
        run.completed_at = datetime.now(UTC) if run.status in {"completed", "escalated"} else None
        run.version += 1

        await self.db.flush()
        return {
            "assistant": assistant,
            "approval": approval_row,
            "final_state": {
                k: v
                for k, v in final_state.items()
                if k not in {"llm", "tool_gateway", "retriever"}
            },
            "run": run,
        }

    async def _persist_events(
        self,
        ctx: ExecutionContext,
        conversation: m.Conversation,
        run: m.AgentRun,
        events: list[dict[str, Any]],
    ) -> None:
        for idx, ev in enumerate(events, start=1):
            raw_type = str(ev.get("type") or "step")
            mapped = EVENT_TYPE_MAP.get(raw_type, raw_type)
            self.db.add(
                m.AgentEvent(
                    organization_id=ctx.organization_id,
                    agent_run_id=run.id,
                    conversation_id=conversation.id,
                    sequence=idx,
                    event_type=mapped,
                    payload=ev.get("payload") or {},
                )
            )

    async def _create_approval(
        self,
        ctx: ExecutionContext,
        conversation: m.Conversation,
        run: m.AgentRun,
        state: dict[str, Any],
    ) -> m.Approval:
        from app.services.idempotency import canonical_hash

        payload = state.get("proposed_action") or {}
        if not payload and state.get("order"):
            payload = {
                "type": "address_change",
                "order_id": state["order"].get("id"),
                "address": (state.get("proposed_action") or {}).get("address")
                or {
                    "line1": "200 Harbor Road",
                    "city": "Oakland",
                    "state": "CA",
                    "postal_code": "94607",
                    "country": "US",
                },
            }
        payload_hash = canonical_hash(payload)
        approval = m.Approval(
            id=uuid4(),
            organization_id=ctx.organization_id,
            conversation_id=conversation.id,
            agent_run_id=run.id,
            action_type=str(payload.get("type") or "address_change"),
            payload=payload,
            payload_hash=payload_hash,
            status="pending",
            requested_by_user_id=ctx.actor_id,
            expires_at=datetime.now(UTC).replace(microsecond=0)
            + __import__("datetime").timedelta(hours=2),
        )
        self.db.add(approval)
        self.db.add(
            m.AgentEvent(
                organization_id=ctx.organization_id,
                agent_run_id=run.id,
                conversation_id=conversation.id,
                sequence=90,
                event_type="approval_required",
                payload={
                    "approval_id": str(approval.id),
                    "current": (state.get("order") or {}).get("shipping_address"),
                    "proposed": payload.get("address"),
                },
            )
        )
        await self.db.flush()

        try:
            from app.services.email import get_email_service

            await get_email_service(self.settings).notify_approval_required(
                self.db,
                organization_id=ctx.organization_id,
                approval_id=str(approval.id),
                conversation_id=str(conversation.id),
                action_type=approval.action_type,
                summary=f"Approve {approval.action_type.replace('_', ' ')} for conversation {conversation.subject or conversation.id}",
                app_url=self.settings.app_url,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("approval_email_failed", error=str(exc))

        return approval

    async def _create_handoff(
        self,
        ctx: ExecutionContext,
        conversation: m.Conversation,
        run: m.AgentRun,
        state: dict[str, Any],
    ) -> None:
        gateway = ToolGateway.from_settings(self.settings)
        try:
            await gateway.call(
                "ticketing.create_ticket",
                payload={
                    "customer": state.get("customer"),
                    "order": state.get("order"),
                    "conversation_summary": state.get("final_response")
                    or state.get("explanation"),
                    "customer_request": state.get("user_message"),
                    "evidence": state.get("citations"),
                    "tools_called": [
                        e.get("payload")
                        for e in (state.get("events") or [])
                        if e.get("type") in {"tool_completed", "delivery_checked", "order_loaded"}
                    ],
                    "actions_attempted": [state.get("proposed_action")],
                    "failure_reason": state.get("error") or "escalation",
                    "recommended_next_action": "Review evidence and contact customer",
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("handoff_failed", error=str(exc))

        try:
            from app.services.email import get_email_service

            reason = str(state.get("error") or state.get("escalation_reason") or "Agent escalation")
            summary = str(
                state.get("final_response")
                or state.get("explanation")
                or "Review the conversation in the support inbox."
            )
            await get_email_service(self.settings).notify_escalation(
                self.db,
                organization_id=ctx.organization_id,
                conversation_id=str(conversation.id),
                reason=reason,
                summary=summary[:500],
                app_url=self.settings.app_url,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("escalation_email_failed", error=str(exc))
