"""Pydantic v2 API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import AliasChoices, BaseModel, Field, model_validator


class HealthResponse(BaseModel):
    status: str


class VersionResponse(BaseModel):
    version: str
    git_sha: str
    graph_version: str


class ConversationCreate(BaseModel):
    subject: str | None = None
    title: str | None = None
    organization_id: UUID | None = None  # spoof detection only
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def alias_title_to_subject(self) -> ConversationCreate:
        if self.subject is None and self.title is not None:
            self.subject = self.title
        return self


class ConversationOut(BaseModel):
    id: UUID
    organization_id: UUID
    status: str
    subject: str | None = None
    title: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def map_subject_title(cls, data: Any) -> Any:
        if hasattr(data, "subject"):
            return {
                "id": data.id,
                "organization_id": data.organization_id,
                "status": data.status,
                "subject": data.subject,
                "title": data.subject,
                "created_at": data.created_at,
                "updated_at": getattr(data, "updated_at", None) or data.created_at,
            }
        if isinstance(data, dict):
            subject = data.get("subject")
            title = data.get("title")
            if subject is None and title is not None:
                data = {**data, "subject": title}
            elif title is None and subject is not None:
                data = {**data, "title": subject}
            if data.get("updated_at") is None and data.get("created_at") is not None:
                data = {**data, "updated_at": data["created_at"]}
        return data


class ConversationListOut(BaseModel):
    items: list[ConversationOut]
    total: int | None = None


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    organization_id: UUID | None = None
    proposed_action: dict[str, Any] | None = None
    order_id: UUID | None = None
    idempotency_key: str | None = None


class MessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    citations: list[dict[str, Any]] | None = None
    approval: dict[str, Any] | None = None
    run_id: UUID | None = None

    model_config = {"from_attributes": True}


class MessageListOut(BaseModel):
    items: list[MessageOut]


class ApprovalDecision(BaseModel):
    reason: str | None = Field(
        default=None,
        validation_alias=AliasChoices("reason", "note"),
    )
    organization_id: UUID | None = None


class ApprovalOut(BaseModel):
    id: UUID
    organization_id: UUID
    conversation_id: UUID | None = None
    status: str
    action_type: str
    summary: str | None = None
    payload: dict[str, Any]
    created_at: datetime
    risk_level: str | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def enrich(cls, data: Any) -> Any:
        if hasattr(data, "action_type"):
            return {
                "id": data.id,
                "organization_id": data.organization_id,
                "conversation_id": getattr(data, "conversation_id", None),
                "status": data.status,
                "action_type": data.action_type,
                "summary": f"Approve {str(data.action_type).replace('_', ' ')}",
                "payload": data.payload or {},
                "created_at": data.created_at,
                "risk_level": "high" if data.action_type == "address_change" else "medium",
            }
        return data


class DocumentPresignRequest(BaseModel):
    title: str
    mime_type: str = "application/pdf"
    byte_size: int | None = None
    organization_id: UUID | None = None


class DocumentPresignResponse(BaseModel):
    document_id: UUID
    upload_url: str
    storage_key: str


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    storage_key: str
    byte_size: int
    checksum_sha256: str
    mime_type: str


class DocumentCompleteRequest(BaseModel):
    checksum_sha256: str | None = None
    organization_id: UUID | None = None


class DocumentOut(BaseModel):
    id: UUID
    organization_id: UUID
    title: str
    filename: str | None = None
    status: str
    mime_type: str
    byte_size: int | None = None
    chunk_count: int | None = None
    created_at: datetime
    updated_at: datetime | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def map_doc(cls, data: Any) -> Any:
        if hasattr(data, "title"):
            return {
                "id": data.id,
                "organization_id": data.organization_id,
                "title": data.title,
                "filename": data.title,
                "status": data.status,
                "mime_type": data.mime_type,
                "byte_size": getattr(data, "byte_size", None),
                "created_at": data.created_at,
                "updated_at": getattr(data, "updated_at", None),
                "error_message": None,
            }
        return data


class DocumentListOut(BaseModel):
    items: list[DocumentOut]


class AgentRunOut(BaseModel):
    id: UUID
    organization_id: UUID
    conversation_id: UUID
    status: str
    intent: str | None = None
    graph_version: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    steps: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def map_run(cls, data: Any) -> Any:
        status_map = {
            "pending": "queued",
            "completed": "succeeded",
            "escalated": "failed",
        }
        if hasattr(data, "status"):
            raw = data.status
            return {
                "id": data.id,
                "organization_id": data.organization_id,
                "conversation_id": data.conversation_id,
                "status": status_map.get(raw, raw),
                "intent": data.intent,
                "graph_version": getattr(data, "graph_version", None),
                "started_at": getattr(data, "started_at", None),
                "finished_at": getattr(data, "completed_at", None),
                "steps": [],
                "error": getattr(data, "error", None),
                "created_at": getattr(data, "created_at", None),
            }
        if isinstance(data, dict) and "status" in data:
            raw = data["status"]
            data = {**data, "status": status_map.get(raw, raw)}
        return data


class JobOut(BaseModel):
    id: UUID
    job_type: str
    status: str
    attempts: int
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationRunCreate(BaseModel):
    dataset: str = "default"
    organization_id: UUID | None = None


class EvaluationRunOut(BaseModel):
    id: UUID
    dataset: str
    status: str
    summary: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditEventOut(BaseModel):
    id: UUID
    action: str
    resource_type: str
    resource_id: str
    created_at: datetime
    payload: dict[str, Any]

    model_config = {"from_attributes": True}


class DevTokenRequest(BaseModel):
    organization_id: UUID
    actor_id: UUID
    roles: list[str] = Field(default_factory=lambda: ["customer"])
    email: str | None = None


class DevLoginRequest(BaseModel):
    email: str
