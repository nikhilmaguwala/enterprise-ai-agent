"""Transactional email via Brevo (Sendinblue) REST API."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db import models as m

logger = logging.getLogger(__name__)

BREVO_SMTP_URL = "https://api.brevo.com/v3/smtp/email"


@dataclass(frozen=True)
class EmailRecipient:
    email: str
    name: str | None = None


@dataclass(frozen=True)
class EmailResult:
    ok: bool
    message_id: str | None = None
    error: str | None = None
    skipped: bool = False


class EmailService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return bool(
            self.settings.email_enabled
            and self.settings.brevo_api_key
            and self.settings.brevo_sender_email
        )

    async def send(
        self,
        *,
        to: list[EmailRecipient],
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> EmailResult:
        if not self.enabled:
            logger.info("email_skipped_disabled", extra={"subject": subject})
            return EmailResult(ok=False, skipped=True, error="email disabled")

        if not to:
            return EmailResult(ok=False, error="no recipients")

        recipients = self._resolve_recipients(to)
        payload: dict[str, Any] = {
            "sender": {
                "name": self.settings.brevo_sender_name,
                "email": self.settings.brevo_sender_email,
            },
            "to": [
                {"email": r.email, "name": r.name or r.email.split("@")[0]}
                for r in recipients
            ],
            "subject": subject,
            "htmlContent": html_content,
        }
        if text_content:
            payload["textContent"] = text_content

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    BREVO_SMTP_URL,
                    headers={
                        "api-key": self.settings.brevo_api_key,
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json=payload,
                )
            if response.status_code >= 400:
                detail = response.text[:500]
                logger.warning(
                    "brevo_send_failed",
                    extra={"status": response.status_code, "detail": detail},
                )
                return EmailResult(ok=False, error=f"Brevo {response.status_code}: {detail}")

            data = response.json()
            message_id = str(data.get("messageId") or "")
            logger.info("brevo_sent", extra={"message_id": message_id, "subject": subject})
            return EmailResult(ok=True, message_id=message_id or None)
        except Exception as exc:  # noqa: BLE001
            logger.warning("brevo_send_error", extra={"error": str(exc)})
            return EmailResult(ok=False, error=str(exc))

    def _resolve_recipients(self, to: list[EmailRecipient]) -> list[EmailRecipient]:
        """In demo mode, route all mail to a verified inbox."""
        fallback = self.settings.email_fallback_recipient.strip()
        if fallback and self.settings.app_env != "production":
            return [EmailRecipient(email=fallback, name="ResolveAI Demo Inbox")]
        return to

    async def notify_approval_required(
        self,
        db: AsyncSession,
        *,
        organization_id: Any,
        approval_id: str,
        conversation_id: str,
        action_type: str,
        summary: str,
        app_url: str,
    ) -> EmailResult:
        recipients = await self._staff_recipients(
            db,
            organization_id=organization_id,
            roles=["support_agent", "supervisor", "admin"],
        )
        inbox_url = f"{app_url.rstrip('/')}/inbox"
        chat_url = f"{app_url.rstrip('/')}/chat?c={conversation_id}"
        html = f"""
        <div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;">
          <h2 style="color:#000f3f;">Approval required — {action_type.replace('_', ' ')}</h2>
          <p style="color:#45464f;">{summary}</p>
          <p style="color:#45464f;">A customer conversation is paused until a supervisor approves the proposed change.</p>
          <p>
            <a href="{chat_url}" style="background:#2563EB;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none;">Open conversation</a>
            &nbsp;
            <a href="{inbox_url}" style="color:#0051d5;">View inbox</a>
          </p>
          <p style="font-size:12px;color:#767680;">Approval ID: {approval_id}</p>
        </div>
        """
        return await self.send(
            to=recipients,
            subject=f"[ResolveAI] Approval required: {action_type.replace('_', ' ')}",
            html_content=html,
            text_content=f"Approval required for {action_type}. Open: {chat_url}",
        )

    async def notify_escalation(
        self,
        db: AsyncSession,
        *,
        organization_id: Any,
        conversation_id: str,
        reason: str,
        summary: str,
        app_url: str,
    ) -> EmailResult:
        recipients = await self._staff_recipients(
            db,
            organization_id=organization_id,
            roles=["support_agent", "supervisor", "admin"],
        )
        inbox_url = f"{app_url.rstrip('/')}/inbox"
        html = f"""
        <div style="font-family:Inter,Arial,sans-serif;max-width:560px;margin:0 auto;">
          <h2 style="color:#000f3f;">Support escalation</h2>
          <p style="color:#45464f;"><strong>Reason:</strong> {reason}</p>
          <p style="color:#45464f;">{summary}</p>
          <p><a href="{inbox_url}" style="background:#2563EB;color:#fff;padding:10px 16px;border-radius:8px;text-decoration:none;">Open support inbox</a></p>
        </div>
        """
        return await self.send(
            to=recipients,
            subject=f"[ResolveAI] Escalation: {reason[:80]}",
            html_content=html,
            text_content=f"Escalation: {reason}. Inbox: {inbox_url}",
        )

    async def _staff_recipients(
        self,
        db: AsyncSession,
        *,
        organization_id: Any,
        roles: list[str],
    ) -> list[EmailRecipient]:
        stmt = (
            select(m.User.email, m.User.display_name)
            .join(m.Membership, m.Membership.user_id == m.User.id)
            .where(
                m.Membership.organization_id == organization_id,
                m.Membership.status == "active",
                m.Membership.role.in_(roles),
                m.User.status == "active",
            )
        )
        rows = (await db.execute(stmt)).all()
        seen: set[str] = set()
        out: list[EmailRecipient] = []
        for email, name in rows:
            key = email.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(EmailRecipient(email=email, name=name))
        if not out and self.settings.brevo_sender_email:
            out.append(
                EmailRecipient(
                    email=self.settings.brevo_sender_email,
                    name=self.settings.brevo_sender_name,
                )
            )
        return out


def get_email_service(settings: Settings | None = None) -> EmailService:
    return EmailService(settings)
