"""Seed the in-memory stores with a couple of demo conversations.

Called on application startup so Swagger UI / GET endpoints have something to
show immediately. Safe to skip — the app works fine with empty stores.
"""

from __future__ import annotations

from app.services import conversation_service


def seed_sample_data() -> None:
    """Create a small set of representative conversations."""
    # Fresh inbound from the UOB TMRW journey.
    conversation_service.create_inbound(
        journey_id="uob-tmrw-onboarding",
        customer_id="cust-1001",
        customer_name="Jane Tan",
        text="Hi, I'd like help opening a savings account.",
    )

    # A conversation that has progressed into ASYNC (waiting on the customer).
    convo, _, _ = conversation_service.create_inbound(
        journey_id="giybug-support",
        customer_id="cust-2002",
        customer_name="Arjun Rao",
        text="My card payment failed, can you check?",
    )
    conversation_service.add_reply(
        convo.conversation_id,
        agent_id="agent-7",
        text="Looking into it now — could you send your last statement?",
    )
    conversation_service.move_to_async(
        convo.conversation_id, reason="Awaiting statement from customer"
    )
