"""Message model."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class SenderType(str, Enum):
    """Who sent a given message."""

    CUSTOMER = "CUSTOMER"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Message(BaseModel):
    """A single chat message within a conversation."""

    message_id: str
    conversation_id: str
    sender_type: SenderType
    text: str
    timestamp: datetime = Field(default_factory=_utcnow)
