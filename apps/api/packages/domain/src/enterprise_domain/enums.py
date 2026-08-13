"""Shared domain enumerations."""

from __future__ import annotations

from enum import StrEnum


class MembershipRole(StrEnum):
    CUSTOMER = "customer"
    SUPPORT_AGENT = "support_agent"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class ConversationStatus(StrEnum):
    OPEN = "open"
    WAITING_APPROVAL = "waiting_approval"
    ESCALATED = "escalated"
    CLOSED = "closed"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    DELAYED = "delayed"


class ShipmentStatus(StrEnum):
    LABEL_CREATED = "label_created"
    IN_TRANSIT = "in_transit"
    DELAYED = "delayed"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    EXCEPTION = "exception"


class AgentRunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    EXECUTED = "executed"


class DocumentStatus(StrEnum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    ACTIVE = "active"
    FAILED = "failed"
    DELETED = "deleted"


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD = "dead"


class IntentType(StrEnum):
    ORDER_STATUS = "order_status"
    DELAY_EXPLANATION = "delay_explanation"
    ADDRESS_CHANGE = "address_change"
    POLICY_QUESTION = "policy_question"
    ESCALATION = "escalation"
    UNKNOWN = "unknown"
