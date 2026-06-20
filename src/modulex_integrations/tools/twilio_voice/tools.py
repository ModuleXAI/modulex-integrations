"""Twilio Voice LangChain ``@tool`` functions.

Three async tools wrapping the Twilio Programmable Voice REST API
(``api.twilio.com/2010-04-01``). The calling convention is the modulex
*api_key* convention: the runtime injects ``api_key: str`` (the Twilio
Auth Token) directly, while ``account_sid`` is a normal parameter the
runtime fills from the resolved credential's data by exact name.

Twilio uses HTTP Basic authentication — ``account_sid`` as the username
and the Auth Token as the password — so each request goes out with
``httpx.AsyncClient(auth=(account_sid, api_key))``.

Error model: every call is wrapped in try/except. Non-2xx responses,
timeouts, and unexpected exceptions surface as ``success=False`` +
``error`` rather than raising. Twilio also returns ``error_code`` /
``message`` on logical failures, surfaced the same way.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.twilio_voice.outputs import (
    CallListItem,
    GetRecordingOutput,
    ListCallsOutput,
    MakeCallOutput,
)

__all__ = ["get_recording", "list_calls", "make_call"]

_API_BASE = "https://api.twilio.com/2010-04-01"
_DEFAULT_TIMEOUT = 30.0


# --- Input schemas (args_schema for each @tool) ----------------------------


class MakeCallInput(BaseModel):
    to: str = Field(description="Phone number to call in E.164 format (e.g., +14155551234)")
    from_: str = Field(
        description=(
            "Your Twilio phone number to call from in E.164 format "
            "(e.g., +14155559876)"
        ),
    )
    account_sid: str = Field(description="Twilio Account SID (starts with 'AC')")
    api_key: str = Field(
        description="Twilio Auth Token (provided by credential system)"
    )
    url: str | None = Field(
        default=None,
        description="Webhook URL that returns TwiML instructions for the call",
    )
    twiml: str | None = Field(
        default=None,
        description=(
            "TwiML instructions to execute (raw XML, e.g. "
            "'<Response><Say>Hello</Say></Response>'). Provide this or 'url'."
        ),
    )
    status_callback: str | None = Field(
        default=None, description="Webhook URL for call status updates"
    )
    status_callback_method: str | None = Field(
        default=None, description="HTTP method for the status callback (GET or POST)"
    )
    record: bool = Field(default=False, description="Whether to record the call")
    recording_status_callback: str | None = Field(
        default=None, description="Webhook URL for recording status updates"
    )
    timeout: int | None = Field(
        default=None,
        description="Seconds to wait for an answer before giving up (default: 60)",
    )
    machine_detection: str | None = Field(
        default=None,
        description="Answering machine detection: 'Enable' or 'DetectMessageEnd'",
    )


class ListCallsInput(BaseModel):
    account_sid: str = Field(description="Twilio Account SID (starts with 'AC')")
    api_key: str = Field(
        description="Twilio Auth Token (provided by credential system)"
    )
    to: str | None = Field(
        default=None, description="Filter by calls to this phone number (E.164 format)"
    )
    from_: str | None = Field(
        default=None,
        description="Filter by calls from this phone number (E.164 format)",
    )
    status: str | None = Field(
        default=None,
        description=(
            "Filter by call status (queued, ringing, in-progress, completed, "
            "busy, failed, no-answer, canceled)"
        ),
    )
    start_time_after: str | None = Field(
        default=None,
        description="Filter calls that started on or after this date (YYYY-MM-DD)",
    )
    start_time_before: str | None = Field(
        default=None,
        description="Filter calls that started on or before this date (YYYY-MM-DD)",
    )
    page_size: int | None = Field(
        default=None,
        description="Number of records to return (max 1000, default 50)",
    )
    include_recordings: bool = Field(
        default=True,
        description=(
            "Whether to fetch recording SIDs for each returned call "
            "(adds one extra request per call that has recordings)"
        ),
    )


class GetRecordingInput(BaseModel):
    recording_sid: str = Field(
        description="Recording SID to retrieve (e.g., RExxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx)"
    )
    account_sid: str = Field(description="Twilio Account SID (starts with 'AC')")
    api_key: str = Field(
        description="Twilio Auth Token (provided by credential system)"
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=MakeCallInput)
@serialize_pydantic_return
async def make_call(
    to: str,
    from_: str,
    account_sid: str,
    api_key: str,
    url: str | None = None,
    twiml: str | None = None,
    status_callback: str | None = None,
    status_callback_method: str | None = None,
    record: bool = False,
    recording_status_callback: str | None = None,
    timeout: int | None = None,
    machine_detection: str | None = None,
) -> MakeCallOutput:
    """Make an outbound phone call using the Twilio Voice API."""
    if not api_key or not api_key.strip():
        return MakeCallOutput(
            success=False,
            error="Twilio Auth Token is empty. Please configure a valid Twilio credential.",
        )
    if not account_sid or not account_sid.strip():
        return MakeCallOutput(success=False, error="Twilio Account SID is required.")
    if not url and not twiml:
        return MakeCallOutput(
            success=False, error="Either 'url' or 'twiml' is required to execute the call."
        )

    # Twilio expects application/x-www-form-urlencoded bodies with
    # PascalCase parameter names.
    form: dict[str, Any] = {"To": to, "From": from_}
    if url:
        form["Url"] = url
    elif twiml:
        form["Twiml"] = twiml
    if status_callback:
        form["StatusCallback"] = status_callback
    if status_callback_method:
        form["StatusCallbackMethod"] = status_callback_method
    if record:
        form["Record"] = "true"
    if recording_status_callback:
        form["RecordingStatusCallback"] = recording_status_callback
    if timeout is not None:
        form["Timeout"] = str(timeout)
    if machine_detection:
        form["MachineDetection"] = machine_detection

    endpoint = f"{_API_BASE}/Accounts/{account_sid}/Calls.json"
    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.post(
                endpoint, auth=(account_sid, api_key), data=form
            )
        data = response.json()
        if response.status_code not in (200, 201):
            return MakeCallOutput(
                success=False,
                error=(
                    data.get("message")
                    or data.get("error_message")
                    or f"Twilio API error ({response.status_code}): {response.text}"
                ),
            )
    except httpx.TimeoutException:
        return MakeCallOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return MakeCallOutput(success=False, error=f"make_call failed: {exc}")

    if data.get("error_code") or data.get("status") == "failed":
        return MakeCallOutput(
            success=False,
            error=data.get("message") or data.get("error_message") or "Call failed",
        )

    return MakeCallOutput(
        success=True,
        call_sid=data.get("sid"),
        status=data.get("status"),
        direction=data.get("direction"),
        from_=data.get("from"),
        to=data.get("to"),
        duration=_to_int(data.get("duration")),
        price=data.get("price"),
        price_unit=data.get("price_unit"),
    )


@tool(args_schema=ListCallsInput)
@serialize_pydantic_return
async def list_calls(
    account_sid: str,
    api_key: str,
    to: str | None = None,
    from_: str | None = None,
    status: str | None = None,
    start_time_after: str | None = None,
    start_time_before: str | None = None,
    page_size: int | None = None,
    include_recordings: bool = True,
) -> ListCallsOutput:
    """Retrieve a list of calls made to and from a Twilio account."""
    if not api_key or not api_key.strip():
        return ListCallsOutput(
            success=False,
            error="Twilio Auth Token is empty. Please configure a valid Twilio credential.",
        )
    if not account_sid or not account_sid.strip():
        return ListCallsOutput(success=False, error="Twilio Account SID is required.")

    params: dict[str, Any] = {}
    if to:
        params["To"] = to
    if from_:
        params["From"] = from_
    if status:
        params["Status"] = status
    # Twilio uses inequality-suffixed keys for date-range filtering.
    if start_time_after:
        params["StartTime>"] = start_time_after
    if start_time_before:
        params["StartTime<"] = start_time_before
    if page_size is not None:
        params["PageSize"] = str(page_size)

    endpoint = f"{_API_BASE}/Accounts/{account_sid}/Calls.json"
    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.get(
                endpoint, auth=(account_sid, api_key), params=params
            )
            data = response.json()
            if response.status_code != 200 or data.get("error_code"):
                return ListCallsOutput(
                    success=False,
                    error=(
                        data.get("message")
                        or data.get("error_message")
                        or f"Twilio API error ({response.status_code}): {response.text}"
                    ),
                )

            calls: list[CallListItem] = []
            for call in data.get("calls") or []:
                recording_sids: list[str] = []
                recordings_uri = (call.get("subresource_uris") or {}).get("recordings")
                if include_recordings and recordings_uri:
                    try:
                        rec_response = await client.get(
                            f"https://api.twilio.com{recordings_uri}",
                            auth=(account_sid, api_key),
                        )
                        if rec_response.status_code == 200:
                            rec_data = rec_response.json()
                            recording_sids = [
                                rec.get("sid")
                                for rec in (rec_data.get("recordings") or [])
                                if rec.get("sid")
                            ]
                    except Exception:
                        recording_sids = []

                calls.append(
                    CallListItem(
                        call_sid=call.get("sid"),
                        from_=call.get("from"),
                        to=call.get("to"),
                        status=call.get("status"),
                        direction=call.get("direction"),
                        duration=_to_int(call.get("duration")),
                        price=call.get("price"),
                        price_unit=call.get("price_unit"),
                        start_time=call.get("start_time"),
                        end_time=call.get("end_time"),
                        date_created=call.get("date_created"),
                        recording_sids=recording_sids,
                    )
                )
    except httpx.TimeoutException:
        return ListCallsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCallsOutput(success=False, error=f"list_calls failed: {exc}")

    return ListCallsOutput(
        success=True,
        calls=calls,
        total=len(calls),
        page=_to_int(data.get("page")),
        page_size=_to_int(data.get("page_size")),
    )


@tool(args_schema=GetRecordingInput)
@serialize_pydantic_return
async def get_recording(
    recording_sid: str,
    account_sid: str,
    api_key: str,
) -> GetRecordingOutput:
    """Retrieve call recording information by recording SID."""
    if not api_key or not api_key.strip():
        return GetRecordingOutput(
            success=False,
            error="Twilio Auth Token is empty. Please configure a valid Twilio credential.",
        )
    if not account_sid or not account_sid.strip():
        return GetRecordingOutput(success=False, error="Twilio Account SID is required.")
    if not recording_sid or not recording_sid.strip():
        return GetRecordingOutput(success=False, error="Recording SID is required.")

    endpoint = f"{_API_BASE}/Accounts/{account_sid}/Recordings/{recording_sid}.json"
    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.get(endpoint, auth=(account_sid, api_key))
        data = response.json()
        if response.status_code != 200 or data.get("error_code"):
            return GetRecordingOutput(
                success=False,
                error=(
                    data.get("message")
                    or data.get("error_message")
                    or f"Twilio API error ({response.status_code}): {response.text}"
                ),
            )
    except httpx.TimeoutException:
        return GetRecordingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetRecordingOutput(success=False, error=f"get_recording failed: {exc}")

    uri = data.get("uri")
    media_url = data.get("media_url")
    if not media_url and uri:
        # The downloadable media lives at the recording URI without the
        # ``.json`` suffix (append ``.mp3``/``.wav`` to fetch audio).
        media_url = f"https://api.twilio.com{uri}".removesuffix(".json")

    return GetRecordingOutput(
        success=True,
        recording_sid=data.get("sid"),
        call_sid=data.get("call_sid"),
        duration=_to_int(data.get("duration")),
        status=data.get("status"),
        channels=_to_int(data.get("channels")),
        source=data.get("source"),
        media_url=media_url,
        price=data.get("price"),
        price_unit=data.get("price_unit"),
        uri=uri,
        # TODO (unverified): the base Recording resource does not return
        # transcription_* fields; they are populated only when a separate
        # Transcription resource exists. Left permissive (None default) per
        # https://www.twilio.com/docs/voice/api/recording
        transcription_text=data.get("transcription_text"),
        transcription_status=data.get("transcription_status"),
        transcription_price=data.get("transcription_price"),
        transcription_price_unit=data.get("transcription_price_unit"),
    )


# --- Helpers ---------------------------------------------------------------


def _to_int(value: Any) -> int | None:
    """Twilio returns numeric fields as strings; coerce defensively."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
