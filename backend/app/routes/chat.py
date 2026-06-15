"""Chat routes — the customer/agent facing conversation flow."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.conversation import (
    Conversation,
    CustomerReturnedRequest,
    InboundMessageRequest,
    MoveToAsyncRequest,
    ReplyRequest,
    WrapUpRequest,
)
from app.models.message import Message
from app.services import conversation_service
from app.services.conversation_service import ConversationError, ConversationNotFound

router = APIRouter(prefix="/chat", tags=["chat"])


def _handle(exc: ConversationError) -> HTTPException:
    """Map a service error to an appropriate HTTP error."""
    if isinstance(exc, ConversationNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=409, detail=str(exc))


class ConversationWithMessage(Conversation):
    """Response model returning the conversation plus the message just created."""

    last_message: Message


@router.post("/inbound", response_model=ConversationWithMessage,
             summary="Create a conversation from a customer inbound message")
def inbound(req: InboundMessageRequest) -> ConversationWithMessage:
    convo, message = conversation_service.create_inbound(
        journey_id=req.journey_id,
        customer_id=req.customer_id,
        customer_name=req.customer_name,
        text=req.text,
    )
    return ConversationWithMessage(**convo.model_dump(), last_message=message)


@router.post("/reply", response_model=ConversationWithMessage,
             summary="Add an agent reply to a conversation")
def reply(req: ReplyRequest) -> ConversationWithMessage:
    try:
        convo, message = conversation_service.add_reply(
            req.conversation_id, req.agent_id, req.text
        )
    except ConversationError as exc:
        raise _handle(exc)
    return ConversationWithMessage(**convo.model_dump(), last_message=message)


@router.post("/move-to-async", response_model=Conversation,
             summary="Move a conversation into the ASYNC state")
def move_to_async(req: MoveToAsyncRequest) -> Conversation:
    try:
        return conversation_service.move_to_async(req.conversation_id, req.reason)
    except ConversationError as exc:
        raise _handle(exc)


@router.post("/wrapup", response_model=Conversation,
             summary="Capture wrap-up + disconnect reasons and resolve")
def wrapup(req: WrapUpRequest) -> Conversation:
    try:
        return conversation_service.wrap_up(
            req.conversation_id, req.wrap_up_reason, req.disconnect_reason
        )
    except ConversationError as exc:
        raise _handle(exc)


@router.post("/customer-returned", response_model=Conversation,
             summary="Move a conversation from ASYNC to RETURNED")
def customer_returned(req: CustomerReturnedRequest) -> Conversation:
    try:
        return conversation_service.customer_returned(req.conversation_id, req.text)
    except ConversationError as exc:
        raise _handle(exc)
