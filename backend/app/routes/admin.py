"""Admin / read routes — conversations and audit trail."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.webhook import AuditEvent
from app.services import audit_service, conversation_service, state_service
from app.services.conversation_service import ConversationNotFound

router = APIRouter(tags=["admin"])


class ConversationDetail(Conversation):
    """Conversation plus its messages."""

    messages: list[Message] = []


@router.get("/conversations", response_model=list[Conversation],
            summary="List all conversations")
def list_conversations() -> list[Conversation]:
    return conversation_service.list_conversations()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail,
            summary="Get a single conversation with its messages")
def get_conversation(conversation_id: str) -> ConversationDetail:
    try:
        convo = conversation_service.get_conversation(conversation_id)
    except ConversationNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    messages = conversation_service.get_messages(conversation_id)
    return ConversationDetail(**convo.model_dump(), messages=messages)


@router.get("/audit/{conversation_id}", response_model=list[AuditEvent],
            summary="Get the audit trail for a conversation")
def get_audit(conversation_id: str) -> list[AuditEvent]:
    try:
        conversation_service.get_conversation(conversation_id)
    except ConversationNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return audit_service.get_events(conversation_id)


@router.post("/admin/reset", tags=["admin"],
             summary="Clear all in-memory data (demo helper)")
def reset() -> dict[str, str]:
    state_service.reset_state()
    return {"status": "reset"}
