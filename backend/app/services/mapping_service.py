"""External conversation mapping service.

Stores and looks up :class:`ExternalConversationMapping` records in memory. This
is the seam for a future Webex Connect / Engage integration — mapping field
values are mock-generated for now.
"""

from __future__ import annotations

import uuid
from typing import Optional

from app.models.mapping import ExternalConversationMapping
from app.services import state_service


def generate_webex_thread_id() -> str:
    """Generate a mock Webex Connect thread id (``tid``)."""
    return f"tid-{uuid.uuid4().hex[:16]}"


def generate_webex_chat_id() -> str:
    """Generate a mock Webex Engage chat id (``chatId``)."""
    return f"chat-{uuid.uuid4().hex[:16]}"


def create_mapping(
    conversation_id: str,
    journey_id: str,
    customer_id: str,
    external_user_id: Optional[str] = None,
    webex_thread_id: Optional[str] = None,
    webex_chat_id: Optional[str] = None,
    webex_team_id: Optional[str] = None,
    webex_asset_id: Optional[str] = None,
) -> ExternalConversationMapping:
    """Create and store a mapping for a conversation."""
    mapping = ExternalConversationMapping(
        conversation_id=conversation_id,
        journey_id=journey_id,
        customer_id=customer_id,
        external_user_id=external_user_id,
        webex_thread_id=webex_thread_id,
        webex_chat_id=webex_chat_id,
        webex_team_id=webex_team_id,
        webex_asset_id=webex_asset_id,
    )
    state_service.mappings[conversation_id] = mapping
    return mapping


def get_mapping_by_conversation(conversation_id: str) -> Optional[ExternalConversationMapping]:
    """Return the mapping for a conversation, or ``None``."""
    return state_service.mappings.get(conversation_id)


def get_mapping_by_webex_thread(thread_id: str) -> Optional[ExternalConversationMapping]:
    """Return the mapping whose ``webex_thread_id`` matches, or ``None``."""
    for mapping in state_service.mappings.values():
        if mapping.webex_thread_id == thread_id:
            return mapping
    return None


def get_mapping_by_webex_chat(chat_id: str) -> Optional[ExternalConversationMapping]:
    """Return the mapping whose ``webex_chat_id`` matches, or ``None``."""
    for mapping in state_service.mappings.values():
        if mapping.webex_chat_id == chat_id:
            return mapping
    return None


def update_mapping(
    conversation_id: str,
    **fields: object,
) -> Optional[ExternalConversationMapping]:
    """Patch fields on an existing mapping.

    Only known, non-``None`` fields are applied. Returns the updated mapping, or
    ``None`` if no mapping exists for the conversation.
    """
    mapping = state_service.mappings.get(conversation_id)
    if mapping is None:
        return None

    updatable = {
        "external_user_id",
        "webex_thread_id",
        "webex_chat_id",
        "webex_team_id",
        "webex_asset_id",
    }
    changed = False
    for key, value in fields.items():
        if key in updatable and value is not None:
            setattr(mapping, key, value)
            changed = True
    if changed:
        mapping.touch()
    return mapping
