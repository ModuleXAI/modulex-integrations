"""Fireflies LangChain ``@tool`` functions.

Ten async tools wrapping the Fireflies.ai GraphQL API. The whole public
surface is served from one endpoint — ``POST https://api.fireflies.ai/graphql``
— so every action posts a ``{"query": ..., "variables": ...}`` document and
reads its result out of the ``data`` envelope. Query documents are module
constants and every caller-supplied value travels in ``variables``, never
interpolated into the document text.

Calling convention is the modulex *api_key* one: the ``ToolExecutor`` injects
``api_key: str`` directly (resolved from the user's ``api_key`` credential),
not an ``auth_type``/``auth_data`` pair. The key travels as
``Authorization: Bearer <api_key>``.

Error model: GraphQL answers HTTP 200 for nearly everything, so transport
failures, non-200 responses, and the top-level ``errors`` array are all folded
into one ``success=False`` + ``error`` envelope. Nothing raises past the
``@tool`` boundary: response bodies are shape-guarded with ``_as_dict`` /
``_as_list`` and every field is routed through a scalar coercer inside the
``_parse_*`` helpers, so a wrongly typed 200 degrades instead of escaping as a
``ValidationError``.
"""
from __future__ import annotations

import json
from typing import Any, NamedTuple

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.fireflies.outputs import (
    AddToLiveMeetingOutput,
    CreateBiteOutput,
    DeleteTranscriptOutput,
    FirefliesAiFilters,
    FirefliesAnalytics,
    FirefliesAttendee,
    FirefliesBite,
    FirefliesCategories,
    FirefliesContact,
    FirefliesSentence,
    FirefliesSentiments,
    FirefliesSpeaker,
    FirefliesSpeakerAnalytics,
    FirefliesSummary,
    FirefliesTranscript,
    FirefliesUser,
    GetTranscriptOutput,
    GetUserOutput,
    ListBitesOutput,
    ListContactsOutput,
    ListTranscriptsOutput,
    ListUsersOutput,
    UploadAudioOutput,
)

__all__ = [
    "add_to_live_meeting",
    "create_bite",
    "delete_transcript",
    "get_transcript",
    "get_user",
    "list_bites",
    "list_contacts",
    "list_transcripts",
    "list_users",
    "upload_audio",
]

# The single GraphQL endpoint. No action parameter ever reaches the host, so
# the credential can only ever be sent to this compile-time constant.
_API_URL = "https://api.fireflies.ai/graphql"
# Transcripts carry every sentence of a meeting, so the read path can be slow.
_TIMEOUT = 60.0
# The API caps list queries at 50 records per call.
_MAX_LIMIT = 50

_EMPTY_KEY_ERROR = "Fireflies API key is empty. Please configure a valid Fireflies credential."

# Closed value set for the soundbite media type, mirroring the API's enum.
_MEDIA_TYPES = ("video", "audio")

# Error codes the add-to-live endpoint returns, mapped to readable messages.
_LIVE_MEETING_ERRORS = {
    "too_many_requests": "Rate limit exceeded. This endpoint allows 3 requests per 20 minutes.",
    "invalid_language_code": "Invalid language code provided.",
    "unsupported_platform": "Meeting platform is not supported.",
}


# --- GraphQL documents -----------------------------------------------------

_LIST_TRANSCRIPTS_QUERY = """
  query Transcripts(
    $keyword: String
    $fromDate: DateTime
    $toDate: DateTime
    $host_email: String
    $participants: [String!]
    $limit: Int
    $skip: Int
  ) {
    transcripts(
      keyword: $keyword
      fromDate: $fromDate
      toDate: $toDate
      host_email: $host_email
      participants: $participants
      limit: $limit
      skip: $skip
    ) {
      id
      title
      date
      duration
      host_email
      participants
    }
  }
"""

_GET_TRANSCRIPT_QUERY = """
  query Transcript($id: String!) {
    transcript(id: $id) {
      id
      title
      date
      dateString
      duration
      privacy
      transcript_url
      audio_url
      video_url
      meeting_link
      host_email
      organizer_email
      participants
      fireflies_users
      speakers {
        id
        name
      }
      meeting_attendees {
        displayName
        email
        phoneNumber
        name
        location
      }
      sentences {
        index
        speaker_name
        speaker_id
        text
        raw_text
        start_time
        end_time
        ai_filters {
          task
          pricing
          metric
          question
          date_and_time
          sentiment
        }
      }
      summary {
        keywords
        action_items
        outline
        shorthand_bullet
        overview
        bullet_gist
        gist
        short_summary
        short_overview
        meeting_type
        topics_discussed
      }
      analytics {
        sentiments {
          negative_pct
          neutral_pct
          positive_pct
        }
        categories {
          questions
          date_times
          metrics
          tasks
        }
        speakers {
          speaker_id
          name
          duration
          word_count
          longest_monologue
          monologues_count
          filler_words
          questions
          duration_pct
          words_per_minute
        }
      }
    }
  }
"""

