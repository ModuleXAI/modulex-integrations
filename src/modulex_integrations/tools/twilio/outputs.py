"""Pydantic response models for the twilio integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CallResource",
    "CheckVerificationTokenOutput",
    "CreateVerificationServiceOutput",
    "DeleteCallOutput",
    "DeleteMessageOutput",
    "DownloadRecordingMediaOutput",
    "GetCallOutput",
    "GetMessageOutput",
    "GetTranscriptsOutput",
    "ListCallsOutput",
    "ListMessageMediaOutput",
    "ListMessagesOutput",
    "ListPhoneNumbersOutput",
    "ListTranscriptsOutput",
    "LookupResult",
    "MakePhoneCallOutput",
    "MediaResource",
    "MessageResource",
    "PhoneNumberInfo",
    "PhoneNumberLookupOutput",
    "SendMessageOutput",
    "SendSmsVerificationOutput",
    "TranscriptResource",
    "TranscriptSentence",
    "VerificationResource",
    "VerificationServiceResource",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class MessageResource(_Base):
    sid: str | None = None
    date_created: str | None = None
    date_updated: str | None = None
    date_sent: str | None = None
    account_sid: str | None = None
    to: str | None = None
    from_number: str | None = None
    body: str | None = None
    status: str | None = None
    num_segments: str | None = None
    num_media: str | None = None
    direction: str | None = None
    price: str | None = None
    price_unit: str | None = None
    error_code: int | None = None
    error_message: str | None = None
    uri: str | None = None


class CallResource(_Base):
    sid: str | None = None
    date_created: str | None = None
    date_updated: str | None = None
    account_sid: str | None = None
    to: str | None = None
    to_formatted: str | None = None
    from_number: str | None = None
    from_formatted: str | None = None
    status: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    duration: str | None = None
    price: str | None = None
    price_unit: str | None = None
    direction: str | None = None
    uri: str | None = None


class MediaResource(_Base):
    sid: str | None = None
    content_type: str | None = None
    date_created: str | None = None
    date_updated: str | None = None
    uri: str | None = None


class LookupResult(_Base):
    phone_number: str | None = None
    country_code: str | None = None
    calling_country_code: str | None = None
    national_format: str | None = None
    valid: bool | None = None
    validation_errors: list[str] = Field(default_factory=list)
    line_type: str | None = None
    carrier_name: str | None = None


class VerificationResource(_Base):
    sid: str | None = None
    service_sid: str | None = None
    account_sid: str | None = None
    to: str | None = None
    channel: str | None = None
    status: str | None = None
    valid: bool | None = None
    date_created: str | None = None
    date_updated: str | None = None


class VerificationServiceResource(_Base):
    sid: str | None = None
    account_sid: str | None = None
    friendly_name: str | None = None
    code_length: int | None = None
    lookup_enabled: bool | None = None
    date_created: str | None = None
    date_updated: str | None = None


class TranscriptSentence(_Base):
    media_channel: int | None = None
    sentence_index: int | None = None
    start_time: float | None = None
    end_time: float | None = None
    transcript: str | None = None
    confidence: float | None = None


class TranscriptResource(_Base):
    sid: str | None = None
    account_sid: str | None = None
    service_sid: str | None = None
    status: str | None = None
    date_created: str | None = None
    date_updated: str | None = None
    duration: int | None = None
    channel: str | None = None
    sentences: list[TranscriptSentence] = Field(default_factory=list)
    transcript_text: str | None = None


class PhoneNumberInfo(_Base):
    sid: str | None = None
    phone_number: str | None = None
    friendly_name: str | None = None


# --- Per-action output models ---------------------------------------------


class SendMessageOutput(_Base):
    success: bool
    error: str | None = None
    message: MessageResource | None = None


class MakePhoneCallOutput(_Base):
    success: bool
    error: str | None = None
    call: CallResource | None = None


class GetMessageOutput(_Base):
    success: bool
    error: str | None = None
    message: MessageResource | None = None


class DeleteMessageOutput(_Base):
    success: bool
    error: str | None = None


class ListMessagesOutput(_Base):
    success: bool
    error: str | None = None
    messages: list[MessageResource] = Field(default_factory=list)


class ListMessageMediaOutput(_Base):
    success: bool
    error: str | None = None
    media: list[MediaResource] = Field(default_factory=list)


class GetCallOutput(_Base):
    success: bool
    error: str | None = None
    call: CallResource | None = None


class DeleteCallOutput(_Base):
    success: bool
    error: str | None = None


class ListCallsOutput(_Base):
    success: bool
    error: str | None = None
    calls: list[CallResource] = Field(default_factory=list)


class DownloadRecordingMediaOutput(_Base):
    success: bool
    error: str | None = None
    download_url: str | None = None
    recording_sid: str | None = None
    format: str | None = None


class PhoneNumberLookupOutput(_Base):
    success: bool
    error: str | None = None
    lookup: LookupResult | None = None


class SendSmsVerificationOutput(_Base):
    success: bool
    error: str | None = None
    verification: VerificationResource | None = None


class CheckVerificationTokenOutput(_Base):
    success: bool
    error: str | None = None
    verification: VerificationResource | None = None


class CreateVerificationServiceOutput(_Base):
    success: bool
    error: str | None = None
    service: VerificationServiceResource | None = None


class ListTranscriptsOutput(_Base):
    success: bool
    error: str | None = None
    transcripts: list[TranscriptResource] = Field(default_factory=list)


class GetTranscriptsOutput(_Base):
    success: bool
    error: str | None = None
    transcripts: list[TranscriptResource] = Field(default_factory=list)


class ListPhoneNumbersOutput(_Base):
    success: bool
    error: str | None = None
    phone_numbers: list[PhoneNumberInfo] = Field(default_factory=list)
