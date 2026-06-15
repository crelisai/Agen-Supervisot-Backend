"""Conversation models and the conversation state machine."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConversationStatus(str, Enum):
    """Lifecycle states for a conversation.

    Flow (typical):
        NEW -> QUEUED -> ASSIGNED -> ACTIVE -> ASYNC -> RETURNED -> RESOLVED -> CLOSED
    """

    NEW = "NEW"
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    ACTIVE = "ACTIVE"
    ASYNC = "ASYNC"
    RETURNED = "RETURNED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


def _utcnow() -> datetime:
    """Timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Conversation(BaseModel):
    """A single chat conversation between a customer and (eventually) an agent."""

    conversation_id: str
    journey_id: str
    customer_id: str
    customer_name: str
    assigned_agent: Optional[str] = None
    status: ConversationStatus = ConversationStatus.NEW
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    # Wrap-up details (populated when the conversation is wrapped up).
    wrap_up_reason: Optional[str] = None
    disconnect_reason: Optional[str] = None

    def touch(self) -> None:
        """Bump the ``updated_at`` timestamp."""
        self.updated_at = _utcnow()


# --- Request payloads ---------------------------------------------------------


class InboundMessageRequest(BaseModel):
    """Customer-initiated inbound message that starts a conversation."""

    journey_id: str = Field(..., examples=["uob-tmrw-onboarding"])
    customer_id: str = Field(..., examples=["cust-1001"])
    customer_name: str = Field(..., examples=["Jane Tan"])
    text: str = Field(..., examples=["Hi, I need help with my account."])


class ReplyRequest(BaseModel):
    """Agent reply to an existing conversation."""

    conversation_id: str
    agent_id: str = Field(..., examples=["agent-42"])
    text: str = Field(..., examples=["Sure, I can help with that."])


class MoveToAsyncRequest(BaseModel):
    """Move a conversation into the ASYNC state."""

    conversation_id: str
    reason: Optional[str] = Field(
        default=None, examples=["Awaiting customer documents"]
    )


class WrapUpRequest(BaseModel):
    """Capture wrap-up details for a conversation."""

    conversation_id: str
    wrap_up_reason: str = Field(..., examples=["Issue resolved"])
    disconnect_reason: str = Field(..., examples=["Customer ended chat"])


class CustomerReturnedRequest(BaseModel):
    """Customer has returned to an ASYNC conversation."""

    conversation_id: str
    text: Optional[str] = Field(
        default=None, examples=["I'm back with the documents."]
    )
