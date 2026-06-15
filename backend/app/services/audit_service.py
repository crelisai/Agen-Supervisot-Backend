"""Audit-trail service.

Every meaningful API action records an :class:`AuditEvent` against its
conversation. The audit log is stored in memory and exposed via the admin /
audit routes.
"""

from __future__ import annotations

import uuid
from typing import Any

from app.models.webhook import AuditEvent
from app.services import state_service


def record_event(
    conversation_id: str,
    event_type: str,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    """Create and store an audit event for a conversation.

    Args:
        conversation_id: The conversation the event belongs to.
        event_type: Human-readable event label, e.g. ``"Conversation Created"``.
        details: Optional structured context for the event.

    Returns:
        The persisted :class:`AuditEvent`.
    """
    event = AuditEvent(
        event_id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        event_type=event_type,
        details=details or {},
    )
    state_service.audit_logs.setdefault(conversation_id, []).append(event)
    return event


def get_events(conversation_id: str) -> list[AuditEvent]:
    """Return the ordered audit trail for a conversation (empty list if none)."""
    return state_service.audit_logs.get(conversation_id, [])
