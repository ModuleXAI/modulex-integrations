"""Pydantic response models for the Ashby integration's @tool functions.

Ashby's API is RPC-style: every endpoint is a ``POST`` to
``https://api.ashbyhq.com/<resource>.<verb>`` and every response is
wrapped in an envelope — ``{"success": true, "results": ...}`` on
success and ``{"success": false, "errorInfo": {...}}`` (or
``{"success": false, "errors": [...]}``) on failure. Because Ashby
returns HTTP 200 for what would normally be a 4XX, the envelope's
``success`` flag is mapped onto our own ``success``/``error`` fields:
a 200 carrying ``success: false`` still produces ``success=False``
with the upstream message.

Every model uses ``extra="forbid"`` and keeps each field permissive
(``| None = None`` for scalars, ``default_factory=list`` for lists) —
Ashby omits fields depending on the API key's permission scopes and
on which ``expand`` values were requested.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddCandidateTagOutput",
    "Application",
    "ApplicationArchiveReason",
    "ApplicationHistoryEntry",
    "ApplicationJobSummary",
    "ArchiveReason",
    "Candidate",
    "CandidateLocation",
    "CandidateSummary",
    "ChangeApplicationStageOutput",
    "CompensationSummaryComponent",
    "CompensationTier",
    "ContactInfo",
    "CreateApplicationOutput",
    "CreateCandidateOutput",
    "CreateNoteOutput",
    "CustomFieldDefinition",
    "CustomFieldSelectableValue",
    "CustomFieldValue",
    "Department",
    "DescriptionPart",
    "DescriptionParts",
    "FileHandle",
    "GetApplicationOutput",
    "GetCandidateOutput",
    "GetJobOutput",
    "GetJobPostingOutput",
    "GetOfferOutput",
    "HiringTeamMember",
    "InterviewEvent",
    "InterviewSchedule",
    "InterviewStageSummary",
    "Job",
    "JobCompensation",
    "JobLocation",
    "JobPosting",
    "JobPostingAddress",
    "JobPostingCompensation",
    "JobPostingLocationIds",
    "JobPostingSummary",
    "ListApplicationsOutput",
    "ListArchiveReasonsOutput",
    "ListCandidateTagsOutput",
    "ListCandidatesOutput",
    "ListCustomFieldsOutput",
    "ListDepartmentsOutput",
    "ListInterviewsOutput",
    "ListJobPostingsOutput",
    "ListJobsOutput",
    "ListLocationsOutput",
    "ListNotesOutput",
    "ListOffersOutput",
    "ListOpeningsOutput",
    "ListSourcesOutput",
    "ListUsersOutput",
    "Location",
    "LocationComponent",
    "Note",
    "NoteAuthor",
    "Offer",
    "OfferVersion",
    "Opening",
    "OpeningVersion",
    "PostalAddress",
    "RemoveCandidateTagOutput",
    "Salary",
    "SearchCandidatesOutput",
    "SocialLink",
    "SourceSummary",
    "SourceType",
    "Tag",
    "UpdateCandidateOutput",
    "UserSummary",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Shared building blocks -------------------------------------------------


class ContactInfo(_Base):
    """An email address or phone number attached to a candidate."""

    value: str | None = None
    type: str | None = None
    is_primary: bool | None = None


class SocialLink(_Base):
    """A social profile link (LinkedIn, GitHub, Twitter, ...)."""

    type: str | None = None
    url: str | None = None


class CustomFieldValue(_Base):
    """A custom field value set on a record."""

    id: str | None = None
    title: str | None = None
    is_private: bool | None = None
    value_label: str | None = None
    value: Any = None


class FileHandle(_Base):
    """A reference to a stored file (resume, offer letter, ...)."""

    id: str | None = None
    name: str | None = None
    handle: str | None = None


class UserSummary(_Base):
    """A summary of an Ashby user."""

    id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    global_role: str | None = None
    is_enabled: bool | None = None
    updated_at: str | None = None
    manager_id: str | None = None


class SourceType(_Base):
    """The grouping a candidate source belongs to."""

    id: str | None = None
    title: str | None = None
    is_archived: bool | None = None


class SourceSummary(_Base):
    """A candidate/application attribution source."""

    id: str | None = None
    title: str | None = None
    is_archived: bool | None = None
    source_type: SourceType | None = None


class Tag(_Base):
    """A candidate tag."""

    id: str | None = None
    title: str | None = None
    is_archived: bool | None = None


class LocationComponent(_Base):
    """One structured part of a candidate location (city, region, ...)."""

    type: str | None = None
    name: str | None = None


class CandidateLocation(_Base):
    """A candidate's location, summary plus structured components."""

    id: str | None = None
    location_summary: str | None = None
    location_components: list[LocationComponent] = Field(default_factory=list)


