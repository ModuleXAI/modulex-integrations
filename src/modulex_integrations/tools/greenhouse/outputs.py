"""Pydantic response models for the Greenhouse integration's @tool functions.

Every model mirrors an object documented in the Greenhouse Harvest API
reference (``https://harvest.greenhouse.io/v1``). Two shapes recur:

* **List endpoints** answer with a top-level JSON array, so each
  ``List*Output`` carries the parsed array plus ``count`` (how many
  objects this page held) and ``next_page`` (parsed out of the RFC 5988
  ``Link`` response header — ``None`` when the current page is the last).
* **Retrieve endpoints** answer with a single JSON object, so each
  ``Get*Output`` flattens that object's attributes onto the envelope.

Every model uses ``extra="forbid"`` and keeps each field permissive
(``| None = None`` for scalars, ``default_factory=list`` for lists):
Greenhouse omits attributes depending on the API key's per-endpoint
permissions, on the plan, and on whether a value was ever set.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "Answer",
    "ApplicationLocation",
    "ApplicationSummary",
    "Attachment",
    "CandidateSummary",
    "Department",
    "DepartmentRef",
    "Education",
    "Employment",
    "GetApplicationOutput",
    "GetCandidateOutput",
    "GetJobOutput",
    "GetUserOutput",
    "HiringTeam",
    "HiringTeamMember",
    "Interview",
    "InterviewKit",
    "InterviewKitQuestion",
    "JobStage",
    "JobSummary",
    "ListApplicationsOutput",
    "ListCandidatesOutput",
    "ListDepartmentsOutput",
    "ListJobStagesOutput",
    "ListJobsOutput",
    "ListOfficesOutput",
    "ListUsersOutput",
    "NamedRef",
    "Office",
    "OfficeLocation",
    "OfficeRef",
    "Opening",
    "RejectionReason",
    "Source",
    "TypedValue",
    "User",
    "UserRef",
]


class _Base(BaseModel):
    """Shared config: reject unknown keys so drift surfaces immediately."""

    model_config = ConfigDict(extra="forbid")


# --- Shared building blocks -------------------------------------------------


class NamedRef(_Base):
    """A minimal ``{id, name}`` reference (stage, job, close reason, type)."""

    id: int | None = None
    name: str | None = None


class TypedValue(_Base):
    """One entry of a candidate's contact-detail arrays.

    Used for ``email_addresses``, ``phone_numbers``, ``addresses``,
    ``website_addresses`` and ``social_media_addresses`` (the last one
    carries no ``type``).
    """

    value: str | None = None
    type: str | None = None


class UserRef(_Base):
    """A Greenhouse user as embedded on another object."""

    id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    name: str | None = None
    employee_id: str | None = None


class HiringTeamMember(UserRef):
    """A hiring-team member; recruiters and coordinators add ``responsible``."""

    responsible: bool | None = None


class HiringTeam(_Base):
    """The four hiring-team roles a job carries."""

    hiring_managers: list[HiringTeamMember] = Field(default_factory=list)
    recruiters: list[HiringTeamMember] = Field(default_factory=list)
    coordinators: list[HiringTeamMember] = Field(default_factory=list)
    sourcers: list[HiringTeamMember] = Field(default_factory=list)


class Attachment(_Base):
    """A file attached to a candidate or application.

    Download URLs are pre-signed and expire seven days after they are
    generated.
    """

    filename: str | None = None
    url: str | None = None
    type: str | None = None
    created_at: str | None = None


class Education(_Base):
    """One entry of a candidate's education history."""

    id: int | None = None
    school_name: str | None = None
    degree: str | None = None
    discipline: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class Employment(_Base):
    """One entry of a candidate's employment history."""

    id: int | None = None
    company_name: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class OfficeLocation(_Base):
    """The human-readable location an office resolves to."""

    name: str | None = None


class DepartmentRef(_Base):
    """A department as embedded on a job."""

    id: int | None = None
    name: str | None = None
    parent_id: int | None = None