_USER_SELECTION = """
  user_id
  name
  email
  integrations
  is_admin
  minutes_consumed
  num_transcripts
  recent_transcript
  recent_meeting
"""

_GET_USER_QUERY = f"""
  query User($id: String) {{
    user(id: $id) {{
      {_USER_SELECTION}
    }}
  }}
"""

_LIST_USERS_QUERY = f"""
  query Users {{
    users {{
      {_USER_SELECTION}
    }}
  }}
"""

_UPLOAD_AUDIO_MUTATION = """
  mutation UploadAudio($input: AudioUploadInput) {
    uploadAudio(input: $input) {
      success
      title
      message
    }
  }
"""

_DELETE_TRANSCRIPT_MUTATION = """
  mutation DeleteTranscript($id: String!) {
    deleteTranscript(id: $id) {
      id
      title
      date
      duration
      host_email
      organizer_email
    }
  }
"""

_ADD_TO_LIVE_MEETING_MUTATION = """
  mutation AddToLiveMeeting(
    $meetingLink: String!
    $title: String
    $meeting_password: String
    $duration: Int
    $language: String
  ) {
    addToLiveMeeting(
      meeting_link: $meetingLink
      title: $title
      meeting_password: $meeting_password
      duration: $duration
      language: $language
    ) {
      success
    }
  }
"""

_CREATE_BITE_MUTATION = """
  mutation CreateBite(
    $transcriptId: ID!
    $startTime: Float!
    $endTime: Float!
    $name: String
    $media_type: String
    $summary: String
  ) {
    createBite(
      transcript_id: $transcriptId
      start_time: $startTime
      end_time: $endTime
      name: $name
      media_type: $media_type
      summary: $summary
    ) {
      id
      name
      status
    }
  }
"""

_LIST_BITES_QUERY = """
  query Bites($mine: Boolean, $transcript_id: ID, $limit: Int, $skip: Int) {
    bites(mine: $mine, transcript_id: $transcript_id, limit: $limit, skip: $skip) {
      id
      name
      transcript_id
      user_id
      start_time
      end_time
      status
      summary
      media_type
      thumbnail
      preview
      created_at
    }
  }
"""

_LIST_CONTACTS_QUERY = """
  query Contacts {
    contacts {
      email
      name
      picture
      last_meeting_date
    }
  }
"""


# --- Transport helpers -----------------------------------------------------


class _ApiError(NamedTuple):
    """A ready-to-surface failure, plus the upstream error code when present."""

    message: str
    code: str | None = None


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _as_dict(payload: Any) -> dict[str, Any]:
    """A non-object payload degrades to empty rather than raising."""
    return payload if isinstance(payload, dict) else {}


def _as_list(payload: Any) -> list[Any]:
    """A non-array payload degrades to empty rather than raising."""
    return payload if isinstance(payload, list) else []


def _as_str(value: Any) -> str | None:
    """Coerce a scalar to str; anything else degrades to None.

    The response models type ids and labels as ``str | None``, but model
    construction happens after the ``except`` clauses — so an upstream field
    arriving with the wrong type would raise ``ValidationError`` past the
    ``@tool`` boundary instead of returning the ``success=False`` envelope.
    """
    if value is None or isinstance(value, (dict, list)):
        return None
    return value if isinstance(value, str) else str(value)


def _as_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    # Counts occasionally arrive as whole floats (1.0); the schema also types
    # some numeric fields (`speaker_id: ID`) as strings, so a numeric string is
    # read too. Anything fractional or non-numeric degrades to None.
    number = _as_float(value)
    if number is not None and number.is_integer():
        return int(number)
    return None


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    # The schema types several numeric fields (sentence/bite `start_time` and
    # `end_time`) as String, so a numeric string is read rather than dropped.
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _as_str_list(value: Any) -> list[str]:
    """Coerce an array of scalars to ``list[str]``, dropping unusable members."""
    return [item for item in (_as_str(entry) for entry in _as_list(value)) if item is not None]


def _as_text(value: Any) -> str | list[str] | None:
    """Summary blocks arrive as either one string or a list of strings."""
    if isinstance(value, list):
        return _as_str_list(value)
    return _as_str(value)


