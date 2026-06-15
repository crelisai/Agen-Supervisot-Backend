"""Mock Cisco Webex Connect adapter.

None of these functions make real network calls. They log the action and write
an audit event so the demo can show the full async flow:

    Async Chat Server -> Webex Connect -> Agent Desktop -> Webhook -> Async Chat Server

Replace the bodies here with real Webex Connect SDK / REST calls when wiring up
a live integration.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.models.mapping import ExternalConversationMapping
from app.services import audit_service

logger = logging.getLogger("webex_adapter")


def build_webex_payload(
    message: str,
    mapping: Optional[ExternalConversationMapping],
) -> dict[str, Any]:
    """Build a mock Webex Connect-shaped payload from a conversation mapping.

    Shape mirrors the *expected future* Cisco field names (userId / tid / chatId).
    These are NOT confirmed Cisco API fields — they are mock placeholders.
    """
    return {
        "datetime": datetime.now(timezone.utc).isoformat(),
        "message": message,
        "userId": mapping.external_user_id if mapping else None,
        "tid": mapping.webex_thread_id if mapping else None,
        "chatId": mapping.webex_chat_id if mapping else None,
        "teamId": mapping.webex_team_id if mapping else None,
        "assetId": mapping.webex_asset_id if mapping else None,
    }


def send_to_webex_connect(
    conversation_id: str,
    message: str,
    mapping: Optional[ExternalConversationMapping] = None,
) -> dict[str, Any]:
    """Pretend to forward a customer message to Webex Connect.

    Logs a Cisco-shaped payload and records it in the audit trail. No network
    calls are made.
    """
    payload = build_webex_payload(message, mapping)
    logger.info("[MOCK] send_to_webex_connect conversation=%s payload=%s",
                conversation_id, payload)
    audit_service.record_event(
        conversation_id,
        "Sent To Webex Connect",
        {"payload": payload, "mock": True},
    )
    return {
        "status": "accepted",
        "mock": True,
        "conversation_id": conversation_id,
        "payload": payload,
    }


def assign_agent(conversation_id: str, agent_id: str) -> dict[str, Any]:
    """Pretend Webex Connect routed the conversation to an agent."""
    logger.info("[MOCK] assign_agent conversation=%s agent=%s",
                conversation_id, agent_id)
    audit_service.record_event(
        conversation_id,
        "Assigned To Agent",
        {"agent_id": agent_id, "mock": True},
    )
    return {"status": "assigned", "agent_id": agent_id, "mock": True}


def notify_previous_agent(conversation_id: str, agent_id: str | None) -> dict[str, Any]:
    """Pretend to notify the agent who previously handled an ASYNC conversation."""
    logger.info("[MOCK] notify_previous_agent conversation=%s agent=%s",
                conversation_id, agent_id)
    audit_service.record_event(
        conversation_id,
        "Notified Previous Agent",
        {"agent_id": agent_id, "mock": True},
    )
    return {"status": "notified", "agent_id": agent_id, "mock": True}


def receive_webhook(conversation_id: str, event_type: str,
                    payload: dict[str, Any]) -> dict[str, Any]:
    """Record receipt of a (mock) Webex Connect webhook callback."""
    logger.info("[MOCK] receive_webhook conversation=%s event=%s payload=%s",
                conversation_id, event_type, payload)
    audit_service.record_event(
        conversation_id,
        "Webhook Received",
        {"event_type": event_type, "payload": payload, "mock": True},
    )
    return {"status": "received", "event_type": event_type, "mock": True}
