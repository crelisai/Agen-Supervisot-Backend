"""End-to-end-ish tests for the async chat flow over the HTTP API."""

from __future__ import annotations


def _create_conversation(client) -> str:
    resp = client.post(
        "/chat/inbound",
        json={
            "journey_id": "uob-tmrw-onboarding",
            "customer_id": "cust-1001",
            "customer_name": "Jane Tan",
            "text": "Hi, I need help.",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["conversation_id"]


def test_conversation_creation(client):
    resp = client.post(
        "/chat/inbound",
        json={
            "journey_id": "uob-tmrw-onboarding",
            "customer_id": "cust-1001",
            "customer_name": "Jane Tan",
            "text": "Hi, I need help.",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["conversation_id"].startswith("conv-")
    # NEW -> QUEUED happens automatically on inbound.
    assert body["status"] == "QUEUED"
    assert body["last_message"]["sender_type"] == "CUSTOMER"

    # It shows up in the list.
    listing = client.get("/conversations").json()
    assert len(listing) == 1


def test_move_to_async(client):
    conversation_id = _create_conversation(client)

    # Agent replies -> conversation becomes ACTIVE.
    reply = client.post(
        "/chat/reply",
        json={"conversation_id": conversation_id, "agent_id": "agent-7", "text": "Hello!"},
    )
    assert reply.status_code == 200, reply.text
    assert reply.json()["status"] == "ACTIVE"
    assert reply.json()["assigned_agent"] == "agent-7"

    # Move to ASYNC.
    resp = client.post(
        "/chat/move-to-async",
        json={"conversation_id": conversation_id, "reason": "Awaiting docs"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "ASYNC"


def test_customer_returned(client):
    conversation_id = _create_conversation(client)
    client.post(
        "/chat/reply",
        json={"conversation_id": conversation_id, "agent_id": "agent-7", "text": "Hi"},
    )
    client.post(
        "/chat/move-to-async",
        json={"conversation_id": conversation_id, "reason": "Awaiting docs"},
    )

    resp = client.post(
        "/chat/customer-returned",
        json={"conversation_id": conversation_id, "text": "I'm back"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "RETURNED"


def test_invalid_transition_is_rejected(client):
    conversation_id = _create_conversation(client)
    # Cannot move to ASYNC directly from QUEUED.
    resp = client.post(
        "/chat/move-to-async",
        json={"conversation_id": conversation_id, "reason": "too soon"},
    )
    assert resp.status_code == 409


def test_audit_generation(client):
    conversation_id = _create_conversation(client)
    client.post(
        "/chat/reply",
        json={"conversation_id": conversation_id, "agent_id": "agent-7", "text": "Hi"},
    )
    client.post(
        "/chat/move-to-async",
        json={"conversation_id": conversation_id, "reason": "Awaiting docs"},
    )

    audit = client.get(f"/audit/{conversation_id}")
    assert audit.status_code == 200, audit.text
    event_types = [e["event_type"] for e in audit.json()]
    assert "Conversation Created" in event_types
    assert "Moved To Async" in event_types
    assert "Sent To Webex Connect" in event_types


def test_webhook_received(client):
    conversation_id = _create_conversation(client)
    resp = client.post(
        "/webhook/webex",
        json={
            "conversation_id": conversation_id,
            "event_type": "AGENT_MESSAGE",
            "agent_id": "agent-9",
            "text": "Reply from Webex",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["conversation_status"] == "ACTIVE"

    audit = client.get(f"/audit/{conversation_id}").json()
    assert "Webhook Received" in [e["event_type"] for e in audit]
