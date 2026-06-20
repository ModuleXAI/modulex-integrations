"""Happy-path tests per action + failure-path and empty-credential tests.

Twilio doesn't raise on logical errors — the tools wrap everything and
return ``success=False`` + ``error``. HTTP is mocked with pytest-httpx.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.twilio_voice import (
    TOOLS,
    get_recording,
    list_calls,
    make_call,
    manifest,
)
from modulex_integrations.tools.twilio_voice.outputs import (
    GetRecordingOutput,
    ListCallsOutput,
    MakeCallOutput,
)

API = "https://api.twilio.com/2010-04-01"
_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
_AUTH_TOKEN = "fake-auth-token"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(account_sid=_ACCOUNT_SID, api_key=_AUTH_TOKEN, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo_is_themed(self) -> None:
        assert manifest.logo == "modulex:twilio_voice-themed"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_make_call(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/Accounts/{_ACCOUNT_SID}/Calls.json",
        json={
            "sid": "CA1234567890",
            "status": "queued",
            "direction": "outbound-api",
            "from": "+14155559876",
            "to": "+14155551234",
            "duration": None,
            "price": None,
            "price_unit": "USD",
        },
    )

    result_dict = await make_call.ainvoke(
        _args(
            to="+14155551234",
            from_="+14155559876",
            twiml="<Response><Say>Hello</Say></Response>",
        )
    )

    assert isinstance(result_dict, dict)

    result = MakeCallOutput.model_validate(result_dict)
    assert result.success is True
    assert result.call_sid == "CA1234567890"
    assert result.status == "queued"
    assert result.direction == "outbound-api"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"].startswith("Basic ")
    body = sent.content.decode()
    assert "To=%2B14155551234" in body
    assert "Twiml=" in body


@pytest.mark.asyncio
async def test_list_calls(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/Accounts/{_ACCOUNT_SID}/Calls.json?Status=completed",
        json={
            "calls": [
                {
                    "sid": "CA0001",
                    "from": "+14155559876",
                    "to": "+14155551234",
                    "status": "completed",
                    "direction": "outbound-api",
                    "duration": "42",
                    "price": "-0.013",
                    "price_unit": "USD",
                    "start_time": "Mon, 01 Jan 2025 00:00:00 +0000",
                    "end_time": "Mon, 01 Jan 2025 00:00:42 +0000",
                    "date_created": "Mon, 01 Jan 2025 00:00:00 +0000",
                    "subresource_uris": {
                        "recordings": (
                            f"/2010-04-01/Accounts/{_ACCOUNT_SID}/Calls/CA0001/Recordings.json"
                        )
                    },
                }
            ],
            "page": 0,
            "page_size": 50,
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"https://api.twilio.com/2010-04-01/Accounts/{_ACCOUNT_SID}/Calls/CA0001/Recordings.json",
        json={"recordings": [{"sid": "RE9999"}]},
    )

    result_dict = await list_calls.ainvoke(_args(status="completed"))

    assert isinstance(result_dict, dict)

    result = ListCallsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1
    assert result.calls[0].call_sid == "CA0001"
    assert result.calls[0].duration == 42
    assert result.calls[0].recording_sids == ["RE9999"]
    assert result.page == 0
    assert result.page_size == 50


@pytest.mark.asyncio
async def test_list_calls_without_recordings_fetch(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/Accounts/{_ACCOUNT_SID}/Calls.json",
        json={
            "calls": [
                {
                    "sid": "CA0002",
                    "from": "+1",
                    "to": "+2",
                    "status": "completed",
                    "direction": "inbound",
                    "duration": "10",
                    "subresource_uris": {"recordings": "/whatever.json"},
                }
            ],
            "page": 0,
            "page_size": 50,
        },
    )

    result_dict = await list_calls.ainvoke(_args(include_recordings=False))

    assert isinstance(result_dict, dict)
    result = ListCallsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.calls[0].recording_sids == []
    # Only the list request fired; no recordings sub-fetch.
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_get_recording(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/Accounts/{_ACCOUNT_SID}/Recordings/RE9999.json",
        json={
            "sid": "RE9999",
            "call_sid": "CA0001",
            "duration": "42",
            "status": "completed",
            "channels": 1,
            "source": "RecordVerb",
            "price": "-0.0025",
            "price_unit": "USD",
            "uri": f"/2010-04-01/Accounts/{_ACCOUNT_SID}/Recordings/RE9999.json",
            "media_url": (
                f"https://api.twilio.com/2010-04-01/Accounts/{_ACCOUNT_SID}/Recordings/RE9999"
            ),
        },
    )

    result_dict = await get_recording.ainvoke(_args(recording_sid="RE9999"))

    assert isinstance(result_dict, dict)

    result = GetRecordingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.recording_sid == "RE9999"
    assert result.call_sid == "CA0001"
    assert result.duration == 42
    assert result.channels == 1
    assert result.media_url is not None


@pytest.mark.asyncio
async def test_get_recording_media_url_fallback(httpx_mock):  # type: ignore[no-untyped-def]
    """When media_url is absent, it is derived from the recording uri."""
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/Accounts/{_ACCOUNT_SID}/Recordings/RE8888.json",
        json={
            "sid": "RE8888",
            "uri": f"/2010-04-01/Accounts/{_ACCOUNT_SID}/Recordings/RE8888.json",
        },
    )

    result_dict = await get_recording.ainvoke(_args(recording_sid="RE8888"))
    result = GetRecordingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.media_url == (
        f"https://api.twilio.com/2010-04-01/Accounts/{_ACCOUNT_SID}/Recordings/RE8888"
    )


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_make_call_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/Accounts/{_ACCOUNT_SID}/Calls.json",
        status_code=400,
        json={"code": 21205, "message": "Url is not a valid URL"},
    )

    result_dict = await make_call.ainvoke(
        _args(to="+14155551234", from_="+14155559876", url="not-a-url")
    )

    assert isinstance(result_dict, dict)
    result = MakeCallOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Url is not a valid URL" in result.error


@pytest.mark.asyncio
async def test_make_call_requires_url_or_twiml() -> None:
    result_dict = await make_call.ainvoke(
        _args(to="+14155551234", from_="+14155559876")
    )
    result = MakeCallOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "url" in result.error.lower() or "twiml" in result.error.lower()


# --- Empty-credential paths ------------------------------------------------


@pytest.mark.asyncio
async def test_make_call_validates_empty_api_key() -> None:
    result_dict = await make_call.ainvoke(
        {
            "to": "+14155551234",
            "from_": "+14155559876",
            "account_sid": _ACCOUNT_SID,
            "api_key": "",
            "twiml": "<Response/>",
        }
    )
    result = MakeCallOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Auth Token" in result.error


@pytest.mark.asyncio
async def test_list_calls_validates_empty_api_key() -> None:
    result_dict = await list_calls.ainvoke(
        {"account_sid": _ACCOUNT_SID, "api_key": "   "}
    )
    result = ListCallsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_get_recording_validates_empty_api_key() -> None:
    result_dict = await get_recording.ainvoke(
        {"recording_sid": "RE9999", "account_sid": _ACCOUNT_SID, "api_key": ""}
    )
    result = GetRecordingOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
