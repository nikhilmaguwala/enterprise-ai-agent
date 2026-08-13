"""Mock ticketing / escalation service."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Mock Ticketing", version="0.1.0")
TICKETS: dict[str, dict[str, Any]] = {}
TOKEN = "mock-service-dev-token"


class TicketCreate(BaseModel):
    organization_id: str | None = None
    subject: str
    body: str
    priority: str = "normal"
    metadata: dict[str, Any] = Field(default_factory=dict)


def require_token(authorization: str | None = Header(default=None)) -> None:
    if not authorization or authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "mock-ticketing"}


@app.post("/tickets")
async def create_ticket(body: TicketCreate, _: None = Depends(require_token)) -> dict:
    ticket_id = str(uuid4())
    ticket = {
        "id": ticket_id,
        "status": "open",
        **body.model_dump(),
    }
    TICKETS[ticket_id] = ticket
    return ticket


@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, _: None = Depends(require_token)) -> dict:
    ticket = TICKETS.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")
    return ticket


@app.post("/tickets/{ticket_id}/comments")
async def add_comment(
    ticket_id: str,
    body: dict[str, Any],
    _: None = Depends(require_token),
) -> dict:
    ticket = TICKETS.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="ticket not found")
    comments = ticket.setdefault("comments", [])
    comment = {"id": str(uuid4()), **body}
    comments.append(comment)
    return comment


@app.post("/handoffs")
async def create_handoff(body: dict[str, Any], _: None = Depends(require_token)) -> dict:
    handoff_id = str(uuid4())
    handoff = {"id": handoff_id, "status": "queued", **body}
    TICKETS[handoff_id] = handoff
    return handoff