class HiringTeamMember(_Base):
    """A member of a job or application hiring team."""

    user_id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    role: str | None = None


class PostalAddress(_Base):
    """A postal address."""

    address_country: str | None = None
    address_region: str | None = None
    address_locality: str | None = None
    postal_code: str | None = None
    street_address: str | None = None


class NoteAuthor(_Base):
    """The Ashby user who authored a note."""

    id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None


# --- Candidate --------------------------------------------------------------


class Candidate(_Base):
    """A candidate record."""

    id: str | None = None
    name: str | None = None
    primary_email_address: ContactInfo | None = None
    primary_phone_number: ContactInfo | None = None
    email_addresses: list[ContactInfo] = Field(default_factory=list)
    phone_numbers: list[ContactInfo] = Field(default_factory=list)
    social_links: list[SocialLink] = Field(default_factory=list)
    linkedin_url: str | None = None
    github_url: str | None = None
    profile_url: str | None = None
    position: str | None = None
    company: str | None = None
    school: str | None = None
    timezone: str | None = None
    location: CandidateLocation | None = None
    tags: list[Tag] = Field(default_factory=list)
    application_ids: list[str] = Field(default_factory=list)
    custom_fields: list[CustomFieldValue] = Field(default_factory=list)
    resume_file_handle: FileHandle | None = None
    file_handles: list[FileHandle] = Field(default_factory=list)
    source: SourceSummary | None = None
    credited_to_user: UserSummary | None = None
    fraud_status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


# --- Job / openings ---------------------------------------------------------


class OpeningVersion(_Base):
    """The latest version of a headcount opening."""

    id: str | None = None
    identifier: str | None = None
    description: str | None = None
    author_id: str | None = None
    created_at: str | None = None
    team_id: str | None = None
    job_ids: list[str] = Field(default_factory=list)
    target_hire_date: str | None = None
    target_start_date: str | None = None
    is_backfill: bool | None = None
    employment_type: str | None = None
    location_ids: list[str] = Field(default_factory=list)
    hiring_team: list[HiringTeamMember] = Field(default_factory=list)
    custom_fields: list[CustomFieldValue] = Field(default_factory=list)


class Opening(_Base):
    """A headcount opening."""

    id: str | None = None
    opened_at: str | None = None
    closed_at: str | None = None
    is_archived: bool | None = None
    archived_at: str | None = None
    close_reason_id: str | None = None
    opening_state: str | None = None
    latest_version: OpeningVersion | None = None


class JobLocation(_Base):
    """The primary location attached to a job."""

    id: str | None = None
    name: str | None = None
    external_name: str | None = None
    is_archived: bool | None = None
    is_remote: bool | None = None
    workplace_type: str | None = None
    parent_location_id: str | None = None
    type: str | None = None
    address: PostalAddress | None = None


class CompensationTier(_Base):
    """One compensation tier configured on a job."""

    id: str | None = None
    title: str | None = None
    additional_information: str | None = None
    tier_summary: str | None = None


class JobCompensation(_Base):
    """Job compensation, present only when expanded in the request."""

    compensation_tiers: list[CompensationTier] = Field(default_factory=list)


class Job(_Base):
    """A job (requisition)."""

    id: str | None = None
    title: str | None = None
    confidential: bool | None = None
    status: str | None = None
    employment_type: str | None = None
    location_id: str | None = None
    department_id: str | None = None
    default_interview_plan_id: str | None = None
    interview_plan_ids: list[str] = Field(default_factory=list)
    custom_fields: list[CustomFieldValue] = Field(default_factory=list)
    job_posting_ids: list[str] = Field(default_factory=list)
    custom_requisition_id: str | None = None
    brand_id: str | None = None
    hiring_team: list[HiringTeamMember] = Field(default_factory=list)
    author: UserSummary | None = None
    created_at: str | None = None
    updated_at: str | None = None
    opened_at: str | None = None
    closed_at: str | None = None
    location: JobLocation | None = None
    openings: list[Opening] = Field(default_factory=list)
    compensation: JobCompensation | None = None


