"""Application configuration.

Plain settings object — no external secrets manager, no .env parsing required
for this demo. Adjust values here if you need to tweak behaviour.
"""

from __future__ import annotations


class Settings:
    """Static application settings for the demo backend."""

    APP_NAME: str = "Async Chat Server Demo Backend"
    APP_DESCRIPTION: str = (
        "Demo backend for an async chat / contact-center flow. "
        "Customer App -> Async Chat Server -> (mock) Webex Connect -> Agent Desktop "
        "-> Webhook Callback -> Async Chat Server -> Customer Notification."
    )
    APP_VERSION: str = "0.1.0"

    # In-memory demo only — no persistence.
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    OPENAPI_URL: str = "/openapi.json"


settings = Settings()
