"""In-memory storage and conversation state-transition rules.

This is the single source of truth for the demo. Everything lives in plain
dictionaries — no database, no persistence across restarts.
"""

from __future__ import annotations

from app.models.conversation import ConversationStatus

# --- In-memory stores ---------------------------------------------------------
# Keyed by conversation_id.
conversations: dict[str, "object"] = {}
# conversation_id -> list[Message]
messages: dict[str, list] = {}
# conversation_id -> list[AuditEvent]
audit_logs: dict[str, list] = {}


def reset_state() -> None:
    """Clear all in-memory stores (useful for tests and the admin reset endpoint)."""
    conversations.clear()
    messages.clear()
    audit_logs.clear()


# --- State machine ------------------------------------------------------------

#: Allowed transitions between conversation states.
ALLOWED_TRANSITIONS: dict[ConversationStatus, set[ConversationStatus]] = {
    ConversationStatus.NEW: {ConversationStatus.QUEUED},
    ConversationStatus.QUEUED: {ConversationStatus.ASSIGNED},
    ConversationStatus.ASSIGNED: {ConversationStatus.ACTIVE},
    ConversationStatus.ACTIVE: {
        ConversationStatus.ASYNC,
        ConversationStatus.RESOLVED,
    },
    ConversationStatus.ASYNC: {
        ConversationStatus.RETURNED,
        ConversationStatus.RESOLVED,
    },
    ConversationStatus.RETURNED: {
        ConversationStatus.ACTIVE,
        ConversationStatus.RESOLVED,
    },
    ConversationStatus.RESOLVED: {ConversationStatus.CLOSED},
    ConversationStatus.CLOSED: set(),
}


def can_transition(current: ConversationStatus, target: ConversationStatus) -> bool:
    """Return True if moving from ``current`` to ``target`` is allowed."""
    return target in ALLOWED_TRANSITIONS.get(current, set())