async def _graphql(
    api_key: str,
    query: str,
    variables: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], _ApiError | None]:
    """POST one GraphQL document and return ``(data, error)``.

    ``error`` is populated for transport failures, non-200 responses, and
    top-level GraphQL ``errors``; it is ``None`` when ``data`` holds a usable
    object.
    """
    payload: dict[str, Any] = {"query": query}
    if variables is not None:
        payload["variables"] = variables

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(_API_URL, headers=_headers(api_key), json=payload)
        if response.status_code != 200:
            return {}, _ApiError(
                f"Fireflies API error ({response.status_code}): {response.text}"
            )
        body = _as_dict(response.json())
    except httpx.TimeoutException:
        return {}, _ApiError("Request to the Fireflies API timed out.")
    except Exception as exc:
        return {}, _ApiError(f"Fireflies API request failed: {exc}")

    errors = _as_list(body.get("errors"))
    if errors:
        first = _as_dict(errors[0])
        message = _as_str(first.get("message"))
        code = _as_str(_as_dict(first.get("extensions")).get("code"))
        detail = message if message else "unknown error"
        if code:
            detail = f"{detail} ({code})"
        return {}, _ApiError(f"Fireflies API error: {detail}", code)

    data = body.get("data")
    if not isinstance(data, dict):
        return {}, _ApiError("Fireflies API returned no data.")
    return data, None


# --- Parsing helpers -------------------------------------------------------


def _parse_speaker(raw: dict[str, Any]) -> FirefliesSpeaker:
    return FirefliesSpeaker(id=_as_int(raw.get("id")), name=_as_str(raw.get("name")))


def _parse_attendee(raw: dict[str, Any]) -> FirefliesAttendee:
    return FirefliesAttendee(
        display_name=_as_str(raw.get("displayName")),
        email=_as_str(raw.get("email")),
        phone_number=_as_str(raw.get("phoneNumber")),
        name=_as_str(raw.get("name")),
        location=_as_str(raw.get("location")),
    )


def _parse_ai_filters(raw: dict[str, Any]) -> FirefliesAiFilters:
    return FirefliesAiFilters(
        task=_as_bool(raw.get("task")),
        pricing=_as_bool(raw.get("pricing")),
        metric=_as_bool(raw.get("metric")),
        question=_as_bool(raw.get("question")),
        date_and_time=_as_bool(raw.get("date_and_time")),
        sentiment=_as_str(raw.get("sentiment")),
    )


def _parse_sentence(raw: dict[str, Any]) -> FirefliesSentence:
    filters = _as_dict(raw.get("ai_filters"))
    return FirefliesSentence(
        index=_as_int(raw.get("index")),
        speaker_name=_as_str(raw.get("speaker_name")),
        speaker_id=_as_int(raw.get("speaker_id")),
        text=_as_str(raw.get("text")),
        raw_text=_as_str(raw.get("raw_text")),
        start_time=_as_float(raw.get("start_time")),
        end_time=_as_float(raw.get("end_time")),
        ai_filters=_parse_ai_filters(filters) if filters else None,
    )


def _parse_summary(raw: dict[str, Any]) -> FirefliesSummary:
    return FirefliesSummary(
        keywords=_as_str_list(raw.get("keywords")),
        action_items=_as_text(raw.get("action_items")),
        outline=_as_text(raw.get("outline")),
        shorthand_bullet=_as_text(raw.get("shorthand_bullet")),
        overview=_as_str(raw.get("overview")),
        bullet_gist=_as_text(raw.get("bullet_gist")),
        gist=_as_str(raw.get("gist")),
        short_summary=_as_str(raw.get("short_summary")),
        short_overview=_as_str(raw.get("short_overview")),
        meeting_type=_as_str(raw.get("meeting_type")),
        topics_discussed=_as_text(raw.get("topics_discussed")),
    )


