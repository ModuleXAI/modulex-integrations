"""Happy-path tests for every twilio @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.twilio import (
    TOOLS,
    check_verification_token,
    create_verification_service,
    delete_call,
    delete_message,
    download_recording_media,
    get_call,
    get_message,
    get_transcripts,
    list_calls,
    list_message_media,
    list_messages,
    list_phone_numbers,
    list_transcripts,
    make_phone_call,
    manifest,
    phone_number_lookup,
    send_message,
    send_sms_verification,
)
from modulex_integrations.tools.twilio.outputs import (
    CheckVerificationTokenOutput,
    CreateVerificationServiceOutput,
    DeleteCallOutput,
    DeleteMessageOutput,
    DownloadRecordingMediaOutput,
    GetCallOutput,
    GetMessageOutput,
    GetTranscriptsOutput,
    ListCallsOutput,
    ListMessageMediaOutput,
    ListMessagesOutput,
    ListPhoneNumbersOutput,
    ListTranscriptsOutput,
    MakePhoneCallOutput,
    PhoneNumberLookupOutput,
    SendMessageOutput,
    SendSmsVerificationOutput,
)

API = "https://api.twilio.com/2010-04-01"
LOOKUP_API = "https://lookups.twilio.com"
VERIFY_API = "https://verify.twilio.com"
INTELLIGENCE_API = "https://intelligence.twilio.com"

_ACCT = "ACfake00000000000000000000000000"

_AUTH: dict[str, Any] = {
    "auth_type": "custom",
    "auth_data": {"account_sid": _ACCT, "auth_token": "fake_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_17_actions(self) -> None:
        assert len(manifest.actions) == 17

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_custom_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"custom"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_send_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/Accounts/{_ACCT}/Messages.json",
        json={
            # TODO: fill in a representative response from Twilio SMS API
            "sid": "SMfake",
            "status": "queued",
            "to": "+16175551212",
            "from": "+15551234567",
            "body": "Hello",
        },
    )

    result_dict = await send_message.ainvoke(
        _args(from_number="+15551234567", to="+16175551212", body="Hello")
    )

    assert isinstance(result_dict, dict)
    result = SendMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message is not None
    assert result.message.sid == "SMfake"


@pytest.mark.asyncio
async def test_make_phone_call(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/Accounts/{_ACCT}/Calls.json",
        json={
            # TODO: fill in a representative response from Twilio Voice API
            "sid": "CAfake",
            "status": "queued",
            "to": "+16175551212",
            "from": "+15551234567",
        },
    )

    result_dict = await make_phone_call.ainvoke(
        _args(
            from_number="+15551234567",
            to="+16175551212",
            call_type="text",
            text="Hello from ModuleX",
        )
    )

    assert isinstance(result_dict, dict)
    result = MakePhoneCallOutput.model_validate(result_dict)
    assert result.success is True
    assert result.call is not None
    assert result.call.sid == "CAfake"


@pytest.mark.asyncio
async def test_get_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/Accounts/{_ACCT}/Messages/SMfake.json",
        json={
            # TODO: fill in a representative response
            "sid": "SMfake",
            "body": "Hello",
            "status": "delivered",
        },
    )

    result_dict = await get_message.ainvoke(_args(message_id="SMfake"))

    assert isinstance(result_dict, dict)
    result = GetMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message is not None


@pytest.mark.asyncio
async def test_delete_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/Accounts/{_ACCT}/Messages/SMfake.json",
        status_code=204,
    )

    result_dict = await delete_message.ainvoke(_args(message_id="SMfake"))

    assert isinstance(result_dict, dict)
    result = DeleteMessageOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_messages(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/Accounts/{_ACCT}/Messages.json?PageSize=50",
        json={
            # TODO: fill in a representative response
            "messages": [
                {"sid": "SM1", "body": "Hello", "status": "delivered"},
                {"sid": "SM2", "body": "World", "status": "delivered"},
            ],
        },
    )

    result_dict = await list_messages.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListMessagesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.messages) == 2


@pytest.mark.asyncio
async def test_list_message_media(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/Accounts/{_ACCT}/Messages/SMfake/Media.json?PageSize=50",
        json={
            # TODO: fill in a representative response
            "media_list": [
                {"sid": "ME1", "content_type": "image/jpeg"},
            ],
        },
    )

    result_dict = await list_message_media.ainvoke(_args(message_id="SMfake"))

    assert isinstance(result_dict, dict)
    result = ListMessageMediaOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.media) == 1


@pytest.mark.asyncio
async def test_get_call(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/Accounts/{_ACCT}/Calls/CAfake.json",
        json={
            # TODO: fill in a representative response
            "sid": "CAfake",
            "status": "completed",
            "duration": "30",
        },
    )

    result_dict = await get_call.ainvoke(_args(sid="CAfake"))

    assert isinstance(result_dict, dict)
    result = GetCallOutput.model_validate(result_dict)
    assert result.success is True
    assert result.call is not None


@pytest.mark.asyncio
async def test_delete_call(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/Accounts/{_ACCT}/Calls/CAfake.json",
        status_code=204,
    )

    result_dict = await delete_call.ainvoke(_args(sid="CAfake"))

    assert isinstance(result_dict, dict)
    result = DeleteCallOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_calls(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/Accounts/{_ACCT}/Calls.json?PageSize=50",
        json={
            # TODO: fill in a representative response
            "calls": [
                {"sid": "CA1", "status": "completed"},
            ],
        },
    )

    result_dict = await list_calls.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListCallsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.calls) == 1


@pytest.mark.asyncio
async def test_download_recording_media() -> None:
    result_dict = await download_recording_media.ainvoke(
        _args(recording_id="REfake", format=".mp3")
    )

    assert isinstance(result_dict, dict)
    result = DownloadRecordingMediaOutput.model_validate(result_dict)
    assert result.success is True
    assert result.download_url is not None
    assert "REfake" in result.download_url
    assert ".mp3" in result.download_url


@pytest.mark.asyncio
async def test_phone_number_lookup(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{LOOKUP_API}/v2/PhoneNumbers/+15551234567?Fields=line_type_intelligence",
        json={
            # TODO: fill in a representative response
            "phone_number": "+15551234567",
            "country_code": "US",
            "calling_country_code": "1",
            "national_format": "(555) 123-4567",
            "valid": True,
            "line_type_intelligence": {"type": "mobile", "carrier_name": "T-Mobile"},
        },
    )

    result_dict = await phone_number_lookup.ainvoke(_args(phone_number="+15551234567"))

    assert isinstance(result_dict, dict)
    result = PhoneNumberLookupOutput.model_validate(result_dict)
    assert result.success is True
    assert result.lookup is not None
    assert result.lookup.valid is True


@pytest.mark.asyncio
async def test_send_sms_verification(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{VERIFY_API}/v2/Services/VAfake/Verifications",
        json={
            # TODO: fill in a representative response
            "sid": "VEfake",
            "service_sid": "VAfake",
            "to": "+16175551212",
            "channel": "sms",
            "status": "pending",
            "valid": False,
        },
    )

    result_dict = await send_sms_verification.ainvoke(
        _args(service_sid="VAfake", to="+16175551212")
    )

    assert isinstance(result_dict, dict)
    result = SendSmsVerificationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.verification is not None


@pytest.mark.asyncio
async def test_check_verification_token(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{VERIFY_API}/v2/Services/VAfake/VerificationCheck",
        json={
            # TODO: fill in a representative response
            "sid": "VEfake",
            "service_sid": "VAfake",
            "to": "+16175551212",
            "channel": "sms",
            "status": "approved",
            "valid": True,
        },
    )

    result_dict = await check_verification_token.ainvoke(
        _args(service_sid="VAfake", to="+16175551212", code="123456")
    )

    assert isinstance(result_dict, dict)
    result = CheckVerificationTokenOutput.model_validate(result_dict)
    assert result.success is True
    assert result.verification is not None
    assert result.verification.valid is True


@pytest.mark.asyncio
async def test_create_verification_service(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{VERIFY_API}/v2/Services",
        json={
            # TODO: fill in a representative response
            "sid": "VAfake",
            "friendly_name": "My Service",
            "code_length": 6,
        },
    )

    result_dict = await create_verification_service.ainvoke(
        _args(friendly_name="My Service")
    )

    assert isinstance(result_dict, dict)
    result = CreateVerificationServiceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.service is not None


@pytest.mark.asyncio
async def test_list_transcripts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{INTELLIGENCE_API}/v2/Transcripts?PageSize=50",
        json={
            # TODO: fill in a representative response
            "transcripts": [
                {"sid": "GTfake", "status": "completed", "duration": 120},
            ],
        },
    )

    result_dict = await list_transcripts.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListTranscriptsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.transcripts) == 1


@pytest.mark.asyncio
async def test_get_transcripts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{INTELLIGENCE_API}/v2/Transcripts/GTfake",
        json={
            # TODO: fill in a representative response
            "sid": "GTfake",
            "status": "completed",
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{INTELLIGENCE_API}/v2/Transcripts/GTfake/Sentences?PageSize=1000",
        json={
            "sentences": [
                {"transcript": "Hello", "sentence_index": 0, "confidence": 0.95},
            ],
        },
    )

    result_dict = await get_transcripts.ainvoke(_args(transcript_sids=["GTfake"]))

    assert isinstance(result_dict, dict)
    result = GetTranscriptsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.transcripts) == 1
    assert len(result.transcripts[0].sentences) == 1


@pytest.mark.asyncio
async def test_list_phone_numbers(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/Accounts/{_ACCT}/IncomingPhoneNumbers.json",
        json={
            # TODO: fill in a representative response
            "incoming_phone_numbers": [
                {"sid": "PNfake", "phone_number": "+15551234567", "friendly_name": "My Number"},
            ],
        },
    )

    result_dict = await list_phone_numbers.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListPhoneNumbersOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.phone_numbers) == 1


# --- Failure-path tests -----------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_missing_credentials() -> None:
    """Empty credentials should return success=False without hitting the wire."""
    result_dict = await send_message.ainvoke(
        {"auth_type": "custom", "auth_data": {}, "from_number": "+15551234567", "to": "+16175551212", "body": "Hello"}
    )

    assert isinstance(result_dict, dict)
    result = SendMessageOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
