"""Authentication tests for the Homework 2 endpoint.

Offline: no Docker, Langfuse, or model provider key.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from server import app as server_app


@pytest.fixture
def sessions(world, tmp_path, monkeypatch):
    """Fresh in-memory sessions and a temp session database for each test."""
    monkeypatch.setattr(server_app, "SESSIONS_DB", tmp_path / "sessions.db")
    monkeypatch.setattr(server_app, "_SESSIONS", {})
    return server_app._SESSIONS


def _create(user_id: int, role: str) -> dict:
    return server_app.create_session(server_app.SessionCreate(user_id=user_id, role=role))


def test_create_session_rejects_role_that_differs_from_database(sessions):
    # User 9002 is a merchant in the database; claiming "support" must fail.
    with pytest.raises(HTTPException) as exc:
        _create(9002, "support")
    assert exc.value.status_code == 403
    assert sessions == {}  # nothing was stored


def test_token_for_one_session_cannot_authorize_another(sessions):
    shopper = _create(1, "shopper")
    merchant = _create(9002, "merchant")

    with pytest.raises(HTTPException) as exc:
        server_app._authorize(merchant["session_id"], f"Bearer {shopper['token']}")
    assert exc.value.status_code == 403

    # The same token still works for the session it was issued for.
    ctx = server_app._authorize(shopper["session_id"], f"Bearer {shopper['token']}")
    assert ctx.user_id == 1 and ctx.role == "shopper"
