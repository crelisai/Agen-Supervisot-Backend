"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import state_service


@pytest.fixture
def client() -> TestClient:
    """A TestClient with a clean in-memory store (no seed data)."""
    with TestClient(app) as c:
        # The lifespan seeds sample data; reset so each test starts clean.
        state_service.reset_state()
        yield c