# --- Application ------------------------------------------------------------


class CandidateSummary(_Base):
    """The trimmed candidate embedded in an application."""

    id: str | None = None
    name: str | None = None
    primary_email_address: ContactInfo | None = None
    primary_phone_number: ContactInfo | None = None


class InterviewStageSummary(_Base):
    """The interview stage an application currently sits in."""

    id: str | None = None
    title: str | None = None
    type: str | None = None
    order_in_interview_plan: int | None = None
    interview_stage_group_id: str | None = None
    interview_plan_id: str | None = None


class ApplicationArchiveReason(_Base):
    """The archive reason recorded on an archived application."""

    id: str | None = None
    text: str | None = None
    reason_type: str | None = None
    is_archived: bool | None = None
    custom_fields: list[CustomFieldValue] = Field(default_factory=list)


class ApplicationJobSummary(_Base):
    """The trimmed job embedded in an application."""

    id: str | None = None
    title: str | None = None
    location_id: str | None = None
    department_id: str | None = None


class ApplicationHistoryEntry(_Base):
    """One stage-history entry on an application."""

    id: str | None = None
    stage_id: str | None = None
    stage_number: int | None = None
    title: str | None = None
    entered_stage_at: str | None = None
    actor_id: str | None = None


class Application(_Base):
    """An application (a candidate considered for a job)."""

    id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    status: str | None = None
    custom_fields: list[CustomFieldValue] = Field(default_factory=list)
    candidate: CandidateSummary | None = None
    current_interview_stage: InterviewStageSummary | None = None
    source: SourceSummary | None = None
    archive_reason: ApplicationArchiveReason | None = None
    archived_at: str | None = None
    job: ApplicationJobSummary | None = None
    credited_to_user: UserSummary | None = None
    hiring_team: list[HiringTeamMember] = Field(default_factory=list)
    applied_via_job_posting_id: str | None = None
    submitter_client_ip: str | None = None
    submitter_user_agent: str | None = None
    application_history: list[ApplicationHistoryEntry] = Field(default_factory=list)


# --- Notes ------------------------------------------------------------------


class Note(_Base):
    """A note recorded on a candidate."""

    id: str | None = None
    content: str | None = None
    is_private: bool | None = None
    author: NoteAuthor | None = None
    created_at: str | None = None


# --- Offers -----------------------------------------------------------------


class Salary(_Base):
    """The salary recorded on an offer version."""

    currency_code: str | None = None
    value: float | None = None


class OfferVersion(_Base):
    """The most recent version of an offer."""

    id: str | None = None
    start_date: str | None = None
    salary: Salary | None = None
    created_at: str | None = None
    opening_id: str | None = None
    custom_fields: list[CustomFieldValue] = Field(default_factory=list)
    file_handles: list[FileHandle] = Field(default_factory=list)
    author: UserSummary | None = None
    approval_status: str | None = None


class Offer(_Base):
    """An offer extended to a candidate."""

    id: str | None = None
    decided_at: str | None = None
    application_id: str | None = None
    acceptance_status: str | None = None
    offer_status: str | None = None
    latest_version: OfferVersion | None = None


# --- Organization reference data --------------------------------------------


class ArchiveReason(_Base):
    """A configured archive reason."""

    id: str | None = None
    text: str | None = None
    reason_type: str | None = None
    is_archived: bool | None = None


class CustomFieldSelectableValue(_Base):
    """One selectable value of a select-style custom field."""

    label: str | None = None
    value: str | None = None
    is_archived: bool | None = None


class CustomFieldDefinition(_Base):
    """A custom field definition."""

    id: str | None = None
    title: str | None = None
    is_private: bool | None = None
    field_type: str | None = None
    object_type: str | None = None
    is_archived: bool | None = None
    is_required: bool | None = None
    selectable_values: list[CustomFieldSelectableValue] = Field(default_factory=list)


