"""Happy-path tests for every bloomerang @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.bloomerang import (
    TOOLS,
    add_interaction,
    create_constituent,
    create_donation,
    manifest,
)
from modulex_integrations.tools.bloomerang.outputs import (
    AddInteractionOutput,
    CreateConstituentOutput,
    CreateDonationOutput,
)

API = "https://api.bloomerang.co/v2"

_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_constituent(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/constituent",
        json={
            # TODO: fill in a representative response from the Bloomerang API docs
            "Id": 12345,
            "Type": "Individual",
            "FirstName": "Jane",
            "LastName": "Doe",
            "FullName": None,
        },
    )

    result_dict = await create_constituent.ainvoke(
        _args(type="Individual", first_name="Jane", last_name="Doe")
    )

    assert isinstance(result_dict, dict)
    result = CreateConstituentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == 12345

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_create_donation(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/transaction",
        json={
            # TODO: fill in a representative response from the Bloomerang API docs
            "Id": 67890,
            "Amount": 100.0,
            "Date": "2026-01-15",
        },
    )

    result_dict = await create_donation.ainvoke(
        _args(
            constituent_id="12345",
            date="2026-01-15",
            amount="100.00",
            fund_id="1",
            payment_method="Check",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateDonationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == 67890

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_add_interaction(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/interaction",
        json={
            # TODO: fill in a representative response from the Bloomerang API docs
            "Id": 11111,
            "Subject": "Follow-up call",
            "Channel": "Phone",
        },
    )

    result_dict = await add_interaction.ainvoke(
        _args(
            constituent_id="12345",
            date="2026-01-15",
            subject="Follow-up call",
            channel="Phone",
            purpose="Solicitation",
        )
    )

    assert isinstance(result_dict, dict)
    result = AddInteractionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == 11111

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-api-key"] == _API_KEY


@pytest.mark.asyncio
async def test_create_constituent_validates_empty_api_key() -> None:
    result_dict = await create_constituent.ainvoke({"type": "Individual", "api_key": ""})
    result = CreateConstituentOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")