def _parse_analytics(raw: dict[str, Any]) -> FirefliesAnalytics:
    sentiments = _as_dict(raw.get("sentiments"))
    categories = _as_dict(raw.get("categories"))
    return FirefliesAnalytics(
        sentiments=(
            FirefliesSentiments(
                negative_pct=_as_float(sentiments.get("negative_pct")),
                neutral_pct=_as_float(sentiments.get("neutral_pct")),
                positive_pct=_as_float(sentiments.get("positive_pct")),
            )
            if sentiments
            else None
        ),
        categories=(
            FirefliesCategories(
                questions=_as_int(categories.get("questions")),
                date_times=_as_int(categories.get("date_times")),
                metrics=_as_int(categories.get("metrics")),
                tasks=_as_int(categories.get("tasks")),
            )
            if categories
            else None
        ),
        speakers=[
            FirefliesSpeakerAnalytics(
                speaker_id=_as_int(speaker.get("speaker_id")),
                name=_as_str(speaker.get("name")),
                duration=_as_float(speaker.get("duration")),
                word_count=_as_int(speaker.get("word_count")),
                longest_monologue=_as_float(speaker.get("longest_monologue")),
                monologues_count=_as_int(speaker.get("monologues_count")),
                filler_words=_as_int(speaker.get("filler_words")),
                questions=_as_int(speaker.get("questions")),
                duration_pct=_as_float(speaker.get("duration_pct")),
                words_per_minute=_as_float(speaker.get("words_per_minute")),
            )
            for speaker in (_as_dict(entry) for entry in _as_list(raw.get("speakers")))
        ],
    )


def _parse_transcript(raw: dict[str, Any]) -> FirefliesTranscript:
    summary = _as_dict(raw.get("summary"))
    analytics = _as_dict(raw.get("analytics"))
    return FirefliesTranscript(
        id=_as_str(raw.get("id")),
        title=_as_str(raw.get("title")),
        date=_as_float(raw.get("date")),
        date_string=_as_str(raw.get("dateString")),
        duration=_as_float(raw.get("duration")),
        privacy=_as_str(raw.get("privacy")),
        transcript_url=_as_str(raw.get("transcript_url")),
        audio_url=_as_str(raw.get("audio_url")),
        video_url=_as_str(raw.get("video_url")),
        meeting_link=_as_str(raw.get("meeting_link")),
        host_email=_as_str(raw.get("host_email")),
        organizer_email=_as_str(raw.get("organizer_email")),
        participants=_as_str_list(raw.get("participants")),
        fireflies_users=_as_str_list(raw.get("fireflies_users")),
        speakers=[
            _parse_speaker(_as_dict(entry)) for entry in _as_list(raw.get("speakers"))
        ],
        meeting_attendees=[
            _parse_attendee(_as_dict(entry))
            for entry in _as_list(raw.get("meeting_attendees"))
        ],
        sentences=[
            _parse_sentence(_as_dict(entry)) for entry in _as_list(raw.get("sentences"))
        ],
        summary=_parse_summary(summary) if summary else None,
        analytics=_parse_analytics(analytics) if analytics else None,
    )


def _parse_user(raw: dict[str, Any]) -> FirefliesUser:
    return FirefliesUser(
        user_id=_as_str(raw.get("user_id")),
        name=_as_str(raw.get("name")),
        email=_as_str(raw.get("email")),
        integrations=_as_str_list(raw.get("integrations")),
        is_admin=_as_bool(raw.get("is_admin")),
        minutes_consumed=_as_float(raw.get("minutes_consumed")),
        num_transcripts=_as_int(raw.get("num_transcripts")),
        recent_transcript=_as_str(raw.get("recent_transcript")),
        recent_meeting=_as_str(raw.get("recent_meeting")),
    )


def _parse_bite(raw: dict[str, Any]) -> FirefliesBite:
    return FirefliesBite(
        id=_as_str(raw.get("id")),
        name=_as_str(raw.get("name")),
        transcript_id=_as_str(raw.get("transcript_id")),
        user_id=_as_str(raw.get("user_id")),
        start_time=_as_float(raw.get("start_time")),
        end_time=_as_float(raw.get("end_time")),
        status=_as_str(raw.get("status")),
        summary=_as_str(raw.get("summary")),
        media_type=_as_str(raw.get("media_type")),
        thumbnail=_as_str(raw.get("thumbnail")),
        preview=_as_str(raw.get("preview")),
        created_at=_as_str(raw.get("created_at")),
    )


def _parse_contact(raw: dict[str, Any]) -> FirefliesContact:
    return FirefliesContact(
        email=_as_str(raw.get("email")),
        name=_as_str(raw.get("name")),
        picture=_as_str(raw.get("picture")),
        last_meeting_date=_as_str(raw.get("last_meeting_date")),
    )


# --- Input normalization ---------------------------------------------------


def _str_list(value: list[str] | str | None) -> list[str]:
    """Normalize a list filter, tolerating a comma-separated string."""
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(part).strip() for part in value if str(part).strip()]


def _clamp_limit(limit: int | None) -> int | None:
    """Keep a caller-supplied page size inside the API's 1..50 window."""
    if limit is None:
        return None
    return max(1, min(int(limit), _MAX_LIMIT))


