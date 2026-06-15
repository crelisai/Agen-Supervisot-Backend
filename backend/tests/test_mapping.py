"""Tests for the external conversation mapping layer."""

from __future__ import annotations


def _create(client) -> dict:
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
    return resp.json()


def test_mapping_created_on_inbound(client):
    body = _create(client)
    mapping = body["mapping"]
    assert mapping["conversation_id"] == body["conversation_id"]
    assert mapping["external_user_id"] == "ext-cust-1001"
    assert mapping["webex_thread_id"].startswith("tid-")
    assert mapping["webex_chat_id"].startswith("chat-")
    assert mapping["webex_team_id"] == "team-uob-tmrw-onboarding"
    assert mapping["webex_asset_id"] == "asset-demo"


def test_lookup_by_conversation_id(client):
    body = _create(client)
    conversation_id = body["conversation_id"]
    resp = client.get(f"/mapping/{conversation_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["conversation_id"] == conversation_id


def test_lookup_by_webex_thread_id(client):
    body = _create(client)
    thread_id = body["mapping"]["webex_thread_id"]
    resp = client.get(f"/mapping/webex-thread/{thread_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["webex_thread_id"] == thread_id
    assert resp.json()["conversation_id"] == body["conversation_id"]


def test_lookup_by_webex_chat_id(client):
    body = _create(client)
    chat_id = body["mapping"]["webex_chat_id"]
    resp = client.get(f"/mapping/webex-chat/{chat_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["webex_chat_id"] == chat_id
    assert resp.json()["conversation_id"] == body["conversation_id"]


def test_lookup_missing_mapping_returns_404(client):
    assert client.get("/mapping/nope").status_code == 404
    assert client.get("/mapping/webex-thread/nope").status_code == 404
    assert client.get("/mapping/webex-chat/nope").status_code == 404


def test_send_to_webex_payload_shape_in_audit(client):
    body = _create(client)
    conversation_id = body["conversation_id"]
    audit = client.get(f"/audit/{conversation_id}").json()
    sent = [e for e in audit if e["event_type"] == "Sent To Webex Connect"]
    assert sent, "expected a 'Sent To Webex Connect' audit event"
    payload = sent[0]["details"]["payload"]
    for field in ("datetime", "message", "userId", "tid", "chatId"):
        assert field in payload
    assert payload["userId"] == "ext-cust-1001"
    assert payload["tid"] == body["mapping"]["webex_thread_id"]
    assert payload["chatId"] == body["mapping"]["webex_chat_id"]
