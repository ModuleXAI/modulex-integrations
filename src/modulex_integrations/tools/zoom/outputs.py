"""Pydantic response models for the zoom integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddMeetingRegistrantOutput",
    "AddWebinarRegistrantOutput",
    "CreateMeetingOutput",
    "CreateUserOutput",
    "DeleteMeetingOutput",
    "DeleteUserOutput",
    "GetCurrentUserOutput",
    "GetMeetingDetailsOutput",
    "GetMeetingRecordingsOutput",
    "GetMeetingSummaryOutput",
    "GetMeetingTranscriptOutput",
    "GetWebinarDetailsOutput",
    "ListAllRecordingsOutput",
    "ListCallRecordingsOutput",
    "ListChannelsOutput",
    "ListMeetingsOutput",
    "ListPastMeetingParticipantsOutput",
    "ListPastWebinarQaOutput",
    "ListUserCallLogsOutput",
    "ListWebinarParticipantsReportOutput",
    "MeetingSummary",
    "MeetingWebinarItem",
    "ParticipantItem",
    "QaItem",
    "RecordingFile",
    "RecordingMeeting",
    "RegistrantResponse",
    "SendChatMessageOutput",
    "UpdateMeetingOutput",
    "UpdateWebinarOutput",
    "UserInfo",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class MeetingWebinarItem(_Base):
    id: int | None = None
    uuid: str | None = None
    topic: str | None = None
    type: int | None = None
    start_time: str | None = None
    duration: int | None = None
    timezone: str | None = None
    join_url: str | None = None
    status: str | None = None


class UserInfo(_Base):
    id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    email: str | None = None
    account_id: str | None = None
    timezone: str | None = None
    type: int | None = None


class RecordingFile(_Base):
    id: str | None = None
    meeting_id: str | None = None
    recording_start: str | None = None
    recording_end: str | None = None
    file_type: str | None = None
    file_size: int | None = None
    download_url: str | None = None
    play_url: str | None = None
    status: str | None = None
    recording_type: str | None = None


class RecordingMeeting(_Base):
    uuid: str | None = None
    id: int | None = None
    topic: str | None = None
    start_time: str | None = None
    duration: int | None = None
    total_size: int | None = None
    recording_count: int | None = None
    recording_files: list[RecordingFile] = Field(default_factory=list)


class ParticipantItem(_Base):
    id: str | None = None
    name: str | None = None
    user_email: str | None = None
    join_time: str | None = None
    leave_time: str | None = None
    duration: int | None = None


class RegistrantResponse(_Base):
    id: str | None = None
    registrant_id: str | None = None
    start_time: str | None = None
    join_url: str | None = None
    topic: str | None = None


class MeetingSummary(_Base):
    meeting_id: int | None = None
    meeting_uuid: str | None = None
    summary_title: str | None = None
    summary_overview: str | None = None
    summary_details: str | None = None
    next_steps: list[str] = Field(default_factory=list)


class QaItem(_Base):
    question: str | None = None
    answer: str | None = None
    name: str | None = None
    email: str | None = None


# --- Per-action output models ---------------------------------------------


class CreateMeetingOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    uuid: str | None = None
    topic: str | None = None
    start_time: str | None = None
    join_url: str | None = None
    password: str | None = None
    start_url: str | None = None


class ListMeetingsOutput(_Base):
    success: bool
    error: str | None = None
    meetings: list[MeetingWebinarItem] = Field(default_factory=list)
    total_records: int | None = None


class GetMeetingDetailsOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    uuid: str | None = None
    topic: str | None = None
    type: int | None = None
    start_time: str | None = None
    duration: int | None = None
    timezone: str | None = None
    join_url: str | None = None
    password: str | None = None
    status: str | None = None
    host_email: str | None = None


class UpdateMeetingOutput(_Base):
    success: bool
    error: str | None = None


class DeleteMeetingOutput(_Base):
    success: bool
    error: str | None = None


class GetCurrentUserOutput(_Base):
    success: bool
    error: str | None = None
    user: UserInfo | None = None


class SendChatMessageOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class ListChannelsOutput(_Base):
    success: bool
    error: str | None = None
    channels: list[dict[str, str | int | None]] = Field(default_factory=list)


class AddMeetingRegistrantOutput(_Base):
    success: bool
    error: str | None = None
    registrant: RegistrantResponse | None = None


class GetMeetingRecordingsOutput(_Base):
    success: bool
    error: str | None = None
    recording_files: list[RecordingFile] = Field(default_factory=list)
    download_access_token: str | None = None


class GetMeetingTranscriptOutput(_Base):
    success: bool
    error: str | None = None
    transcript_url: str | None = None
    transcript_text: str | None = None


class GetMeetingSummaryOutput(_Base):
    success: bool
    error: str | None = None
    summary: MeetingSummary | None = None


class ListAllRecordingsOutput(_Base):
    success: bool
    error: str | None = None
    meetings: list[RecordingMeeting] = Field(default_factory=list)
    total_records: int | None = None


class ListCallRecordingsOutput(_Base):
    success: bool
    error: str | None = None
    recordings: list[dict[str, str | int | None]] = Field(default_factory=list)
    total_records: int | None = None


class ListUserCallLogsOutput(_Base):
    success: bool
    error: str | None = None
    call_logs: list[dict[str, str | int | None]] = Field(default_factory=list)
    total_records: int | None = None


class ListPastMeetingParticipantsOutput(_Base):
    success: bool
    error: str | None = None
    participants: list[ParticipantItem] = Field(default_factory=list)
    total_records: int | None = None


class CreateUserOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    type: int | None = None


class DeleteUserOutput(_Base):
    success: bool
    error: str | None = None


class GetWebinarDetailsOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    uuid: str | None = None
    topic: str | None = None
    type: int | None = None
    start_time: str | None = None
    duration: int | None = None
    timezone: str | None = None
    join_url: str | None = None
    host_email: str | None = None


class UpdateWebinarOutput(_Base):
    success: bool
    error: str | None = None


class AddWebinarRegistrantOutput(_Base):
    success: bool
    error: str | None = None
    registrant: RegistrantResponse | None = None


class ListWebinarParticipantsReportOutput(_Base):
    success: bool
    error: str | None = None
    participants: list[ParticipantItem] = Field(default_factory=list)
    total_records: int | None = None


class ListPastWebinarQaOutput(_Base):
    success: bool
    error: str | None = None
    questions: list[QaItem] = Field(default_factory=list)