class Department(_Base):
    """A department."""

    id: str | None = None
    name: str | None = None
    external_name: str | None = None
    is_archived: bool | None = None
    parent_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    extra_data: dict[str, Any] | None = None


class Location(_Base):
    """A configured location."""

    id: str | None = None
    name: str | None = None
    external_name: str | None = None
    is_archived: bool | None = None
    is_remote: bool | None = None
    workplace_type: str | None = None
    parent_location_id: str | None = None
    type: str | None = None
    address: PostalAddress | None = None
    extra_data: dict[str, Any] | None = None


# --- Job postings -----------------------------------------------------------


class JobPostingLocationIds(_Base):
    """Primary and secondary location ids of a job posting."""

    primary_location_id: str | None = None
    secondary_location_ids: list[str] = Field(default_factory=list)


class JobPostingSummary(_Base):
    """A job posting as returned by the list endpoint."""

    id: str | None = None
    title: str | None = None
    job_id: str | None = None
    department_name: str | None = None
    team_name: str | None = None
    location_name: str | None = None
    location_ids: JobPostingLocationIds | None = None
    workplace_type: str | None = None
    employment_type: str | None = None
    is_listed: bool | None = None
    published_date: str | None = None
    application_deadline: str | None = None
    external_link: str | None = None
    apply_link: str | None = None
    compensation_tier_summary: str | None = None
    should_display_compensation_on_job_board: bool | None = None
    updated_at: str | None = None


class DescriptionPart(_Base):
    """One HTML/plain-text section of a job posting description."""

    html: str | None = None
    plain: str | None = None


class DescriptionParts(_Base):
    """The opening/body/closing sections of a job posting description."""

    description_opening: DescriptionPart | None = None
    description_body: DescriptionPart | None = None
    description_closing: DescriptionPart | None = None


class JobPostingAddress(_Base):
    """The address block of a job posting."""

    postal_address: PostalAddress | None = None


class CompensationSummaryComponent(_Base):
    """One component of a job posting's compensation summary."""

    summary: str | None = None
    compensation_type_label: str | None = None
    interval: str | None = None
    currency_code: str | None = None
    min_value: float | None = None
    max_value: float | None = None


class JobPostingCompensation(_Base):
    """The compensation block displayed on a job posting."""

    compensation_tier_summary: str | None = None
    summary_components: list[CompensationSummaryComponent] = Field(default_factory=list)
    should_display_compensation_on_job_board: bool | None = None


class JobPosting(_Base):
    """A job posting with its full description."""

    id: str | None = None
    title: str | None = None
    description_plain: str | None = None
    description_html: str | None = None
    description_social: str | None = None
    description_parts: DescriptionParts | None = None
    department_name: str | None = None
    team_name: str | None = None
    team_name_hierarchy: list[str] = Field(default_factory=list)
    job_id: str | None = None
    location_name: str | None = None
    location_ids: JobPostingLocationIds | None = None
    address: JobPostingAddress | None = None
    is_remote: bool | None = None
    workplace_type: str | None = None
    employment_type: str | None = None
    is_listed: bool | None = None
    suppress_description_opening: bool | None = None
    suppress_description_closing: bool | None = None
    published_date: str | None = None
    application_deadline: str | None = None
    external_link: str | None = None
    apply_link: str | None = None
    compensation: JobPostingCompensation | None = None
    application_limit_callout_html: str | None = None
    updated_at: str | None = None
    job: dict[str, Any] | None = None


# --- Interviews -------------------------------------------------------------


class InterviewEvent(_Base):
    """A single scheduled interview event."""

    id: str | None = None
    interview_id: str | None = None
    interview_schedule_id: str | None = None
    interviewer_user_ids: list[str] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    feedback_link: str | None = None
    location: str | None = None
    meeting_link: str | None = None
    has_submitted_feedback: bool | None = None


class InterviewSchedule(_Base):
    """An interview schedule with its events."""

    id: str | None = None
    status: str | None = None
    application_id: str | None = None
    interview_stage_id: str | None = None
    scheduled_by: UserSummary | None = None
    created_at: str | None = None
    updated_at: str | None = None
    interview_events: list[InterviewEvent] = Field(default_factory=list)


