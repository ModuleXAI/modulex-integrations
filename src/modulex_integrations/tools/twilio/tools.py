"""Twilio LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.twilio.outputs import (
    CallResource,
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
    LookupResult,
    MakePhoneCallOutput,
    MediaResource,
    MessageResource,
    PhoneNumberInfo,
    PhoneNumberLookupOutput,
    SendMessageOutput,
    SendSmsVerificationOutput,
    TranscriptResource,
    TranscriptSentence,
    VerificationResource,
    VerificationServiceResource,
)

__all__ = [
    "check_verification_token",
    "create_verification_service",
    "delete_call",
    "delete_message",
    "download_recording_media",
    "get_call",
    "get_message",
    "get_transcripts",
    "list_calls",
    "list_message_media",
    "list_messages",
    "list_phone_numbers",
    "list_transcripts",
    "make_phone_call",
    "phone_number_lookup",
    "send_message",
    "send_sms_verification",
]

_BASE_URL = "https://api.twilio.com/2010-04-01"
_LOOKUP_URL = "https://lookups.twilio.com"
_VERIFY_URL = "https://verify.twilio.com"
_INTELLIGENCE_URL = "https://intelligence.twilio.com"
_TIMEOUT = 30.0


def _basic_auth(auth_data: dict[str, Any]) -> httpx.BasicAuth:
    account_sid = auth_data.get("account_sid", "")
    auth_token = auth_data.get("auth_token", "")
    return httpx.BasicAuth(username=account_sid, password=auth_token)


def _account_sid(auth_data: dict[str, Any]) -> str:
    val: str = auth_data.get("account_sid", "")
    return val


def _parse_message(m: dict[str, Any]) -> MessageResource:
    return MessageResource(
        sid=m.get("sid"),
        date_created=m.get("date_created"),
        date_updated=m.get("date_updated"),
        date_sent=m.get("date_sent"),
        account_sid=m.get("account_sid"),
        to=m.get("to"),
        from_number=m.get("from"),
        body=m.get("body"),
        status=m.get("status"),
        num_segments=m.get("num_segments"),
        num_media=m.get("num_media"),
        direction=m.get("direction"),
        price=m.get("price"),
        price_unit=m.get("price_unit"),
        error_code=m.get("error_code"),
        error_message=m.get("error_message"),
        uri=m.get("uri"),
    )


def _parse_call(c: dict[str, Any]) -> CallResource:
    return CallResource(
        sid=c.get("sid"),
        date_created=c.get("date_created"),
        date_updated=c.get("date_updated"),
        account_sid=c.get("account_sid"),
        to=c.get("to"),
        to_formatted=c.get("to_formatted"),
        from_number=c.get("from"),
        from_formatted=c.get("from_formatted"),
        status=c.get("status"),
        start_time=c.get("start_time"),
        end_time=c.get("end_time"),
        duration=c.get("duration"),
        price=c.get("price"),
        price_unit=c.get("price_unit"),
        direction=c.get("direction"),
        uri=c.get("uri"),
    )


# --- Input schemas --------------------------------------------------------


class SendMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    from_number: str = Field(description="The sender's Twilio phone number in E.164 format")
    to: str = Field(description="The destination phone number in E.164 format")
    body: str = Field(description="The text of the message, limited to 1600 characters")
    media_url: list[str] | None = Field(default=None, description="Array of media URLs to include")


class MakePhoneCallInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    from_number: str = Field(description="The caller's Twilio phone number in E.164 format")
    to: str = Field(description="The destination phone number in E.164 format")
    call_type: str = Field(description="How to handle the call: text, url, or application")
    text: str | None = Field(default=None, description="Text for Twilio to speak. Required when call_type is 'text'")
    url: str | None = Field(default=None, description="URL returning TwiML. Required when call_type is 'url'")
    application_sid: str | None = Field(default=None, description="Application SID. Required when call_type is 'application'")
    timeout: int | None = Field(default=None, description="Seconds to ring before no-answer (default 60, max 600)")
    record: bool | None = Field(default=None, description="Whether to record the call")


class GetMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="The SID of the message to retrieve")


class DeleteMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="The SID of the message to delete")


class ListMessagesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    from_number: str | None = Field(default=None, description="Filter by sender phone number in E.164 format")
    to: str | None = Field(default=None, description="Filter by recipient phone number in E.164 format")
    limit: int = Field(default=50, description="Maximum number of messages to return")


class ListMessageMediaInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="The SID of the message")
    limit: int = Field(default=50, description="Maximum number of media items to return")


class GetCallInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    sid: str = Field(description="The SID of the call to retrieve")


class DeleteCallInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    sid: str = Field(description="The SID of the call to delete")


class ListCallsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    from_number: str | None = Field(default=None, description="Filter by caller phone number in E.164 format")
    to: str | None = Field(default=None, description="Filter by recipient phone number in E.164 format")
    parent_call_sid: str | None = Field(default=None, description="Only include calls spawned by this parent call SID")
    status: str | None = Field(default=None, description="Filter by status: queued, ringing, in-progress, canceled, completed, failed, busy, no-answer")
    limit: int = Field(default=50, description="Maximum number of calls to return")


class DownloadRecordingMediaInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    recording_id: str = Field(description="The SID of the recording")
    format: str = Field(default=".wav", description="Audio format: .mp3 or .wav")


class PhoneNumberLookupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    phone_number: str = Field(description="The phone number to look up")


class SendSmsVerificationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    service_sid: str = Field(description="The SID of the Verify service")
    to: str = Field(description="The destination phone number in E.164 format")


class CheckVerificationTokenInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    service_sid: str = Field(description="The SID of the Verify service")
    to: str = Field(description="The phone number that received the verification code in E.164 format")
    code: str = Field(description="The verification code to check")


class CreateVerificationServiceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    friendly_name: str = Field(description="A human-readable name for the new verification service")


class ListTranscriptsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    include_transcript_text: bool | None = Field(default=None, description="Set to true to include transcript sentences")
    limit: int = Field(default=50, description="Maximum number of transcripts to return")


class GetTranscriptsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    transcript_sids: list[str] = Field(description="Array of transcript SID strings to retrieve")


class ListPhoneNumbersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=SendMessageInput)
@serialize_pydantic_return
async def send_message(
    auth_type: str,
    auth_data: dict[str, Any],
    from_number: str,
    to: str,
    body: str,
    media_url: list[str] | None = None,
) -> SendMessageOutput:
    """Send an SMS or MMS message with optional media files."""
    acct = _account_sid(auth_data)
    if not acct or not auth_data.get("auth_token"):
        return SendMessageOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    data: dict[str, Any] = {"From": from_number, "To": to, "Body": body}
    if media_url:
        for i, u in enumerate(media_url):
            data[f"MediaUrl{i}"] = u
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/Accounts/{acct}/Messages.json",
                auth=_basic_auth(auth_data),
                data=data,
            )
        if response.status_code not in (200, 201):
            return SendMessageOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        m = response.json()
    except httpx.TimeoutException:
        return SendMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendMessageOutput(success=False, error=f"Call failed: {exc}")
    return SendMessageOutput(success=True, message=_parse_message(m))


@tool(args_schema=MakePhoneCallInput)
@serialize_pydantic_return
async def make_phone_call(
    auth_type: str,
    auth_data: dict[str, Any],
    from_number: str,
    to: str,
    call_type: str,
    text: str | None = None,
    url: str | None = None,
    application_sid: str | None = None,
    timeout: int | None = None,
    record: bool | None = None,
) -> MakePhoneCallOutput:
    """Initiate a phone call using text-to-speech, a TwiML URL, or an application SID."""
    acct = _account_sid(auth_data)
    if not acct or not auth_data.get("auth_token"):
        return MakePhoneCallOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    data: dict[str, Any] = {"From": from_number, "To": to}
    if call_type == "text":
        twiml = f"<Response><Say>{text or ''}</Say></Response>"
        data["Twiml"] = twiml
    elif call_type == "url":
        if url:
            data["Url"] = url
    elif call_type == "application":
        if application_sid:
            data["ApplicationSid"] = application_sid
    if timeout is not None:
        data["Timeout"] = timeout
    if record is not None:
        data["Record"] = str(record).lower()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/Accounts/{acct}/Calls.json",
                auth=_basic_auth(auth_data),
                data=data,
            )
        if response.status_code not in (200, 201):
            return MakePhoneCallOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        c = response.json()
    except httpx.TimeoutException:
        return MakePhoneCallOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return MakePhoneCallOutput(success=False, error=f"Call failed: {exc}")
    return MakePhoneCallOutput(success=True, call=_parse_call(c))


@tool(args_schema=GetMessageInput)
@serialize_pydantic_return
async def get_message(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
) -> GetMessageOutput:
    """Retrieve details of a specific message by SID."""
    acct = _account_sid(auth_data)
    if not acct or not auth_data.get("auth_token"):
        return GetMessageOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/Accounts/{acct}/Messages/{message_id}.json",
                auth=_basic_auth(auth_data),
            )
        if response.status_code != 200:
            return GetMessageOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        m = response.json()
    except httpx.TimeoutException:
        return GetMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMessageOutput(success=False, error=f"Call failed: {exc}")
    return GetMessageOutput(success=True, message=_parse_message(m))


@tool(args_schema=DeleteMessageInput)
@serialize_pydantic_return
async def delete_message(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
) -> DeleteMessageOutput:
    """Delete a message record from your account."""
    acct = _account_sid(auth_data)
    if not acct or not auth_data.get("auth_token"):
        return DeleteMessageOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/Accounts/{acct}/Messages/{message_id}.json",
                auth=_basic_auth(auth_data),
            )
        if response.status_code != 204:
            return DeleteMessageOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return DeleteMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteMessageOutput(success=False, error=f"Call failed: {exc}")
    return DeleteMessageOutput(success=True)


@tool(args_schema=ListMessagesInput)
@serialize_pydantic_return
async def list_messages(
    auth_type: str,
    auth_data: dict[str, Any],
    from_number: str | None = None,
    to: str | None = None,
    limit: int = 50,
) -> ListMessagesOutput:
    """List messages associated with your account, optionally filtered by sender or recipient."""
    acct = _account_sid(auth_data)
    if not acct or not auth_data.get("auth_token"):
        return ListMessagesOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    params: dict[str, Any] = {"PageSize": limit}
    if from_number:
        params["From"] = from_number
    if to:
        params["To"] = to
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/Accounts/{acct}/Messages.json",
                auth=_basic_auth(auth_data),
                params=params,
            )
        if response.status_code != 200:
            return ListMessagesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListMessagesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListMessagesOutput(success=False, error=f"Call failed: {exc}")
    messages = [_parse_message(m) for m in data.get("messages", [])]
    return ListMessagesOutput(success=True, messages=messages)


@tool(args_schema=ListMessageMediaInput)
@serialize_pydantic_return
async def list_message_media(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    limit: int = 50,
) -> ListMessageMediaOutput:
    """List media resources associated with a message."""
    acct = _account_sid(auth_data)
    if not acct or not auth_data.get("auth_token"):
        return ListMessageMediaOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/Accounts/{acct}/Messages/{message_id}/Media.json",
                auth=_basic_auth(auth_data),
                params={"PageSize": limit},
            )
        if response.status_code != 200:
            return ListMessageMediaOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListMessageMediaOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListMessageMediaOutput(success=False, error=f"Call failed: {exc}")
    media = [
        MediaResource(
            sid=item.get("sid"),
            content_type=item.get("content_type"),
            date_created=item.get("date_created"),
            date_updated=item.get("date_updated"),
            uri=item.get("uri"),
        )
        for item in data.get("media_list", [])
    ]
    return ListMessageMediaOutput(success=True, media=media)


@tool(args_schema=GetCallInput)
@serialize_pydantic_return
async def get_call(
    auth_type: str,
    auth_data: dict[str, Any],
    sid: str,
) -> GetCallOutput:
    """Retrieve details of a specific call by SID."""
    acct = _account_sid(auth_data)
    if not acct or not auth_data.get("auth_token"):
        return GetCallOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/Accounts/{acct}/Calls/{sid}.json",
                auth=_basic_auth(auth_data),
            )
        if response.status_code != 200:
            return GetCallOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        c = response.json()
    except httpx.TimeoutException:
        return GetCallOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCallOutput(success=False, error=f"Call failed: {exc}")
    return GetCallOutput(success=True, call=_parse_call(c))


@tool(args_schema=DeleteCallInput)
@serialize_pydantic_return
async def delete_call(
    auth_type: str,
    auth_data: dict[str, Any],
    sid: str,
) -> DeleteCallOutput:
    """Delete a call record from your account."""
    acct = _account_sid(auth_data)
    if not acct or not auth_data.get("auth_token"):
        return DeleteCallOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/Accounts/{acct}/Calls/{sid}.json",
                auth=_basic_auth(auth_data),
            )
        if response.status_code != 204:
            return DeleteCallOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return DeleteCallOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteCallOutput(success=False, error=f"Call failed: {exc}")
    return DeleteCallOutput(success=True)


@tool(args_schema=ListCallsInput)
@serialize_pydantic_return
async def list_calls(
    auth_type: str,
    auth_data: dict[str, Any],
    from_number: str | None = None,
    to: str | None = None,
    parent_call_sid: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> ListCallsOutput:
    """List calls associated with your account, optionally filtered by number, status, or parent call."""
    acct = _account_sid(auth_data)
    if not acct or not auth_data.get("auth_token"):
        return ListCallsOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    params: dict[str, Any] = {"PageSize": limit}
    if from_number:
        params["From"] = from_number
    if to:
        params["To"] = to
    if parent_call_sid:
        params["ParentCallSid"] = parent_call_sid
    if status:
        params["Status"] = status
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/Accounts/{acct}/Calls.json",
                auth=_basic_auth(auth_data),
                params=params,
            )
        if response.status_code != 200:
            return ListCallsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListCallsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCallsOutput(success=False, error=f"Call failed: {exc}")
    calls = [_parse_call(c) for c in data.get("calls", [])]
    return ListCallsOutput(success=True, calls=calls)


@tool(args_schema=DownloadRecordingMediaInput)
@serialize_pydantic_return
async def download_recording_media(
    auth_type: str,
    auth_data: dict[str, Any],
    recording_id: str,
    format: str = ".wav",
) -> DownloadRecordingMediaOutput:
    """Get the download URL for a call recording in the specified format."""
    acct = _account_sid(auth_data)
    if not acct or not auth_data.get("auth_token"):
        return DownloadRecordingMediaOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    download_url = f"{_BASE_URL}/Accounts/{acct}/Recordings/{recording_id}{format}"
    return DownloadRecordingMediaOutput(
        success=True,
        download_url=download_url,
        recording_sid=recording_id,
        format=format,
    )


@tool(args_schema=PhoneNumberLookupInput)
@serialize_pydantic_return
async def phone_number_lookup(
    auth_type: str,
    auth_data: dict[str, Any],
    phone_number: str,
) -> PhoneNumberLookupOutput:
    """Look up information about a phone number including line type intelligence."""
    if not _account_sid(auth_data) or not auth_data.get("auth_token"):
        return PhoneNumberLookupOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_LOOKUP_URL}/v2/PhoneNumbers/{phone_number}",
                auth=_basic_auth(auth_data),
                params={"Fields": "line_type_intelligence"},
            )
        if response.status_code != 200:
            return PhoneNumberLookupOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return PhoneNumberLookupOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PhoneNumberLookupOutput(success=False, error=f"Call failed: {exc}")
    lti = data.get("line_type_intelligence") or {}
    lookup = LookupResult(
        phone_number=data.get("phone_number"),
        country_code=data.get("country_code"),
        calling_country_code=data.get("calling_country_code"),
        national_format=data.get("national_format"),
        valid=data.get("valid"),
        validation_errors=data.get("validation_errors") or [],
        line_type=lti.get("type"),
        carrier_name=lti.get("carrier_name"),
    )
    return PhoneNumberLookupOutput(success=True, lookup=lookup)


@tool(args_schema=SendSmsVerificationInput)
@serialize_pydantic_return
async def send_sms_verification(
    auth_type: str,
    auth_data: dict[str, Any],
    service_sid: str,
    to: str,
) -> SendSmsVerificationOutput:
    """Send an SMS verification code to a phone number via Twilio Verify."""
    if not _account_sid(auth_data) or not auth_data.get("auth_token"):
        return SendSmsVerificationOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_VERIFY_URL}/v2/Services/{service_sid}/Verifications",
                auth=_basic_auth(auth_data),
                data={"To": to, "Channel": "sms"},
            )
        if response.status_code not in (200, 201):
            return SendSmsVerificationOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        v = response.json()
    except httpx.TimeoutException:
        return SendSmsVerificationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendSmsVerificationOutput(success=False, error=f"Call failed: {exc}")
    return SendSmsVerificationOutput(
        success=True,
        verification=VerificationResource(
            sid=v.get("sid"),
            service_sid=v.get("service_sid"),
            account_sid=v.get("account_sid"),
            to=v.get("to"),
            channel=v.get("channel"),
            status=v.get("status"),
            valid=v.get("valid"),
            date_created=v.get("date_created"),
            date_updated=v.get("date_updated"),
        ),
    )


@tool(args_schema=CheckVerificationTokenInput)
@serialize_pydantic_return
async def check_verification_token(
    auth_type: str,
    auth_data: dict[str, Any],
    service_sid: str,
    to: str,
    code: str,
) -> CheckVerificationTokenOutput:
    """Check if a user-provided verification code is correct."""
    if not _account_sid(auth_data) or not auth_data.get("auth_token"):
        return CheckVerificationTokenOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_VERIFY_URL}/v2/Services/{service_sid}/VerificationCheck",
                auth=_basic_auth(auth_data),
                data={"To": to, "Code": code},
            )
        if response.status_code == 404:
            return CheckVerificationTokenOutput(success=False, error="Verification not found — it may have expired or already been consumed.")
        if response.status_code not in (200, 201):
            return CheckVerificationTokenOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        v = response.json()
    except httpx.TimeoutException:
        return CheckVerificationTokenOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CheckVerificationTokenOutput(success=False, error=f"Call failed: {exc}")
    return CheckVerificationTokenOutput(
        success=True,
        verification=VerificationResource(
            sid=v.get("sid"),
            service_sid=v.get("service_sid"),
            account_sid=v.get("account_sid"),
            to=v.get("to"),
            channel=v.get("channel"),
            status=v.get("status"),
            valid=v.get("valid"),
            date_created=v.get("date_created"),
            date_updated=v.get("date_updated"),
        ),
    )


@tool(args_schema=CreateVerificationServiceInput)
@serialize_pydantic_return
async def create_verification_service(
    auth_type: str,
    auth_data: dict[str, Any],
    friendly_name: str,
) -> CreateVerificationServiceOutput:
    """Create a new Twilio Verify service for sending SMS verifications."""
    if not _account_sid(auth_data) or not auth_data.get("auth_token"):
        return CreateVerificationServiceOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_VERIFY_URL}/v2/Services",
                auth=_basic_auth(auth_data),
                data={"FriendlyName": friendly_name},
            )
        if response.status_code not in (200, 201):
            return CreateVerificationServiceOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        s = response.json()
    except httpx.TimeoutException:
        return CreateVerificationServiceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateVerificationServiceOutput(success=False, error=f"Call failed: {exc}")
    return CreateVerificationServiceOutput(
        success=True,
        service=VerificationServiceResource(
            sid=s.get("sid"),
            account_sid=s.get("account_sid"),
            friendly_name=s.get("friendly_name"),
            code_length=s.get("code_length"),
            lookup_enabled=s.get("lookup_enabled"),
            date_created=s.get("date_created"),
            date_updated=s.get("date_updated"),
        ),
    )


@tool(args_schema=ListTranscriptsInput)
@serialize_pydantic_return
async def list_transcripts(
    auth_type: str,
    auth_data: dict[str, Any],
    include_transcript_text: bool | None = None,
    limit: int = 50,
) -> ListTranscriptsOutput:
    """List voice intelligence transcripts, optionally including transcript text."""
    if not _account_sid(auth_data) or not auth_data.get("auth_token"):
        return ListTranscriptsOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_INTELLIGENCE_URL}/v2/Transcripts",
                auth=_basic_auth(auth_data),
                params={"PageSize": limit},
            )
        if response.status_code != 200:
            return ListTranscriptsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListTranscriptsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTranscriptsOutput(success=False, error=f"Call failed: {exc}")
    transcripts: list[TranscriptResource] = []
    for t in data.get("transcripts", []):
        tr = TranscriptResource(
            sid=t.get("sid"),
            account_sid=t.get("account_sid"),
            service_sid=t.get("service_sid"),
            status=t.get("status"),
            date_created=t.get("date_created"),
            date_updated=t.get("date_updated"),
            duration=t.get("duration"),
            channel=t.get("channel"),
        )
        if include_transcript_text:
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    sent_resp = await client.get(
                        f"{_INTELLIGENCE_URL}/v2/Transcripts/{t['sid']}/Sentences",
                        auth=_basic_auth(auth_data),
                        params={"PageSize": 1000},
                    )
                if sent_resp.status_code == 200:
                    sent_data = sent_resp.json()
                    sentences = [
                        TranscriptSentence(
                            media_channel=s.get("media_channel"),
                            sentence_index=s.get("sentence_index"),
                            start_time=s.get("start_time"),
                            end_time=s.get("end_time"),
                            transcript=s.get("transcript"),
                            confidence=s.get("confidence"),
                        )
                        for s in sent_data.get("sentences", [])
                    ]
                    tr.sentences = sentences
                    tr.transcript_text = " ".join(
                        s.get("transcript", "") for s in sent_data.get("sentences", [])
                    )
            except Exception:
                pass
        transcripts.append(tr)
    return ListTranscriptsOutput(success=True, transcripts=transcripts)


@tool(args_schema=GetTranscriptsInput)
@serialize_pydantic_return
async def get_transcripts(
    auth_type: str,
    auth_data: dict[str, Any],
    transcript_sids: list[str],
) -> GetTranscriptsOutput:
    """Retrieve full transcripts with sentences for the specified transcript SIDs."""
    if not _account_sid(auth_data) or not auth_data.get("auth_token"):
        return GetTranscriptsOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    transcripts: list[TranscriptResource] = []
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            for tsid in transcript_sids:
                t_resp = await client.get(
                    f"{_INTELLIGENCE_URL}/v2/Transcripts/{tsid}",
                    auth=_basic_auth(auth_data),
                )
                if t_resp.status_code != 200:
                    continue
                t = t_resp.json()
                s_resp = await client.get(
                    f"{_INTELLIGENCE_URL}/v2/Transcripts/{tsid}/Sentences",
                    auth=_basic_auth(auth_data),
                    params={"PageSize": 1000},
                )
                sentences: list[TranscriptSentence] = []
                transcript_text = ""
                if s_resp.status_code == 200:
                    s_data = s_resp.json()
                    sentences = [
                        TranscriptSentence(
                            media_channel=s.get("media_channel"),
                            sentence_index=s.get("sentence_index"),
                            start_time=s.get("start_time"),
                            end_time=s.get("end_time"),
                            transcript=s.get("transcript"),
                            confidence=s.get("confidence"),
                        )
                        for s in s_data.get("sentences", [])
                    ]
                    transcript_text = " ".join(
                        s.get("transcript", "") for s in s_data.get("sentences", [])
                    )
                transcripts.append(
                    TranscriptResource(
                        sid=t.get("sid"),
                        account_sid=t.get("account_sid"),
                        service_sid=t.get("service_sid"),
                        status=t.get("status"),
                        date_created=t.get("date_created"),
                        date_updated=t.get("date_updated"),
                        duration=t.get("duration"),
                        channel=t.get("channel"),
                        sentences=sentences,
                        transcript_text=transcript_text,
                    )
                )
    except httpx.TimeoutException:
        return GetTranscriptsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetTranscriptsOutput(success=False, error=f"Call failed: {exc}")
    return GetTranscriptsOutput(success=True, transcripts=transcripts)


@tool(args_schema=ListPhoneNumbersInput)
@serialize_pydantic_return
async def list_phone_numbers(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListPhoneNumbersOutput:
    """List incoming phone numbers on your Twilio account."""
    acct = _account_sid(auth_data)
    if not acct or not auth_data.get("auth_token"):
        return ListPhoneNumbersOutput(success=False, error="Missing Twilio credentials. Configure Account SID and Auth Token.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/Accounts/{acct}/IncomingPhoneNumbers.json",
                auth=_basic_auth(auth_data),
            )
        if response.status_code != 200:
            return ListPhoneNumbersOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListPhoneNumbersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListPhoneNumbersOutput(success=False, error=f"Call failed: {exc}")
    numbers = [
        PhoneNumberInfo(
            sid=n.get("sid"),
            phone_number=n.get("phone_number"),
            friendly_name=n.get("friendly_name"),
        )
        for n in data.get("incoming_phone_numbers", [])
    ]
    return ListPhoneNumbersOutput(success=True, phone_numbers=numbers)