_ATTENDEES_ERROR = (
    "attendees must be a JSON array of objects, e.g. "
    '[{"displayName": "Ada", "email": "ada@example.com"}].'
)


def _normalize_attendees(
    value: list[dict[str, Any]] | str | None,
) -> tuple[list[dict[str, Any]], str | None]:
    """Accept attendees either as a list of objects or as a JSON string."""
    if value is None:
        return [], None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return [], None
        try:
            parsed: Any = json.loads(text)
        except ValueError:
            return [], _ATTENDEES_ERROR
    else:
        parsed = value
    if not isinstance(parsed, list):
        return [], _ATTENDEES_ERROR
    attendees: list[dict[str, Any]] = []
    for entry in parsed:
        if not isinstance(entry, dict):
            return [], _ATTENDEES_ERROR
        attendees.append(entry)
    return attendees, None


# --- Input schemas (args_schema for each @tool) ----------------------------


class ListTranscriptsInput(BaseModel):
    api_key: str = Field(description="Fireflies API key (provided by credential system)")
    keyword: str | None = Field(
        default=None,
        description='Search meeting titles and spoken words (e.g. "quarterly review")',
    )
    from_date: str | None = Field(
        default=None,
        description="Only meetings from this ISO 8601 timestamp onwards (2026-01-01T00:00:00Z)",
    )
    to_date: str | None = Field(
        default=None,
        description="Only meetings up to this ISO 8601 timestamp (2026-12-31T23:59:59Z)",
    )
    host_email: str | None = Field(
        default=None, description="Filter by the meeting host's email address"
    )
    participants: list[str] | str | None = Field(
        default=None,
        description="Filter by participant email addresses (list or comma-separated string)",
    )
    limit: int | None = Field(
        default=None, description="Maximum number of transcripts to return (max 50)"
    )
    skip: int | None = Field(
        default=None, description="Number of transcripts to skip, for pagination"
    )


class GetTranscriptInput(BaseModel):
    transcript_id: str = Field(description='The transcript ID to retrieve (e.g. "abc123def456")')
    api_key: str = Field(description="Fireflies API key (provided by credential system)")


class GetUserInput(BaseModel):
    api_key: str = Field(description="Fireflies API key (provided by credential system)")
    user_id: str | None = Field(
        default=None,
        description="User ID to retrieve; omit to get the owner of the API key",
    )


class ListUsersInput(BaseModel):
    api_key: str = Field(description="Fireflies API key (provided by credential system)")


class UploadAudioInput(BaseModel):
    audio_url: str = Field(
        description=(
            "Public HTTPS URL of the audio/video file to transcribe "
            "(mp3, mp4, wav, m4a, ogg)"
        )
    )
    api_key: str = Field(description="Fireflies API key (provided by credential system)")
    title: str | None = Field(default=None, description="Title for the meeting/transcript")
    webhook: str | None = Field(
        default=None,
        description="URL the service calls when the transcription finishes",
    )
    language: str | None = Field(
        default=None,
        description='Transcription language code, e.g. "es", "de" (defaults to English)',
    )
    attendees: list[dict[str, Any]] | str | None = Field(
        default=None,
        description=(
            "Attendees as a JSON array of objects with displayName, email, "
            "and/or phoneNumber"
        ),
    )
    client_reference_id: str | None = Field(
        default=None, description="Custom reference ID echoed back on webhook events"
    )


class DeleteTranscriptInput(BaseModel):
    transcript_id: str = Field(description='The transcript ID to delete (e.g. "abc123def456")')
    api_key: str = Field(description="Fireflies API key (provided by credential system)")


class AddToLiveMeetingInput(BaseModel):
    meeting_link: str = Field(
        description="Meeting URL for Zoom, Google Meet, Microsoft Teams, etc."
    )
    api_key: str = Field(description="Fireflies API key (provided by credential system)")
    title: str | None = Field(
        default=None, description="Title for the meeting (max 256 characters)"
    )
    meeting_password: str | None = Field(
        default=None, description="Meeting password if one is required (max 32 characters)"
    )
    duration: int | None = Field(
        default=None,
        description="How long the bot should stay, in minutes (15-120, default 60)",
    )
    language: str | None = Field(
        default=None, description='Transcription language code, e.g. "en", "es", "de"'
    )