class OfficeRef(_Base):
    """An office as embedded on a job."""

    id: int | None = None
    name: str | None = None
    location: OfficeLocation | None = None


class Opening(_Base):
    """A single headcount slot on a job."""

    id: int | None = None
    opening_id: str | None = None
    status: str | None = None
    opened_at: str | None = None
    closed_at: str | None = None
    application_id: int | None = None
    close_reason: NamedRef | None = None


class Source(_Base):
    """Where an application came from."""

    id: int | None = None
    public_name: str | None = None


class RejectionReason(_Base):
    """Why an application was rejected."""

    id: int | None = None
    name: str | None = None
    type: NamedRef | None = None


class ApplicationLocation(_Base):
    """The answer to the location question on a job post."""

    address: str | None = None


class Answer(_Base):
    """One question/answer pair from a job post."""

    question: str | None = None
    answer: str | None = None


# --- List item models -------------------------------------------------------


class CandidateSummary(_Base):
    """A candidate as returned by the list endpoint."""

    id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    title: str | None = None
    is_private: bool | None = None
    can_email: bool | None = None
    email_addresses: list[TypedValue] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    application_ids: list[int] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    last_activity: str | None = None


class JobSummary(_Base):
    """A job as returned by the list endpoint."""

    id: int | None = None
    name: str | None = None
    status: str | None = None
    confidential: bool | None = None
    departments: list[DepartmentRef] = Field(default_factory=list)
    offices: list[OfficeRef] = Field(default_factory=list)
    opened_at: str | None = None
    closed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ApplicationSummary(_Base):
    """An application as returned by the list endpoint."""

    id: int | None = None
    candidate_id: int | None = None
    prospect: bool | None = None
    status: str | None = None
    current_stage: NamedRef | None = None
    jobs: list[NamedRef] = Field(default_factory=list)
    applied_at: str | None = None
    rejected_at: str | None = None
    last_activity_at: str | None = None


class User(_Base):
    """A Greenhouse user (recruiter, coordinator, hiring manager, admin)."""

    id: int | None = None
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    primary_email_address: str | None = None
    disabled: bool | None = None
    site_admin: bool | None = None
    emails: list[str] = Field(default_factory=list)
    employee_id: str | None = None
    linked_candidate_ids: list[int] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class Department(_Base):
    """A department in the organization's hierarchy."""

    id: int | None = None
    name: str | None = None
    parent_id: int | None = None
    child_ids: list[int] = Field(default_factory=list)
    external_id: str | None = None


class Office(_Base):
    """An office in the organization's hierarchy."""

    id: int | None = None
    name: str | None = None
    location: OfficeLocation | None = None
    primary_contact_user_id: int | None = None
    parent_id: int | None = None
    child_ids: list[int] = Field(default_factory=list)
    external_id: str | None = None


class InterviewKitQuestion(_Base):
    """One question on an interview kit (may contain basic HTML)."""

    id: int | None = None
    question: str | None = None


class InterviewKit(_Base):
    """Prep content and questions attached to an interview step."""

    id: int | None = None
    content: str | None = None
    questions: list[InterviewKitQuestion] = Field(default_factory=list)


class Interview(_Base):
    """One interview step inside a job stage."""

    id: int | None = None
    name: str | None = None
    schedulable: bool | None = None
    estimated_minutes: int | None = None
    default_interviewer_users: list[UserRef] = Field(default_factory=list)
    interview_kit: InterviewKit | None = None


class JobStage(_Base):
    """An interview stage on a job; ``priority`` orders them ascending."""

    id: int | None = None
    name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    job_id: int | None = None
    priority: int | None = None
    active: bool | None = None
    interviews: list[Interview] = Field(default_factory=list)


# --- Per-action outputs -----------------------------------------------------


class ListCandidatesOutput(_Base):
    """Result of ``list_candidates``."""

    success: bool
    error: str | None = None
    candidates: list[CandidateSummary] = Field(default_factory=list)
    count: int | None = None
    next_page: int | None = None


