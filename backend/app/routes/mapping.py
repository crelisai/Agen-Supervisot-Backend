"""Mapping routes — look up external Webex Connect / Engage identifiers."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.mapping import ExternalConversationMapping
from app.services import mapping_service

router = APIRouter(prefix="/mapping", tags=["mapping"])


@router.get("/{conversation_id}", response_model=ExternalConversationMapping,
            summary="Get the external mapping for a conversation")
def get_by_conversation(conversation_id: str) -> ExternalConversationMapping:
    mapping = mapping_service.get_mapping_by_conversation(conversation_id)
    if mapping is None:
        raise HTTPException(
            status_code=404,
            detail=f"No mapping for conversation '{conversation_id}'",
        )
    return mapping


@router.get("/webex-thread/{thread_id}", response_model=ExternalConversationMapping,
            summary="Get the mapping by Webex Connect thread id (tid)")
def get_by_webex_thread(thread_id: str) -> ExternalConversationMapping:
    mapping = mapping_service.get_mapping_by_webex_thread(thread_id)
    if mapping is None:
        raise HTTPException(
            status_code=404, detail=f"No mapping for webex thread '{thread_id}'"
        )
    return mapping


@router.get("/webex-chat/{chat_id}", response_model=ExternalConversationMapping,
            summary="Get the mapping by Webex Engage chat id (chatId)")
def get_by_webex_chat(chat_id: str) -> ExternalConversationMapping:
    mapping = mapping_service.get_mapping_by_webex_chat(chat_id)
    if mapping is None:
        raise HTTPException(
            status_code=404, detail=f"No mapping for webex chat '{chat_id}'"
        )
    return mapping
