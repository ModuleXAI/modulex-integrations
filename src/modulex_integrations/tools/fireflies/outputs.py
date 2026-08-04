"""Pydantic response models for the Fireflies integration's @tool functions.

Fireflies exposes a single GraphQL endpoint (``https://api.fireflies.ai/graphql``),
so every action posts a query or mutation and reads its typed result out of the
``data`` envelope. The models below flatten those GraphQL nodes into stable
snake_case shapes.

The API answers HTTP 200 for practically everything — successes and failures
alike, with failures carried in a top-level ``errors`` array — so each model
carries ``success`` + ``error`` and every data field stays optional.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddToLiveMeetingOutput",
    "CreateBiteOutput",
    "DeleteTranscriptOutput",
    "FirefliesAiFilters",
    "FirefliesAnalytics",
    "FirefliesAttendee",
    "FirefliesBite",
    "FirefliesCategories",
    "FirefliesContact",
    "FirefliesSentence",
    "FirefliesSentiments",
    "FirefliesSpeaker",
    "FirefliesSpeakerAnalytics",
    "FirefliesSummary",
    "FirefliesTranscript",
    "FirefliesUser",
    "GetTranscriptOutput",
    "GetUserOutput",
    "ListBitesOutput",
    "ListContactsOutput",
    "ListTranscriptsOutput",
    "ListUsersOutput",
    "UploadAudioOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class FirefliesSpeaker(_Base):
    """A diarized speaker detected in a recording."""

    id: int | None = None
    name: str | None = None


class FirefliesAttendee(_Base):
    """A calendar attendee attached to a meeting."""

    display_name: str | None = None
    email: str | None = None
    phone_number: str | None = None
    name: str | None = None
    location: str | None = None


class FirefliesAiFilters(_Base):
    """Per-sentence AI classification flags."""

    task: bool | None = None
    pricing: bool | None = None
    metric: bool | None = None
    question: bool | None = None
    date_and_time: bool | None = None
    sentiment: str | None = None


class FirefliesSentence(_Base):
    """One utterance in a transcript, with speaker attribution and timing."""

    index: int | None = None
    speaker_name: str | None = None
    speaker_id: int | None = None
    text: str | None = None
    raw_text: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    ai_filters: FirefliesAiFilters | None = None


class FirefliesSummary(_Base):
    """The AI-generated meeting summary block.

    Several fields are documented as "a list of ..." but are delivered as a
    single newline-separated string on most meetings, so they are typed as a
    union rather than forced into one shape.
    """

    keywords: str | list[str] | None = None
    action_items: str | list[str] | None = None
    outline: str | list[str] | None = None
    shorthand_bullet: str | list[str] | None = None
    overview: str | None = None
    bullet_gist: str | list[str] | None = None
    gist: str | None = None
    short_summary: str | None = None
    short_overview: str | None = None
    meeting_type: str | None = None
    topics_discussed: str | list[str] | None = None


class FirefliesSentiments(_Base):
    """Sentiment split across the whole meeting, in percent."""

    negative_pct: float | None = None
    neutral_pct: float | None = None
    positive_pct: float | None = None


class FirefliesCategories(_Base):
    """Counts of AI-detected sentence categories across the meeting."""

    questions: int | None = None
    date_times: int | None = None
    metrics: int | None = None
    tasks: int | None = None


class FirefliesSpeakerAnalytics(_Base):
    """Talk-time and speaking-style analytics for one speaker."""

    speaker_id: int | None = None
    name: str | None = None
    duration: float | None = None
    word_count: int | None = None
    longest_monologue: float | None = None
    monologues_count: int | None = None
    filler_words: int | None = None
    questions: int | None = None
    duration_pct: float | None = None
    words_per_minute: float | None = None


class FirefliesAnalytics(_Base):
    """Meeting-level analytics: sentiment, category counts, per-speaker stats."""

    sentiments: FirefliesSentiments | None = None
    categories: FirefliesCategories | None = None
    speakers: list[FirefliesSpeakerAnalytics] = Field(default_factory=list)


class FirefliesTranscript(_Base):
    """A recorded meeting and everything derived from it.

    List actions populate only the summary-level fields (id, title, date,
    duration, host email, participants); the single-transcript action fills in
    sentences, summary, and analytics as well.
    """

    id: str | None = None
    title: str | None = None
    date: float | None = None
    date_string: str | None = None
    duration: float | None = None
    privacy: str | None = None
    transcript_url: str | None = None
    audio_url: str | None = None
    video_url: str | None = None
    meeting_link: str | None = None
    host_email: str | None = None
    organizer_email: str | None = None
    participants: list[str] = Field(default_factory=list)
    fireflies_users: list[str] = Field(default_factory=list)
    speakers: list[FirefliesSpeaker] = Field(default_factory=list)
    meeting_attendees: list[FirefliesAttendee] = Field(default_factory=list)
    sentences: list[FirefliesSentence] = Field(default_factory=list)
    summary: FirefliesSummary | None = None
    analytics: FirefliesAnalytics | None = None


class FirefliesUser(_Base):
    """A member of the workspace/team."""

    user_id: str | None = None
    name: str | None = None
    email: str | None = None
    integrations: list[str] = Field(default_factory=list)
    is_admin: bool | None = None
    minutes_consumed: float | None = None
    num_transcripts: int | None = None
    recent_transcript: str | None = None
    recent_meeting: str | None = None


class FirefliesBite(_Base):
    """A soundbite — a clipped highlight of a recording."""

    id: str | None = None
    name: str | None = None
    transcript_id: str | None = None
    user_id: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    status: str | None = None
    summary: str | None = None
    media_type: str | None = None
    thumbnail: str | None = None
    preview: str | None = None
    created_at: str | None = None


class FirefliesContact(_Base):
    """Someone the account has met with."""

    email: str | None = None
    name: str | None = None
    picture: str | None = None
    last_meeting_date: str | None = None


# --- Per-action output models ----------------------------------------------


class ListTranscriptsOutput(_Base):
    success: bool
    error: str | None = None
    transcripts: list[FirefliesTranscript] = Field(default_factory=list)
    count: int | None = None


class GetTranscriptOutput(_Base):
    success: bool
    error: str | None = None
    transcript: FirefliesTranscript | None = None


class GetUserOutput(_Base):
    success: bool
    error: str | None = None
    user: FirefliesUser | None = None


class ListUsersOutput(_Base):
    success: bool
    error: str | None = None
    users: list[FirefliesUser] = Field(default_factory=list)


class UploadAudioOutput(_Base):
    success: bool
    error: str | None = None
    uploaded: bool = False
    title: str | None = None
    message: str | None = None


class DeleteTranscriptOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool = False
    transcript: FirefliesTranscript | None = None


class AddToLiveMeetingOutput(_Base):
    success: bool
    error: str | None = None
    added: bool = False


class CreateBiteOutput(_Base):
    success: bool
    error: str | None = None
    bite: FirefliesBite | None = None


class ListBitesOutput(_Base):
    success: bool
    error: str | None = None
    bites: list[FirefliesBite] = Field(default_factory=list)


class ListContactsOutput(_Base):
    success: bool
    error: str | None = None
    contacts: list[FirefliesContact] = Field(default_factory=list)