class GetCandidateOutput(_Base):
    """Result of ``get_candidate``."""

    success: bool
    error: str | None = None
    id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    title: str | None = None
    is_private: bool | None = None
    can_email: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None
    last_activity: str | None = None
    email_addresses: list[TypedValue] = Field(default_factory=list)
    phone_numbers: list[TypedValue] = Field(default_factory=list)
    addresses: list[TypedValue] = Field(default_factory=list)
    website_addresses: list[TypedValue] = Field(default_factory=list)
    social_media_addresses: list[TypedValue] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    application_ids: list[int] = Field(default_factory=list)
    recruiter: UserRef | None = None
    coordinator: UserRef | None = None
    attachments: list[Attachment] = Field(default_factory=list)
    educations: list[Education] = Field(default_factory=list)
    employments: list[Employment] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class ListJobsOutput(_Base):
    """Result of ``list_jobs``."""

    success: bool
    error: str | None = None
    jobs: list[JobSummary] = Field(default_factory=list)
    count: int | None = None
    next_page: int | None = None


class GetJobOutput(_Base):
    """Result of ``get_job``."""

    success: bool
    error: str | None = None
    id: int | None = None
    name: str | None = None
    requisition_id: str | None = None
    status: str | None = None
    confidential: bool | None = None
    created_at: str | None = None
    opened_at: str | None = None
    closed_at: str | None = None
    updated_at: str | None = None
    is_template: bool | None = None
    notes: str | None = None
    departments: list[DepartmentRef] = Field(default_factory=list)
    offices: list[OfficeRef] = Field(default_factory=list)
    hiring_team: HiringTeam | None = None
    openings: list[Opening] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class ListApplicationsOutput(_Base):
    """Result of ``list_applications``."""

    success: bool
    error: str | None = None
    applications: list[ApplicationSummary] = Field(default_factory=list)
    count: int | None = None
    next_page: int | None = None


class GetApplicationOutput(_Base):
    """Result of ``get_application``."""

    success: bool
    error: str | None = None
    id: int | None = None
    candidate_id: int | None = None
    prospect: bool | None = None
    status: str | None = None
    applied_at: str | None = None
    rejected_at: str | None = None
    last_activity_at: str | None = None
    location: ApplicationLocation | None = None
    source: Source | None = None
    credited_to: UserRef | None = None
    recruiter: UserRef | None = None
    coordinator: UserRef | None = None
    current_stage: NamedRef | None = None
    rejection_reason: RejectionReason | None = None
    jobs: list[NamedRef] = Field(default_factory=list)
    job_post_id: int | None = None
    answers: list[Answer] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class ListUsersOutput(_Base):
    """Result of ``list_users``."""

    success: bool
    error: str | None = None
    users: list[User] = Field(default_factory=list)
    count: int | None = None
    next_page: int | None = None


class GetUserOutput(_Base):
    """Result of ``get_user``."""

    success: bool
    error: str | None = None
    id: int | None = None
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    primary_email_address: str | None = None
    disabled: bool | None = None
    site_admin: bool | None = None
    emails: list[str] = Field(default_factory=list)
    employee_id: str | None = None
    linked_candidate_ids: list[int] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class ListDepartmentsOutput(_Base):
    """Result of ``list_departments``."""

    success: bool
    error: str | None = None
    departments: list[Department] = Field(default_factory=list)
    count: int | None = None
    next_page: int | None = None


class ListOfficesOutput(_Base):
    """Result of ``list_offices``."""

    success: bool
    error: str | None = None
    offices: list[Office] = Field(default_factory=list)
    count: int | None = None
    next_page: int | None = None


class ListJobStagesOutput(_Base):
    """Result of ``list_job_stages``."""

    success: bool
    error: str | None = None
    stages: list[JobStage] = Field(default_factory=list)
    count: int | None = None
    next_page: int | None = None
