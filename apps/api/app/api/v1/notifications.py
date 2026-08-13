"""Email notification test endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.core.config import Settings, get_settings
from app.core.security import ExecutionContext, get_execution_context
from app.services.email import EmailRecipient, get_email_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


class TestEmailRequest(BaseModel):
    to: EmailStr | None = None
    subject: str = Field(default="ResolveAI test email", max_length=200)


class TestEmailResponse(BaseModel):
    ok: bool
    skipped: bool = False
    message_id: str | None = None
    error: str | None = None
    sent_to: str | None = None


@router.post("/test-email", response_model=TestEmailResponse)
async def send_test_email(
    body: TestEmailRequest,
    ctx: ExecutionContext = Depends(get_execution_context),
    settings: Settings = Depends(get_settings),
) -> TestEmailResponse:
    ctx.require_permission("admin:all")

    service = get_email_service(settings)
    recipient = body.to or settings.email_fallback_recipient or settings.brevo_sender_email
    if not recipient:
        raise HTTPException(status_code=400, detail="no recipient configured")

    result = await service.send(
        to=[EmailRecipient(email=str(recipient), name=ctx.email or "Admin")],
        subject=body.subject,
        html_content=f"""
        <div style="font-family:Inter,Arial,sans-serif;">
          <h2>ResolveAI email test</h2>
          <p>Brevo transactional email is configured correctly.</p>
          <p>Sent by: {ctx.email or 'admin'}</p>
        </div>
        """,
        text_content="ResolveAI Brevo test email — configuration OK.",
    )

    return TestEmailResponse(
        ok=result.ok,
        skipped=result.skipped,
        message_id=result.message_id,
        error=result.error,
        sent_to=recipient,
    )
