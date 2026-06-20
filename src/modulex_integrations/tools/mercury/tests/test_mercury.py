"""Happy-path tests for every mercury @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.mercury import (
    TOOLS,
    get_account_info,
    manifest,
)
from modulex_integrations.tools.mercury.outputs import (
    GetAccountInfoOutput,
)

API = "https://backend.mercury.com/api/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "fake_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_1_action(self) -> None:
        assert len(manifest.actions) == 1

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_bearer_token_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"bearer_token"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_get_account_info(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/account/acct_123",
        json={
            # TODO: fill in a representative response shape from the Mercury API docs
            "id": "acct_123",
            "name": "Mercury Checking",
            "status": "active",
            "type": "checking",
            "currentBalance": 50000.00,
            "availableBalance": 49000.00,
            "routingNumber": "084106768",
            "accountNumber": "1234567890",
            "createdAt": "2023-01-15T00:00:00Z",
        },
    )

    result_dict = await get_account_info.ainvoke(_args(account_id="acct_123"))

    assert isinstance(result_dict, dict)
    result = GetAccountInfoOutput.model_validate(result_dict)
    assert result.success is True
    assert result.account_id == "acct_123"
    assert result.name == "Mercury Checking"
    assert result.current_balance == 50000.00


@pytest.mark.asyncio
async def test_get_account_info_missing_token(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await get_account_info.ainvoke(
        {"auth_type": "bearer_token", "auth_data": {}, "account_id": "acct_123"}
    )

    assert isinstance(result_dict, dict)
    result = GetAccountInfoOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "token" in result.error.lower()
