"""Webhook models (mock Cisco Webex Connect callbacks)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """A single audit-trail entry attached to a conversation."""

    event_id: str
    conversation_id: str
    event_type: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WebexEventType(str, Enum):
    """Subset of mock Webex Connect event types we understand."""

    AGENT_ASSIGNED = "AGENT_ASSIGNED"
    AGENT_MESSAGE = "AGENT_MESSAGE"
    CONVERSATION_RESOLVED = "CONVERSATION_RESOLVED"
    CUSTOMER_NOTIFIED = "CUSTOMER_NOTIFIED"


class WebexWebhookRequest(BaseModel):
    """Inbound webhook payload from (mock) Webex Connect / Agent Desktop."""

    conversation_id: str
    event_type: WebexEventType = Field(..., examples=["AGENT_MESSAGE"])
    agent_id: Optional[str] = Field(default=None, examples=["agent-42"])
    text: Optional[str] = Field(default=None, examples=["Agent reply via Webex"])
    metadata: dict[str, Any] = Field(default_factory=dict)
