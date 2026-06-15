"""Conversation orchestration service.

Coordinates the in-memory stores, the state machine, the audit trail and the
mock Webex adapter. Routes call into this module rather than touching storage
directly.
"""

from __future__ import annotations

import uuid
from typing import Optional

from app.models.conversation import Conversation, ConversationStatus
from app.models.mapping import ExternalConversationMapping
from app.models.message import Message, SenderType
from app.services import audit_service, mapping_service, state_service, webex_adapter


class ConversationError(Exception):
    """Raised when a requested operation is invalid (e.g. bad state transition)."""


class ConversationNotFound(ConversationError):
    """Raised when a conversation_id does not exist."""


# --- Helpers ------------------------------------------------------------------


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def get_conversation(conversation_id: str) -> Conversation:
    """Fetch a conversation or raise :class:`ConversationNotFound`."""
    convo = state_service.conversations.get(conversation_id)
    if convo is None:
        raise ConversationNotFound(f"Conversation '{conversation_id}' not found")
    return convo


def list_conversations() -> list[Conversation]:
    """Return all conversations."""
    return list(state_service.conversations.values())


def get_messages(conversation_id: str) -> list[Message]:
    """Return all messages for a conversation (validates existence)."""
    get_conversation(conversation_id)
    return state_service.messages.get(conversation_id, [])


def _add_message(conversation_id: str, sender_type: SenderType, text: str) -> Message:
    message = Message(
        message_id=_new_id("msg"),
        conversation_id=conversation_id,
        sender_type=sender_type,
        text=text,
    )
    state_service.messages.setdefault(conversation_id, []).append(message)
    return message


def _transition(convo: Conversation, target: ConversationStatus) -> None:
    if not state_service.can_transition(convo.status, target):
        raise ConversationError(
            f"Invalid transition {convo.status.value} -> {target.value}"
        )
    convo.status = target
    convo.touch()


# --- Use cases ----------------------------------------------------------------


def create_inbound(
    journey_id: str,
    customer_id: str,
    customer_name: str,
    text: str,
) -> tuple[Conversation, Message, ExternalConversationMapping]:
    """Create a new conversation from a customer inbound message.

    The conversation is created as NEW, the customer message is stored, a mock
    Webex Connect/Engage mapping is generated, the conversation is queued, and
    the message is forwarded to (mock) Webex Connect.
    """
    conversation_id = _new_id("conv")
    convo = Conversation(
        conversation_id=conversation_id,
        journey_id=journey_id,
        customer_id=customer_id,
        customer_name=customer_name,
        status=ConversationStatus.NEW,
    )
    state_service.conversations[conversation_id] = convo
    audit_service.record_event(
        conversation_id,
        "Conversation Created",
        {"journey_id": journey_id, "customer_id": customer_id},
    )

    message = _add_message(conversation_id, SenderType.CUSTOMER, text)
    audit_service.record_event(
        conversation_id,
        "Customer Message Received",
        {"message_id": message.message_id},
    )

    # Generate mock Webex Connect / Engage identifiers and store the mapping.
    mapping = mapping_service.create_mapping(
        conversation_id=conversation_id,
        journey_id=journey_id,
        customer_id=customer_id,
        external_user_id=f"ext-{customer_id}",
        webex_thread_id=mapping_service.generate_webex_thread_id(),
        webex_chat_id=mapping_service.generate_webex_chat_id(),
        webex_team_id=f"team-{journey_id}",
        webex_asset_id="asset-demo",
    )
    audit_service.record_event(
        conversation_id,
        "External Mapping Created",
        {
            "userId": mapping.external_user_id,
            "tid": mapping.webex_thread_id,
            "chatId": mapping.webex_chat_id,
        },
    )

    # Move NEW -> QUEUED and hand off to Webex Connect.
    _transition(convo, ConversationStatus.QUEUED)
    audit_service.record_event(conversation_id, "Queued", {})
    webex_adapter.send_to_webex_connect(conversation_id, text, mapping)

    return convo, message, mapping


def add_reply(conversation_id: str, agent_id: str, text: str) -> tuple[Conversation, Message]:
    """Add an agent reply.

    Assigns/activates the conversation as needed so a reply always lands in a
    sensible state for the demo.
    """
    convo = get_conversation(conversation_id)

    # Walk the conversation forward to ACTIVE if it isn't there yet.
    if convo.status == ConversationStatus.QUEUED:
        _transition(convo, ConversationStatus.ASSIGNED)
        convo.assigned_agent = agent_id
        webex_adapter.assign_agent(conversation_id, agent_id)
    if convo.status == ConversationStatus.RETURNED:
        _transition(convo, ConversationStatus.ACTIVE)
    if convo.status == ConversationStatus.ASSIGNED:
        if convo.assigned_agent is None:
            convo.assigned_agent = agent_id
        _transition(convo, ConversationStatus.ACTIVE)

    if convo.status != ConversationStatus.ACTIVE:
        raise ConversationError(
            f"Cannot reply while conversation is {convo.status.value}"
        )

    message = _add_message(conversation_id, SenderType.AGENT, text)
    convo.touch()
    audit_service.record_event(
        conversation_id,
        "Agent Reply Added",
        {"agent_id": agent_id, "message_id": message.message_id},
    )
    return convo, message


def move_to_async(conversation_id: str, reason: Optional[str]) -> Conversation:
    """Move an ACTIVE conversation into the ASYNC state."""
    convo = get_conversation(conversation_id)
    _transition(convo, ConversationStatus.ASYNC)
    audit_service.record_event(
        conversation_id, "Moved To Async", {"reason": reason}
    )
    return convo


def wrap_up(
    conversation_id: str,
    wrap_up_reason: str,
    disconnect_reason: str,
) -> Conversation:
    """Capture wrap-up details and mark the conversation RESOLVED."""
    convo = get_conversation(conversation_id)
    convo.wrap_up_reason = wrap_up_reason
    convo.disconnect_reason = disconnect_reason
    _transition(convo, ConversationStatus.RESOLVED)
    audit_service.record_event(
        conversation_id,
        "Wrap-Up Captured",
        {"wrap_up_reason": wrap_up_reason, "disconnect_reason": disconnect_reason},
    )
    return convo


def customer_returned(conversation_id: str, text: Optional[str]) -> Conversation:
    """Move a conversation from ASYNC back to RETURNED when the customer returns.

    Notifies the previously assigned agent (mock) and stores the customer's
    optional message.
    """
    convo = get_conversation(conversation_id)
    _transition(convo, ConversationStatus.RETURNED)
    audit_service.record_event(conversation_id, "Customer Returned", {})

    if text:
        message = _add_message(conversation_id, SenderType.CUSTOMER, text)
        audit_service.record_event(
            conversation_id,
            "Customer Message Received",
            {"message_id": message.message_id},
        )

    webex_adapter.notify_previous_agent(conversation_id, convo.assigned_agent)
    return convo
