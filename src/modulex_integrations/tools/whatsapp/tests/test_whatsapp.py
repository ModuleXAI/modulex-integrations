"""Happy-path test for ``send_message`` + failure-path tests for the
non-2xx -> success=False branch and the empty-credential short-circuit
(WhatsApp's tool does not raise on errors)."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.whatsapp import (
    TOOLS,
    manifest,
    send_message,
)
from modulex_integrations.tools.whatsapp.outputs import SendMessageOutput

API = "https://graph.facebook.com/v25.0"
_API_KEY = "fake-access-token"
_PHONE_NUMBER_ID = "123456789012345"
_SEND_URL = f"{API}/{_PHONE_NUMBER_ID}/messages"


def _args(**extra: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "api_key": _API_KEY,
        "phone_number_id": _PHONE_NUMBER_ID,
        "phone_number": "+14155552671",
        "message": "Hello from ModuleX",
    }
    base.update(extra)
    return base


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_1_action(self) -> None:
        assert len(manifest.actions) == 1

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo_is_themed(self) -> None:
        assert manifest.logo == "modulex:whatsapp-themed"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=_SEND_URL,
        json={
            "messaging_product": "whatsapp",
            "contacts": [
                {"input": "+14155552671", "wa_id": "14155552671"}
            ],
            "messages": [
                {"id": "wamid.HBgL123", "message_status": "accepted"}
            ],
        },
    )

    result_dict = await send_message.ainvoke(_args(preview_url=True))

    assert isinstance(result_dict, dict)

    result = SendMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "wamid.HBgL123"
    assert result.message_status == "accepted"
    assert result.messaging_product == "whatsapp"
    assert result.input_phone_number == "+14155552671"
    assert result.whatsapp_user_id == "14155552671"
    assert result.contacts[0].input == "+14155552671"
    assert result.contacts[0].wa_id == "14155552671"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"
    body = sent.read().decode()
    assert '"messaging_product": "whatsapp"' in body or '"messaging_product":"whatsapp"' in body
    assert "preview_url" in body


@pytest.mark.asyncio
async def test_send_message_without_preview_omits_preview_url(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=_SEND_URL,
        json={
            "messaging_product": "whatsapp",
            "contacts": [{"input": "+14155552671", "wa_id": "14155552671"}],
            "messages": [{"id": "wamid.HBgL999"}],
        },
    )

    result_dict = await send_message.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = SendMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "wamid.HBgL999"
    assert result.message_status is None

    body = httpx_mock.get_requests()[0].read().decode()
    assert "preview_url" not in body


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    """WhatsApp errors come back as HTTP 4xx/5xx; the tool wraps them in
    ``success=False`` + ``error`` rather than raising."""
    httpx_mock.add_response(
        method="POST",
        url=_SEND_URL,
        status_code=401,
        json={"error": {"message": "Invalid OAuth access token."}},
    )

    result_dict = await send_message.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = SendMessageOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error
    assert "Invalid OAuth access token." in result.error


@pytest.mark.asyncio
async def test_send_message_missing_message_id(httpx_mock):  # type: ignore[no-untyped-def]
    """A 200 with no message ID is reported as a failure, mirroring the
    upstream contract that a send without an id did not succeed."""
    httpx_mock.add_response(
        method="POST",
        url=_SEND_URL,
        json={"messaging_product": "whatsapp", "contacts": [], "messages": []},
    )

    result_dict = await send_message.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = SendMessageOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "message ID" in result.error


@pytest.mark.asyncio
async def test_send_message_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await send_message.ainvoke(_args(api_key=""))

    assert isinstance(result_dict, dict)
    result = SendMessageOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access token" in result.error
