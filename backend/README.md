# Async Chat Server — Demo Backend

A small **FastAPI** backend that demonstrates an asynchronous chat / contact-center
flow for a bank use case (UOB TMRW / GIYBUG style). It is a **demo only**:
everything is stored **in memory** (plain Python dictionaries) and the Cisco Webex
Connect integration is **mocked**.

## Architecture

```
Customer Mobile App (UOB TMRW / GIYBUG)
        │
        ▼
  Async Chat Server   ◀── this backend
        │
        ▼
  Cisco Webex Connect (mocked: webex_adapter.py)
        │
        ▼
   Agent Desktop
        │
        ▼
  Webhook Callback  ──▶ POST /webhook/webex
        │
        ▼
  Async Chat Server
        │
        ▼
  Customer Notification
```

### Conversation state machine

```
NEW → QUEUED → ASSIGNED → ACTIVE → ASYNC → RETURNED → RESOLVED → CLOSED
```

| State     | Meaning                                              |
|-----------|------------------------------------------------------|
| NEW       | Just created from a customer inbound message         |
| QUEUED    | Handed off to (mock) Webex Connect for routing       |
| ASSIGNED  | An agent has been assigned                           |
| ACTIVE    | Agent and customer are chatting                      |
| ASYNC     | Parked, waiting on the customer (out-of-session)     |
| RETURNED  | Customer came back to an ASYNC conversation          |
| RESOLVED  | Wrapped up (wrap-up + disconnect reasons captured)   |
| CLOSED    | Terminal                                             |

Invalid transitions are rejected with HTTP `409`.

## Project structure

```
backend/
├── app/
│   ├── main.py                # FastAPI app + startup seed
│   ├── config.py              # static settings
│   ├── models/                # Pydantic v2 models
│   │   ├── conversation.py    # Conversation + state enum + request bodies
│   │   ├── message.py         # Message + SenderType
│   │   └── webhook.py         # AuditEvent + Webex webhook payloads
│   ├── services/
│   │   ├── conversation_service.py  # orchestration / use cases
│   │   ├── state_service.py         # in-memory stores + transition rules
│   │   ├── audit_service.py         # audit trail
│   │   └── webex_adapter.py         # MOCK Webex Connect adapter
│   ├── routes/
│   │   ├── chat.py            # /chat/*
│   │   ├── webhook.py         # /webhook/webex
│   │   └── admin.py           # /conversations, /audit, /admin/reset
│   └── data/
│       └── sample_data.py     # demo seed data
├── tests/
├── requirements.txt
└── README.md
```

## Setup

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

- Swagger UI:  http://127.0.0.1:8000/docs
- ReDoc:       http://127.0.0.1:8000/redoc
- OpenAPI:     http://127.0.0.1:8000/openapi.json

The app seeds two demo conversations on startup.

## Test

```bash
cd backend
pytest -q
```

## Endpoints

| Method | Path                              | Purpose                                  |
|--------|-----------------------------------|------------------------------------------|
| GET    | `/`                               | Health check / service info              |
| POST   | `/chat/inbound`                   | Create a conversation + customer message |
| POST   | `/chat/reply`                     | Add an agent reply                       |
| POST   | `/chat/move-to-async`             | Move conversation to ASYNC               |
| POST   | `/chat/wrapup`                    | Capture wrap-up + disconnect reasons     |
| POST   | `/chat/customer-returned`         | ASYNC → RETURNED                         |
| POST   | `/webhook/webex`                  | Mock Cisco Webex Connect webhook         |
| GET    | `/conversations`                  | List all conversations                   |
| GET    | `/conversations/{id}`             | Conversation detail + messages           |
| GET    | `/audit/{id}`                     | Audit trail for a conversation           |
| POST   | `/admin/reset`                    | Clear all in-memory data (demo helper)   |

## Sample curl commands

> On Windows PowerShell, prefer `curl.exe` (or `Invoke-RestMethod`) to avoid the
> `curl` alias.

Create a conversation:

```bash
curl -s -X POST http://127.0.0.1:8000/chat/inbound \
  -H "Content-Type: application/json" \
  -d '{"journey_id":"uob-tmrw-onboarding","customer_id":"cust-1001","customer_name":"Jane Tan","text":"Hi, I need help."}'
```

Agent reply (use the conversation_id returned above):

```bash
curl -s -X POST http://127.0.0.1:8000/chat/reply \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"<ID>","agent_id":"agent-7","text":"Sure, happy to help."}'
```

Move to async:

```bash
curl -s -X POST http://127.0.0.1:8000/chat/move-to-async \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"<ID>","reason":"Awaiting customer documents"}'
```

Customer returns:

```bash
curl -s -X POST http://127.0.0.1:8000/chat/customer-returned \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"<ID>","text":"I am back with the docs."}'
```

Wrap up:

```bash
curl -s -X POST http://127.0.0.1:8000/chat/wrapup \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"<ID>","wrap_up_reason":"Issue resolved","disconnect_reason":"Customer ended chat"}'
```

Mock Webex webhook:

```bash
curl -s -X POST http://127.0.0.1:8000/webhook/webex \
  -H "Content-Type: application/json" \
  -d '{"conversation_id":"<ID>","event_type":"AGENT_MESSAGE","agent_id":"agent-9","text":"Reply via Webex"}'
```

Read the audit trail:

```bash
curl -s http://127.0.0.1:8000/audit/<ID>
```

## Notes for future Webex Connect integration

`app/services/webex_adapter.py` is the seam. Each function (`send_to_webex_connect`,
`assign_agent`, `notify_previous_agent`, `receive_webhook`) currently only logs and
writes an audit event. Swap the bodies for real Webex Connect REST/SDK calls — the
rest of the app does not need to change.
