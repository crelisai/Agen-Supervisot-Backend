"""Webhook routes — mock Cisco Webex Connect callback endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.models.conversation import ConversationStatus
from app.models.webhook import WebexEventType, WebexWebhookRequest
from app.services import conversation_service, webex_adapter
from app.services.conversation_service import ConversationError, ConversationNotFound

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/webex", summary="Mock Cisco Webex Connect webhook callback")
def webex(req: WebexWebhookRequest) -> dict[str, Any]:
    """Receive a (mock) Webex Connect callback and apply its effect.

    Supported events:
      * AGENT_ASSIGNED       -> assign the agent
      * AGENT_MESSAGE        -> add an agent reply
      * CONVERSATION_RESOLVED-> wrap up / resolve
      * CUSTOMER_NOTIFIED    -> audit only
    """
    # Validate the conversation exists before doing anything.
    try:
        conversation_service.get_conversation(req.conversation_id)
    except ConversationNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    # Always record receipt of the webhook.
    webex_adapter.receive_webhook(
        req.conversation_id,
        req.event_type.value,
        {"agent_id": req.agent_id, "text": req.text, "metadata": req.metadata},
    )

    try:
        if req.event_type == WebexEventType.AGENT_ASSIGNED and req.agent_id:
            webex_adapter.assign_agent(req.conversation_id, req.agent_id)
            convo = conversation_service.get_conversation(req.conversation_id)
            convo.assigned_agent = req.agent_id
            convo.touch()

        elif req.event_type == WebexEventType.AGENT_MESSAGE and req.text:
            conversation_service.add_reply(
                req.conversation_id, req.agent_id or "webex-agent", req.text
            )

        elif req.event_type == WebexEventType.CONVERSATION_RESOLVED:
            convo = conversation_service.get_conversation(req.conversation_id)
            if convo.status != ConversationStatus.RESOLVED:
                conversation_service.wrap_up(
                    req.conversation_id,
                    wrap_up_reason="Resolved via Webex webhook",
                    disconnect_reason="Webex callback",
                )
    except ConversationError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    convo = conversation_service.get_conversation(req.conversation_id)
    return {
        "status": "ok",
        "event_type": req.event_type.value,
        "conversation_id": req.conversation_id,
        "conversation_status": convo.status.value,
    }
