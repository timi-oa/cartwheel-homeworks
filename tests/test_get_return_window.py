"""The student-added get_return_window tool (HW1 Part A), tested offline."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent import tools
from agent.agent import TOOLS_BY_ROLE
from agent.auth import AuthContext

SHOPPER_1 = AuthContext(user_id=1, role="shopper")


def test_override_store_returns_store_window_and_cites_store_policy(world: dict) -> None:
    result = tools.get_return_window(SHOPPER_1, 7)  # Northwind Books, 45 days
    assert result["ok"] is True
    assert result["return_window_days"] == 45
    assert result["source"] == "store_override"
    assert result["policy_id"] == "store-northwind-books-policy"
    assert result["counts_from_policy_id"] == "cw-returns"


def test_store_without_override_returns_platform_default(world: dict) -> None:
    result = tools.get_return_window(SHOPPER_1, 1)  # Blue Heron Ceramics
    assert result["ok"] is True
    assert result["return_window_days"] == 30
    assert result["source"] == "platform_default"
    assert result["policy_id"] == "cw-returns"


def test_stricter_override_is_returned_not_the_default(world: dict) -> None:
    result = tools.get_return_window(SHOPPER_1, 13)  # Saltbox Pantry, 7 days
    assert result["return_window_days"] == 7
    assert result["policy_id"] == "store-saltbox-pantry-policy"


def test_unknown_store_is_not_found(world: dict) -> None:
    result = tools.get_return_window(SHOPPER_1, 999999)
    assert result["ok"] is False
    assert result["error"] == "not_found"


def test_missing_policy_doc_is_never_cited(
    world: dict, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    empty = tmp_path / "policies"
    empty.mkdir()
    monkeypatch.setenv("CARTWHEEL_POLICIES_DIR", str(empty))
    result = tools.get_return_window(SHOPPER_1, 7)
    assert result["ok"] is False
    assert result["error"] == "policy_unavailable"


@pytest.mark.parametrize("role", ["shopper", "merchant", "support"])
def test_tool_is_registered_for_every_role(role: str) -> None:
    names = {getattr(t, "name", None) for t in TOOLS_BY_ROLE[role]}
    assert "get_return_window" in names


def test_lookup_by_store_name_matches_lookup_by_id(world: dict) -> None:
    by_name = tools.get_return_window(SHOPPER_1, store_name="northwind books")
    by_id = tools.get_return_window(SHOPPER_1, 7)
    assert by_name == by_id
    assert by_name["return_window_days"] == 45


def test_unknown_store_name_is_not_found(world: dict) -> None:
    result = tools.get_return_window(SHOPPER_1, store_name="No Such Store")
    assert result["ok"] is False
    assert result["error"] == "not_found"


def test_no_store_given_is_invalid_input(world: dict) -> None:
    result = tools.get_return_window(SHOPPER_1)
    assert result["ok"] is False
    assert result["error"] == "invalid_input"