# --- Per-action output models -----------------------------------------------


class ListCandidatesOutput(_Base):
    success: bool
    error: str | None = None
    candidates: list[Candidate] = Field(default_factory=list)
    more_data_available: bool | None = None
    next_cursor: str | None = None


class GetCandidateOutput(Candidate):
    success: bool
    error: str | None = None


class CreateCandidateOutput(Candidate):
    success: bool
    error: str | None = None


class UpdateCandidateOutput(Candidate):
    success: bool
    error: str | None = None


class AddCandidateTagOutput(Candidate):
    success: bool
    error: str | None = None


class RemoveCandidateTagOutput(Candidate):
    success: bool
    error: str | None = None


class SearchCandidatesOutput(_Base):
    success: bool
    error: str | None = None
    candidates: list[Candidate] = Field(default_factory=list)


class ListJobsOutput(_Base):
    success: bool
    error: str | None = None
    jobs: list[Job] = Field(default_factory=list)
    more_data_available: bool | None = None
    next_cursor: str | None = None


class GetJobOutput(Job):
    success: bool
    error: str | None = None


class CreateNoteOutput(Note):
    success: bool
    error: str | None = None


class ListNotesOutput(_Base):
    success: bool
    error: str | None = None
    notes: list[Note] = Field(default_factory=list)
    more_data_available: bool | None = None
    next_cursor: str | None = None


class ListApplicationsOutput(_Base):
    success: bool
    error: str | None = None
    applications: list[Application] = Field(default_factory=list)
    more_data_available: bool | None = None
    next_cursor: str | None = None


class GetApplicationOutput(Application):
    success: bool
    error: str | None = None


class CreateApplicationOutput(Application):
    success: bool
    error: str | None = None


class ChangeApplicationStageOutput(Application):
    success: bool
    error: str | None = None


class ListOffersOutput(_Base):
    success: bool
    error: str | None = None
    offers: list[Offer] = Field(default_factory=list)
    more_data_available: bool | None = None
    next_cursor: str | None = None


class GetOfferOutput(Offer):
    success: bool
    error: str | None = None


class ListSourcesOutput(_Base):
    success: bool
    error: str | None = None
    sources: list[SourceSummary] = Field(default_factory=list)


class ListCandidateTagsOutput(_Base):
    success: bool
    error: str | None = None
    tags: list[Tag] = Field(default_factory=list)
    more_data_available: bool | None = None
    next_cursor: str | None = None
    sync_token: str | None = None


class ListArchiveReasonsOutput(_Base):
    success: bool
    error: str | None = None
    archive_reasons: list[ArchiveReason] = Field(default_factory=list)


class ListCustomFieldsOutput(_Base):
    success: bool
    error: str | None = None
    custom_fields: list[CustomFieldDefinition] = Field(default_factory=list)
    more_data_available: bool | None = None
    next_cursor: str | None = None
    sync_token: str | None = None


class ListDepartmentsOutput(_Base):
    success: bool
    error: str | None = None
    departments: list[Department] = Field(default_factory=list)
    more_data_available: bool | None = None
    next_cursor: str | None = None
    sync_token: str | None = None


class ListLocationsOutput(_Base):
    success: bool
    error: str | None = None
    locations: list[Location] = Field(default_factory=list)
    more_data_available: bool | None = None
    next_cursor: str | None = None
    sync_token: str | None = None


class ListJobPostingsOutput(_Base):
    success: bool
    error: str | None = None
    job_postings: list[JobPostingSummary] = Field(default_factory=list)


class GetJobPostingOutput(JobPosting):
    success: bool
    error: str | None = None


class ListOpeningsOutput(_Base):
    success: bool
    error: str | None = None
    openings: list[Opening] = Field(default_factory=list)
    more_data_available: bool | None = None
    next_cursor: str | None = None


class ListUsersOutput(_Base):
    success: bool
    error: str | None = None
    users: list[UserSummary] = Field(default_factory=list)
    more_data_available: bool | None = None
    next_cursor: str | None = None


class ListInterviewsOutput(_Base):
    success: bool
    error: str | None = None
    interview_schedules: list[InterviewSchedule] = Field(default_factory=list)
    more_data_available: bool | None = None
    next_cursor: str | None = None