class CreateBiteInput(BaseModel):
    transcript_id: str = Field(description="ID of the transcript to clip the soundbite from")
    start_time: float = Field(description="Start of the soundbite, in seconds")
    end_time: float = Field(description="End of the soundbite, in seconds")
    api_key: str = Field(description="Fireflies API key (provided by credential system)")
    name: str | None = Field(
        default=None, description="Name for the soundbite (max 256 characters)"
    )
    media_type: str | None = Field(
        default=None, description="Soundbite media type: 'video' or 'audio'"
    )
    summary: str | None = Field(
        default=None, description="Summary of the soundbite (max 500 characters)"
    )


class ListBitesInput(BaseModel):
    api_key: str = Field(description="Fireflies API key (provided by credential system)")
    transcript_id: str | None = Field(
        default=None, description="Only return soundbites clipped from this transcript"
    )
    mine: bool = Field(
        default=True, description="Only return soundbites owned by the API key owner"
    )
    limit: int | None = Field(
        default=None, description="Maximum number of soundbites to return (max 50)"
    )
    skip: int | None = Field(
        default=None, description="Number of soundbites to skip, for pagination"
    )


class ListContactsInput(BaseModel):
    api_key: str = Field(description="Fireflies API key (provided by credential system)")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=ListTranscriptsInput)
@serialize_pydantic_return
async def list_transcripts(
    api_key: str,
    keyword: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    host_email: str | None = None,
    participants: list[str] | str | None = None,
    limit: int | None = None,
    skip: int | None = None,
) -> ListTranscriptsOutput:
    """List meeting transcripts, filtered by keyword, date range, host, or participant."""
    if not api_key or not api_key.strip():
        return ListTranscriptsOutput(success=False, error=_EMPTY_KEY_ERROR)

    variables: dict[str, Any] = {}
    if keyword and keyword.strip():
        variables["keyword"] = keyword.strip()
    if from_date and from_date.strip():
        variables["fromDate"] = from_date.strip()
    if to_date and to_date.strip():
        variables["toDate"] = to_date.strip()
    if host_email and host_email.strip():
        variables["host_email"] = host_email.strip()
    attendee_emails = _str_list(participants)
    if attendee_emails:
        variables["participants"] = attendee_emails
    page_size = _clamp_limit(limit)
    if page_size is not None:
        variables["limit"] = page_size
    if skip is not None:
        variables["skip"] = max(0, int(skip))

    data, error = await _graphql(api_key, _LIST_TRANSCRIPTS_QUERY, variables)
    if error is not None:
        return ListTranscriptsOutput(success=False, error=error.message)

    transcripts = [
        _parse_transcript(_as_dict(entry)) for entry in _as_list(data.get("transcripts"))
    ]
    return ListTranscriptsOutput(
        success=True, transcripts=transcripts, count=len(transcripts)
    )


@tool(args_schema=GetTranscriptInput)
@serialize_pydantic_return
async def get_transcript(transcript_id: str, api_key: str) -> GetTranscriptOutput:
    """Get one transcript in full, including its sentences, summary, action items, and analytics."""
    if not api_key or not api_key.strip():
        return GetTranscriptOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not transcript_id or not transcript_id.strip():
        return GetTranscriptOutput(success=False, error="transcript_id is required.")

    data, error = await _graphql(
        api_key, _GET_TRANSCRIPT_QUERY, {"id": transcript_id.strip()}
    )
    if error is not None:
        return GetTranscriptOutput(success=False, error=error.message)

    transcript = _as_dict(data.get("transcript"))
    if not transcript:
        return GetTranscriptOutput(
            success=False, error=f"Transcript '{transcript_id}' was not found."
        )
    return GetTranscriptOutput(success=True, transcript=_parse_transcript(transcript))


@tool(args_schema=GetUserInput)
@serialize_pydantic_return
async def get_user(api_key: str, user_id: str | None = None) -> GetUserOutput:
    """Get one user's profile and usage; returns the API key owner when no user ID is given."""
    if not api_key or not api_key.strip():
        return GetUserOutput(success=False, error=_EMPTY_KEY_ERROR)

    # The argument is nullable, but the upstream default (the key owner) only
    # applies when `id` is absent entirely — so omit it rather than send null.
    variables: dict[str, Any] = {}
    if user_id and user_id.strip():
        variables["id"] = user_id.strip()

    data, error = await _graphql(api_key, _GET_USER_QUERY, variables)
    if error is not None:
        return GetUserOutput(success=False, error=error.message)

    user = _as_dict(data.get("user"))
    if not user:
        return GetUserOutput(success=False, error="User not found.")
    return GetUserOutput(success=True, user=_parse_user(user))


