"""External conversation mapping model.

Maps an internal conversation to *future* Cisco Webex Connect / Webex Engage
identifiers. These fields are mock-compatible placeholders only — they are NOT
guaranteed to match real Cisco API field names yet. Treat them as a seam for a
future integration.

Future external identifiers:
    external_user_id  -> userId   (app/customer user identifier)
    webex_thread_id   -> tid      (Webex Connect thread id)
    webex_chat_id     -> chatId   (Webex Engage chat id)
    webex_team_id     -> teamId   (Engage / team routing id)
    webex_asset_id    -> assetId  (Connect / Engage asset or business id)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ExternalConversationMapping(BaseModel):
    """Links an internal conversation to mock Webex Connect / Engage identifiers."""

    conversation_id: str
    journey_id: str
    customer_id: str
    external_user_id: Optional[str] = None
    webex_thread_id: Optional[str] = None
    webex_chat_id: Optional[str] = None
    webex_team_id: Optional[str] = None
    webex_asset_id: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    def touch(self) -> None:
        """Bump the ``updated_at`` timestamp."""
        self.updated_at = _utcnow()