@tool(args_schema=ListUsersInput)
@serialize_pydantic_return
async def list_users(api_key: str) -> ListUsersOutput:
    """List the users in your team, with their transcript counts and minutes consumed."""
    if not api_key or not api_key.strip():
        return ListUsersOutput(success=False, error=_EMPTY_KEY_ERROR)

    data, error = await _graphql(api_key, _LIST_USERS_QUERY)
    if error is not None:
        return ListUsersOutput(success=False, error=error.message)

    return ListUsersOutput(
        success=True,
        users=[_parse_user(_as_dict(entry)) for entry in _as_list(data.get("users"))],
    )


@tool(args_schema=UploadAudioInput)
@serialize_pydantic_return
async def upload_audio(
    audio_url: str,
    api_key: str,
    title: str | None = None,
    webhook: str | None = None,
    language: str | None = None,
    attendees: list[dict[str, Any]] | str | None = None,
    client_reference_id: str | None = None,
) -> UploadAudioOutput:
    """Submit a publicly reachable audio or video URL for transcription."""
    if not api_key or not api_key.strip():
        return UploadAudioOutput(success=False, error=_EMPTY_KEY_ERROR)

    url = (audio_url or "").strip()
    if not url:
        return UploadAudioOutput(success=False, error="audio_url is required.")
    if not url.startswith("https://"):
        return UploadAudioOutput(
            success=False, error="audio_url must be a publicly reachable https:// URL."
        )

    parsed_attendees, attendee_error = _normalize_attendees(attendees)
    if attendee_error is not None:
        return UploadAudioOutput(success=False, error=attendee_error)

    audio_input: dict[str, Any] = {"url": url}
    if title and title.strip():
        audio_input["title"] = title.strip()
    if webhook and webhook.strip():
        hook = webhook.strip()
        if not hook.lower().startswith(("http://", "https://")):
            return UploadAudioOutput(success=False, error="webhook must be an http(s) URL.")
        audio_input["webhook"] = hook
    if language and language.strip():
        audio_input["custom_language"] = language.strip()
    if client_reference_id and client_reference_id.strip():
        audio_input["client_reference_id"] = client_reference_id.strip()
    if parsed_attendees:
        audio_input["attendees"] = parsed_attendees

    data, error = await _graphql(
        api_key, _UPLOAD_AUDIO_MUTATION, {"input": audio_input}
    )
    if error is not None:
        return UploadAudioOutput(success=False, error=error.message)

    result = _as_dict(data.get("uploadAudio"))
    if not result:
        return UploadAudioOutput(success=False, error="Upload failed.")

    uploaded = _as_bool(result.get("success"))
    message = _as_str(result.get("message"))
    if uploaded is not True:
        return UploadAudioOutput(
            success=False,
            error=message or "Upload failed.",
            title=_as_str(result.get("title")),
            message=message,
        )
    return UploadAudioOutput(
        success=True,
        uploaded=True,
        title=_as_str(result.get("title")),
        message=message,
    )


@tool(args_schema=DeleteTranscriptInput)
@serialize_pydantic_return
async def delete_transcript(transcript_id: str, api_key: str) -> DeleteTranscriptOutput:
    """Delete a transcript; returns the details of the meeting that was removed."""
    if not api_key or not api_key.strip():
        return DeleteTranscriptOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not transcript_id or not transcript_id.strip():
        return DeleteTranscriptOutput(success=False, error="transcript_id is required.")

    data, error = await _graphql(
        api_key, _DELETE_TRANSCRIPT_MUTATION, {"id": transcript_id.strip()}
    )
    if error is not None:
        return DeleteTranscriptOutput(success=False, error=error.message)

    deleted = _as_dict(data.get("deleteTranscript"))
    if not deleted:
        return DeleteTranscriptOutput(
            success=False, error=f"Failed to delete transcript '{transcript_id}'."
        )
    return DeleteTranscriptOutput(
        success=True, deleted=True, transcript=_parse_transcript(deleted)
    )


@tool(args_schema=AddToLiveMeetingInput)
@serialize_pydantic_return
async def add_to_live_meeting(
    meeting_link: str,
    api_key: str,
    title: str | None = None,
    meeting_password: str | None = None,
    duration: int | None = None,
    language: str | None = None,
) -> AddToLiveMeetingOutput:
    """Send the notetaker bot into an ongoing meeting to record and transcribe it."""
    if not api_key or not api_key.strip():
        return AddToLiveMeetingOutput(success=False, error=_EMPTY_KEY_ERROR)

    link = (meeting_link or "").strip()
    if not link.lower().startswith(("http://", "https://")):
        return AddToLiveMeetingOutput(
            success=False, error="meeting_link must be a valid http(s) meeting URL."
        )

    variables: dict[str, Any] = {"meetingLink": link}
    if title and title.strip():
        variables["title"] = title.strip()[:256]
    if meeting_password and meeting_password.strip():
        variables["meeting_password"] = meeting_password.strip()[:32]
    if duration is not None:
        variables["duration"] = min(max(int(duration), 15), 120)
    if language and language.strip():
        variables["language"] = language.strip()[:5]

    data, error = await _graphql(api_key, _ADD_TO_LIVE_MEETING_MUTATION, variables)
    if error is not None:
        message = _LIVE_MEETING_ERRORS.get(error.code or "", error.message)
        return AddToLiveMeetingOutput(success=False, error=message)

    added = _as_bool(_as_dict(data.get("addToLiveMeeting")).get("success"))
    if added is not True:
        return AddToLiveMeetingOutput(
            success=False, error="The bot could not be added to the meeting."
        )
    return AddToLiveMeetingOutput(success=True, added=True)


@tool(args_schema=CreateBiteInput)
@serialize_pydantic_return
async def create_bite(
    transcript_id: str,
    start_time: float,
    end_time: float,
    api_key: str,
    name: str | None = None,
    media_type: str | None = None,
    summary: str | None = None,
) -> CreateBiteOutput:
    """Clip a soundbite (highlight) from a time range of a transcript."""
    if not api_key or not api_key.strip():
        return CreateBiteOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not transcript_id or not transcript_id.strip():
        return CreateBiteOutput(success=False, error="transcript_id is required.")
    if start_time >= end_time:
        return CreateBiteOutput(success=False, error="start_time must be less than end_time.")
    kind = (media_type or "").strip().lower()
    if kind and kind not in _MEDIA_TYPES:
        return CreateBiteOutput(
            success=False, error=f"media_type must be one of: {', '.join(_MEDIA_TYPES)}."
        )

    variables: dict[str, Any] = {
        "transcriptId": transcript_id.strip(),
        "startTime": float(start_time),
        "endTime": float(end_time),
    }
    if name and name.strip():
        variables["name"] = name.strip()[:256]
    if kind:
        variables["media_type"] = kind
    if summary and summary.strip():
        variables["summary"] = summary.strip()[:500]

    data, error = await _graphql(api_key, _CREATE_BITE_MUTATION, variables)
    if error is not None:
        return CreateBiteOutput(success=False, error=error.message)

    bite = _as_dict(data.get("createBite"))
    if not bite:
        return CreateBiteOutput(success=False, error="Failed to create the soundbite.")
    return CreateBiteOutput(success=True, bite=_parse_bite(bite))


@tool(args_schema=ListBitesInput)
@serialize_pydantic_return
async def list_bites(
    api_key: str,
    transcript_id: str | None = None,
    mine: bool = True,
    limit: int | None = None,
    skip: int | None = None,
) -> ListBitesOutput:
    """List soundbites (highlights), optionally only those clipped from one transcript."""
    if not api_key or not api_key.strip():
        return ListBitesOutput(success=False, error=_EMPTY_KEY_ERROR)

    variables: dict[str, Any] = {"mine": mine}
    if transcript_id and transcript_id.strip():
        variables["transcript_id"] = transcript_id.strip()
    page_size = _clamp_limit(limit)
    if page_size is not None:
        variables["limit"] = page_size
    if skip is not None:
        variables["skip"] = max(0, int(skip))

    data, error = await _graphql(api_key, _LIST_BITES_QUERY, variables)
    if error is not None:
        return ListBitesOutput(success=False, error=error.message)

    return ListBitesOutput(
        success=True,
        bites=[_parse_bite(_as_dict(entry)) for entry in _as_list(data.get("bites"))],
    )


@tool(args_schema=ListContactsInput)
@serialize_pydantic_return
async def list_contacts(api_key: str) -> ListContactsOutput:
    """List the people you have met with, with the date of the most recent meeting."""
    if not api_key or not api_key.strip():
        return ListContactsOutput(success=False, error=_EMPTY_KEY_ERROR)

    data, error = await _graphql(api_key, _LIST_CONTACTS_QUERY)
    if error is not None:
        return ListContactsOutput(success=False, error=error.message)

    return ListContactsOutput(
        success=True,
        contacts=[
            _parse_contact(_as_dict(entry)) for entry in _as_list(data.get("contacts"))
        ],
    )
