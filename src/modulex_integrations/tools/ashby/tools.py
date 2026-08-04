"""Ashby LangChain ``@tool`` functions.

Twenty-eight async tools wrapping the Ashby ATS API. The calling
convention is the modulex *api_key* one: the ``ToolExecutor`` injects
an ``api_key: str`` directly (resolved from the user's ``api_key``
credential), not an ``auth_type``/``auth_data`` pair.

Transport notes that shape every function below:

* Ashby is **RPC-style**. Every endpoint is a ``POST`` to
  ``https://api.ashbyhq.com/<resource>.<verb>`` — even reads such as
  ``candidate.list`` — with parameters in a JSON body. Endpoint paths
  are module-level constants; no action parameter ever reaches the URL.
* Auth is **HTTP Basic with the API key as the username and an empty
  password**, i.e. ``Authorization: Basic <base64("<key>:")>``. The
  ``Accept: application/json; version=1`` header pins the API version.
* Responses are enveloped: ``{"success": true, "results": ...}`` on
  success, ``{"success": false, "errorInfo": {...}}`` (or
  ``{"success": false, "errors": [...]}``) on failure — and Ashby
  returns **HTTP 200 for what would normally be a 4XX**. A 200 whose
  envelope says ``success: false`` is therefore mapped to
  ``success=False`` plus the upstream message. Missing-permission
  responses come back as 403 and bad credentials as 401 with a
  non-JSON body, so the status code is checked before parsing.
* List endpoints are cursor-paginated. The cursor is exposed as a
  parameter (``cursor`` in, ``next_cursor``/``more_data_available``
  out) rather than looped over, so a single call is always a single
  bounded request.

Error model: every call is wrapped in try/except and returns the typed
output with ``success=False`` + ``error`` for non-2xx responses,
envelope failures, timeouts, and unexpected exceptions rather than
raising.
"""
from __future__ import annotations

import base64
from datetime import UTC, datetime
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.ashby.outputs import (
    AddCandidateTagOutput,
    Application,
    ApplicationArchiveReason,
    ApplicationHistoryEntry,
    ApplicationJobSummary,
    ArchiveReason,
    Candidate,
    CandidateLocation,
    CandidateSummary,
    ChangeApplicationStageOutput,
    CompensationSummaryComponent,
    CompensationTier,
    ContactInfo,
    CreateApplicationOutput,
    CreateCandidateOutput,
    CreateNoteOutput,
    CustomFieldDefinition,
    CustomFieldSelectableValue,
    CustomFieldValue,
    Department,
    DescriptionPart,
    DescriptionParts,
    FileHandle,
    GetApplicationOutput,
    GetCandidateOutput,
    GetJobOutput,
    GetJobPostingOutput,
    GetOfferOutput,
    HiringTeamMember,
    InterviewEvent,
    InterviewSchedule,
    InterviewStageSummary,
    Job,
    JobCompensation,
    JobLocation,
    JobPostingAddress,
    JobPostingCompensation,
    JobPostingLocationIds,
    JobPostingSummary,
    ListApplicationsOutput,
    ListArchiveReasonsOutput,
    ListCandidatesOutput,
    ListCandidateTagsOutput,
    ListCustomFieldsOutput,
    ListDepartmentsOutput,
    ListInterviewsOutput,
    ListJobPostingsOutput,
    ListJobsOutput,
    ListLocationsOutput,
    ListNotesOutput,
    ListOffersOutput,
    ListOpeningsOutput,
    ListSourcesOutput,
    ListUsersOutput,
    Location,
    LocationComponent,
    Note,
    NoteAuthor,
    Offer,
    OfferVersion,
    Opening,
    OpeningVersion,
    PostalAddress,
    RemoveCandidateTagOutput,
    Salary,
    SearchCandidatesOutput,
    SocialLink,
    SourceSummary,
    SourceType,
    Tag,
    UpdateCandidateOutput,
    UserSummary,
)

__all__ = [
    "add_candidate_tag",
    "change_application_stage",
    "create_application",
    "create_candidate",
    "create_note",
    "get_application",
    "get_candidate",
    "get_job",
    "get_job_posting",
    "get_offer",
    "list_applications",
    "list_archive_reasons",
    "list_candidate_tags",
    "list_candidates",
    "list_custom_fields",
    "list_departments",
    "list_interviews",
    "list_job_postings",
    "list_jobs",
    "list_locations",
    "list_notes",
    "list_offers",
    "list_openings",
    "list_sources",
    "list_users",
    "remove_candidate_tag",
    "search_candidates",
    "update_candidate",
]

_ASHBY_API_BASE = "https://api.ashbyhq.com"
_TIMEOUT = 30.0
_EMPTY_KEY_ERROR = "Ashby API key is empty. Please configure a valid Ashby credential."


# --- Auth + transport helpers ----------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    """Ashby Basic auth: API key as username, empty password."""
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "Accept": "application/json; version=1",
    }


def _as_dict(payload: Any) -> dict[str, Any]:
    """A non-object body degrades to empty rather than raising."""
    return payload if isinstance(payload, dict) else {}


def _as_dict_list(payload: Any) -> list[dict[str, Any]]:
    """Keep only the object entries of a list payload."""
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _flag(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _whole(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) or isinstance(value, float):
        return float(value)
    return None


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _error_message(data: dict[str, Any], fallback: str) -> str:
    """Extract a readable message from an Ashby failure envelope."""
    info = data.get("errorInfo")
    if isinstance(info, dict):
        message = info.get("message")
        if isinstance(message, str) and message:
            code = info.get("code")
            if isinstance(code, str) and code:
                return f"{message} ({code})"
            return message
    errors = data.get("errors")
    if isinstance(errors, list) and errors:
        parts: list[str] = []
        for item in errors:
            if isinstance(item, dict):
                message = item.get("message")
                parts.append(message if isinstance(message, str) else str(item))
            else:
                parts.append(str(item))
        joined = "; ".join(part for part in parts if part)
        if joined:
            return joined
    return fallback


# Epoch values below this are seconds, above are milliseconds. 1e11 ms is
# 1973-03-03; 1e11 s is the year 5138 — no real date lands in both.
_EPOCH_MS_THRESHOLD = 100_000_000_000


def _iso_to_ms(value: str | None) -> int | None:
    """Ashby date filters take epoch milliseconds; accept ISO 8601 too."""
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.isdigit():
        epoch = int(text)
        # Callers (and LLMs) routinely emit epoch SECONDS. Passing those
        # through as milliseconds silently resolves to early 1970 and returns
        # a wrong-but-successful result. The two ranges do not overlap for any
        # realistic date: 1e11 milliseconds is 1973, 1e11 seconds is year 5138.
        return epoch * 1000 if epoch < _EPOCH_MS_THRESHOLD else epoch
    if text.endswith(("Z", "z")):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return int(parsed.timestamp() * 1000)


async def _call(
    endpoint: str, api_key: str, body: dict[str, Any], failure: str
) -> tuple[dict[str, Any], str | None]:
    """POST to an Ashby RPC endpoint and unwrap its response envelope.

    ``endpoint`` is always a module-level constant string — no action
    parameter is ever interpolated into the URL.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_ASHBY_API_BASE}/{endpoint}", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return {}, f"Ashby API error ({response.status_code}): {response.text}"
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return {}, "Request to the Ashby API timed out."
    except Exception as exc:
        return {}, f"{failure}: {exc}"
    if not data.get("success"):
        return {}, _error_message(data, failure)
    return data, None


# --- Response mappers -------------------------------------------------------


def _contact(raw: Any) -> ContactInfo | None:
    if not isinstance(raw, dict):
        return None
    return ContactInfo(
        value=_text(raw.get("value")),
        type=_text(raw.get("type")),
        is_primary=_flag(raw.get("isPrimary")),
    )


def _contacts(raw: Any) -> list[ContactInfo]:
    mapped = [_contact(item) for item in _as_dict_list(raw)]
    return [item for item in mapped if item is not None]


def _custom_fields(raw: Any) -> list[CustomFieldValue]:
    return [
        CustomFieldValue(
            id=_text(item.get("id")),
            title=_text(item.get("title")),
            is_private=_flag(item.get("isPrivate")),
            value_label=_text(item.get("valueLabel")),
            value=item.get("value"),
        )
        for item in _as_dict_list(raw)
    ]


def _file_handle(raw: Any) -> FileHandle | None:
    if not isinstance(raw, dict):
        return None
    return FileHandle(
        id=_text(raw.get("id")),
        name=_text(raw.get("name")),
        handle=_text(raw.get("handle")),
    )


def _file_handles(raw: Any) -> list[FileHandle]:
    mapped = [_file_handle(item) for item in _as_dict_list(raw)]
    return [item for item in mapped if item is not None]


def _user_summary(raw: Any) -> UserSummary | None:
    if not isinstance(raw, dict):
        return None
    return UserSummary(
        id=_text(raw.get("id")),
        first_name=_text(raw.get("firstName")),
        last_name=_text(raw.get("lastName")),
        email=_text(raw.get("email")),
        global_role=_text(raw.get("globalRole")),
        is_enabled=_flag(raw.get("isEnabled")),
        updated_at=_text(raw.get("updatedAt")),
        manager_id=_text(raw.get("managerId")),
    )


def _source(raw: Any) -> SourceSummary | None:
    if not isinstance(raw, dict):
        return None
    source_type = raw.get("sourceType")
    return SourceSummary(
        id=_text(raw.get("id")),
        title=_text(raw.get("title")),
        is_archived=_flag(raw.get("isArchived")),
        source_type=(
            SourceType(
                id=_text(source_type.get("id")),
                title=_text(source_type.get("title")),
                is_archived=_flag(source_type.get("isArchived")),
            )
            if isinstance(source_type, dict)
            else None
        ),
    )


def _tags(raw: Any) -> list[Tag]:
    return [
        Tag(
            id=_text(item.get("id")),
            title=_text(item.get("title")),
            is_archived=_flag(item.get("isArchived")),
        )
        for item in _as_dict_list(raw)
    ]


def _hiring_team(raw: Any) -> list[HiringTeamMember]:
    return [
        HiringTeamMember(
            user_id=_text(item.get("userId")),
            first_name=_text(item.get("firstName")),
            last_name=_text(item.get("lastName")),
            email=_text(item.get("email")),
            role=_text(item.get("role")),
        )
        for item in _as_dict_list(raw)
    ]


def _postal_address(raw: Any) -> PostalAddress | None:
    if not isinstance(raw, dict):
        return None
    return PostalAddress(
        address_country=_text(raw.get("addressCountry")),
        address_region=_text(raw.get("addressRegion")),
        address_locality=_text(raw.get("addressLocality")),
        postal_code=_text(raw.get("postalCode")),
        street_address=_text(raw.get("streetAddress")),
    )


def _candidate_fields(raw: Any) -> dict[str, Any]:
    """Map a raw candidate object onto ``Candidate`` keyword arguments."""
    data = _as_dict(raw)
    social_links = _as_dict_list(data.get("socialLinks"))
    location = data.get("location")
    return {
        "id": _text(data.get("id")),
        "name": _text(data.get("name")),
        "primary_email_address": _contact(data.get("primaryEmailAddress")),
        "primary_phone_number": _contact(data.get("primaryPhoneNumber")),
        "email_addresses": _contacts(data.get("emailAddresses")),
        "phone_numbers": _contacts(data.get("phoneNumbers")),
        "social_links": [
            SocialLink(type=_text(link.get("type")), url=_text(link.get("url")))
            for link in social_links
        ],
        "linkedin_url": next(
            (_text(link.get("url")) for link in social_links if link.get("type") == "LinkedIn"),
            None,
        ),
        "github_url": next(
            (_text(link.get("url")) for link in social_links if link.get("type") == "GitHub"),
            None,
        ),
        "profile_url": _text(data.get("profileUrl")),
        "position": _text(data.get("position")),
        "company": _text(data.get("company")),
        "school": _text(data.get("school")),
        "timezone": _text(data.get("timezone")),
        "location": (
            CandidateLocation(
                id=_text(location.get("id")),
                location_summary=_text(location.get("locationSummary")),
                location_components=[
                    LocationComponent(type=_text(part.get("type")), name=_text(part.get("name")))
                    for part in _as_dict_list(location.get("locationComponents"))
                ],
            )
            if isinstance(location, dict)
            else None
        ),
        "tags": _tags(data.get("tags")),
        "application_ids": _text_list(data.get("applicationIds")),
        "custom_fields": _custom_fields(data.get("customFields")),
        "resume_file_handle": _file_handle(data.get("resumeFileHandle")),
        "file_handles": _file_handles(data.get("fileHandles")),
        "source": _source(data.get("source")),
        "credited_to_user": _user_summary(data.get("creditedToUser")),
        "fraud_status": _text(data.get("fraudStatus")),
        "created_at": _text(data.get("createdAt")),
        "updated_at": _text(data.get("updatedAt")),
    }


def _openings(raw: Any) -> list[Opening]:
    openings: list[Opening] = []
    for item in _as_dict_list(raw):
        version = item.get("latestVersion")
        openings.append(
            Opening(
                id=_text(item.get("id")),
                opened_at=_text(item.get("openedAt")),
                closed_at=_text(item.get("closedAt")),
                is_archived=_flag(item.get("isArchived")),
                archived_at=_text(item.get("archivedAt")),
                close_reason_id=_text(item.get("closeReasonId")),
                opening_state=_text(item.get("openingState")),
                latest_version=(
                    OpeningVersion(
                        id=_text(version.get("id")),
                        identifier=_text(version.get("identifier")),
                        description=_text(version.get("description")),
                        author_id=_text(version.get("authorId")),
                        created_at=_text(version.get("createdAt")),
                        team_id=_text(version.get("teamId")),
                        job_ids=_text_list(version.get("jobIds")),
                        target_hire_date=_text(version.get("targetHireDate")),
                        target_start_date=_text(version.get("targetStartDate")),
                        is_backfill=_flag(version.get("isBackfill")),
                        employment_type=_text(version.get("employmentType")),
                        location_ids=_text_list(version.get("locationIds")),
                        hiring_team=_hiring_team(version.get("hiringTeam")),
                        custom_fields=_custom_fields(version.get("customFields")),
                    )
                    if isinstance(version, dict)
                    else None
                ),
            )
        )
    return openings


def _job_fields(raw: Any) -> dict[str, Any]:
    """Map a raw job object onto ``Job`` keyword arguments."""
    data = _as_dict(raw)
    location = data.get("location")
    address = location.get("address") if isinstance(location, dict) else None
    postal = address.get("postalAddress") if isinstance(address, dict) else None
    compensation = data.get("compensation")
    return {
        "id": _text(data.get("id")),
        "title": _text(data.get("title")),
        "confidential": _flag(data.get("confidential")),
        "status": _text(data.get("status")),
        "employment_type": _text(data.get("employmentType")),
        "location_id": _text(data.get("locationId")),
        "department_id": _text(data.get("departmentId")),
        "default_interview_plan_id": _text(data.get("defaultInterviewPlanId")),
        "interview_plan_ids": _text_list(data.get("interviewPlanIds")),
        "custom_fields": _custom_fields(data.get("customFields")),
        "job_posting_ids": _text_list(data.get("jobPostingIds")),
        "custom_requisition_id": _text(data.get("customRequisitionId")),
        "brand_id": _text(data.get("brandId")),
        "hiring_team": _hiring_team(data.get("hiringTeam")),
        "author": _user_summary(data.get("author")),
        "created_at": _text(data.get("createdAt")),
        "updated_at": _text(data.get("updatedAt")),
        "opened_at": _text(data.get("openedAt")),
        "closed_at": _text(data.get("closedAt")),
        "location": (
            JobLocation(
                id=_text(location.get("id")),
                name=_text(location.get("name")),
                external_name=_text(location.get("externalName")),
                is_archived=_flag(location.get("isArchived")),
                is_remote=_flag(location.get("isRemote")),
                workplace_type=_text(location.get("workplaceType")),
                parent_location_id=_text(location.get("parentLocationId")),
                type=_text(location.get("type")),
                address=_postal_address(postal),
            )
            if isinstance(location, dict)
            else None
        ),
        "openings": _openings(data.get("openings")),
        "compensation": (
            JobCompensation(
                compensation_tiers=[
                    CompensationTier(
                        id=_text(tier.get("id")),
                        title=_text(tier.get("title")),
                        additional_information=_text(tier.get("additionalInformation")),
                        tier_summary=_text(tier.get("tierSummary")),
                    )
                    for tier in _as_dict_list(compensation.get("compensationTiers"))
                ]
            )
            if isinstance(compensation, dict)
            else None
        ),
    }


def _application_fields(raw: Any) -> dict[str, Any]:
    """Map a raw application object onto ``Application`` keyword arguments."""
    data = _as_dict(raw)
    candidate = _as_dict(data.get("candidate"))
    job = _as_dict(data.get("job"))
    stage = data.get("currentInterviewStage")
    archive_reason = data.get("archiveReason")
    return {
        "id": _text(data.get("id")),
        "created_at": _text(data.get("createdAt")),
        "updated_at": _text(data.get("updatedAt")),
        "status": _text(data.get("status")),
        "custom_fields": _custom_fields(data.get("customFields")),
        "candidate": CandidateSummary(
            id=_text(candidate.get("id")),
            name=_text(candidate.get("name")),
            primary_email_address=_contact(candidate.get("primaryEmailAddress")),
            primary_phone_number=_contact(candidate.get("primaryPhoneNumber")),
        ),
        "current_interview_stage": (
            InterviewStageSummary(
                id=_text(stage.get("id")),
                title=_text(stage.get("title")),
                type=_text(stage.get("type")),
                order_in_interview_plan=_whole(stage.get("orderInInterviewPlan")),
                interview_stage_group_id=_text(stage.get("interviewStageGroupId")),
                interview_plan_id=_text(stage.get("interviewPlanId")),
            )
            if isinstance(stage, dict)
            else None
        ),
        "source": _source(data.get("source")),
        "archive_reason": (
            ApplicationArchiveReason(
                id=_text(archive_reason.get("id")),
                text=_text(archive_reason.get("text")),
                reason_type=_text(archive_reason.get("reasonType")),
                is_archived=_flag(archive_reason.get("isArchived")),
                custom_fields=_custom_fields(archive_reason.get("customFields")),
            )
            if isinstance(archive_reason, dict)
            else None
        ),
        "archived_at": _text(data.get("archivedAt")),
        "job": ApplicationJobSummary(
            id=_text(job.get("id")),
            title=_text(job.get("title")),
            location_id=_text(job.get("locationId")),
            department_id=_text(job.get("departmentId")),
        ),
        "credited_to_user": _user_summary(data.get("creditedToUser")),
        "hiring_team": _hiring_team(data.get("hiringTeam")),
        "applied_via_job_posting_id": _text(data.get("appliedViaJobPostingId")),
        "submitter_client_ip": _text(data.get("submitterClientIp")),
        "submitter_user_agent": _text(data.get("submitterUserAgent")),
        "application_history": [
            ApplicationHistoryEntry(
                id=_text(entry.get("id")),
                stage_id=_text(entry.get("stageId")),
                stage_number=_whole(entry.get("stageNumber")),
                title=_text(entry.get("title")),
                entered_stage_at=_text(entry.get("enteredStageAt")),
                actor_id=_text(entry.get("actorId")),
            )
            for entry in _as_dict_list(data.get("applicationHistory"))
        ],
    }


def _note_fields(raw: Any) -> dict[str, Any]:
    """Map a raw note object onto ``Note`` keyword arguments."""
    data = _as_dict(raw)
    author = data.get("author")
    return {
        "id": _text(data.get("id")),
        "content": _text(data.get("content")),
        "is_private": _flag(data.get("isPrivate")),
        "author": (
            NoteAuthor(
                id=_text(author.get("id")),
                first_name=_text(author.get("firstName")),
                last_name=_text(author.get("lastName")),
                email=_text(author.get("email")),
            )
            if isinstance(author, dict)
            else None
        ),
        "created_at": _text(data.get("createdAt")),
    }


def _offer_fields(raw: Any) -> dict[str, Any]:
    """Map a raw offer object onto ``Offer`` keyword arguments."""
    data = _as_dict(raw)
    version = data.get("latestVersion")
    salary = version.get("salary") if isinstance(version, dict) else None
    return {
        "id": _text(data.get("id")),
        "decided_at": _text(data.get("decidedAt")),
        "application_id": _text(data.get("applicationId")),
        "acceptance_status": _text(data.get("acceptanceStatus")),
        "offer_status": _text(data.get("offerStatus")),
        "latest_version": (
            OfferVersion(
                id=_text(version.get("id")),
                start_date=_text(version.get("startDate")),
                salary=(
                    Salary(
                        currency_code=_text(salary.get("currencyCode")),
                        value=_number(salary.get("value")),
                    )
                    if isinstance(salary, dict)
                    else None
                ),
                created_at=_text(version.get("createdAt")),
                opening_id=_text(version.get("openingId")),
                custom_fields=_custom_fields(version.get("customFields")),
                file_handles=_file_handles(version.get("fileHandles")),
                author=_user_summary(version.get("author")),
                approval_status=_text(version.get("approvalStatus")),
            )
            if isinstance(version, dict)
            else None
        ),
    }


def _job_posting_location_ids(raw: Any) -> JobPostingLocationIds | None:
    if not isinstance(raw, dict):
        return None
    return JobPostingLocationIds(
        primary_location_id=_text(raw.get("primaryLocationId")),
        secondary_location_ids=_text_list(raw.get("secondaryLocationIds")),
    )


def _description_part(raw: Any) -> DescriptionPart | None:
    if not isinstance(raw, dict):
        return None
    return DescriptionPart(html=_text(raw.get("html")), plain=_text(raw.get("plain")))


def _job_posting_fields(raw: Any) -> dict[str, Any]:
    """Map a raw job posting object onto ``JobPosting`` keyword arguments."""
    data = _as_dict(raw)
    parts = data.get("descriptionParts")
    address = data.get("address")
    compensation = data.get("compensation")
    job = data.get("job")
    return {
        "id": _text(data.get("id")),
        "title": _text(data.get("title")),
        "description_plain": _text(data.get("descriptionPlain")),
        "description_html": _text(data.get("descriptionHtml")),
        "description_social": _text(data.get("descriptionSocial")),
        "description_parts": (
            DescriptionParts(
                description_opening=_description_part(parts.get("descriptionOpening")),
                description_body=_description_part(parts.get("descriptionBody")),
                description_closing=_description_part(parts.get("descriptionClosing")),
            )
            if isinstance(parts, dict)
            else None
        ),
        "department_name": _text(data.get("departmentName")),
        "team_name": _text(data.get("teamName")),
        "team_name_hierarchy": _text_list(data.get("teamNameHierarchy")),
        "job_id": _text(data.get("jobId")),
        "location_name": _text(data.get("locationName")),
        "location_ids": _job_posting_location_ids(data.get("locationIds")),
        "address": (
            JobPostingAddress(postal_address=_postal_address(address.get("postalAddress")))
            if isinstance(address, dict)
            else None
        ),
        "is_remote": _flag(data.get("isRemote")),
        "workplace_type": _text(data.get("workplaceType")),
        "employment_type": _text(data.get("employmentType")),
        "is_listed": _flag(data.get("isListed")),
        "suppress_description_opening": _flag(data.get("suppressDescriptionOpening")),
        "suppress_description_closing": _flag(data.get("suppressDescriptionClosing")),
        "published_date": _text(data.get("publishedDate")),
        "application_deadline": _text(data.get("applicationDeadline")),
        "external_link": _text(data.get("externalLink")),
        "apply_link": _text(data.get("applyLink")),
        "compensation": (
            JobPostingCompensation(
                compensation_tier_summary=_text(compensation.get("compensationTierSummary")),
                summary_components=[
                    CompensationSummaryComponent(
                        summary=_text(component.get("summary")),
                        compensation_type_label=_text(component.get("compensationTypeLabel")),
                        interval=_text(component.get("interval")),
                        currency_code=_text(component.get("currencyCode")),
                        min_value=_number(component.get("minValue")),
                        max_value=_number(component.get("maxValue")),
                    )
                    for component in _as_dict_list(compensation.get("summaryComponents"))
                ],
                should_display_compensation_on_job_board=_flag(
                    compensation.get("shouldDisplayCompensationOnJobBoard")
                ),
            )
            if isinstance(compensation, dict)
            else None
        ),
        "application_limit_callout_html": _text(data.get("applicationLimitCalloutHtml")),
        "updated_at": _text(data.get("updatedAt")),
        "job": job if isinstance(job, dict) else None,
    }


def _interview_schedules(raw: Any) -> list[InterviewSchedule]:
    schedules: list[InterviewSchedule] = []
    for item in _as_dict_list(raw):
        schedules.append(
            InterviewSchedule(
                id=_text(item.get("id")),
                status=_text(item.get("status")),
                application_id=_text(item.get("applicationId")),
                interview_stage_id=_text(item.get("interviewStageId")),
                scheduled_by=_user_summary(item.get("scheduledBy")),
                created_at=_text(item.get("createdAt")),
                updated_at=_text(item.get("updatedAt")),
                interview_events=[
                    InterviewEvent(
                        id=_text(event.get("id")),
                        interview_id=_text(event.get("interviewId")),
                        interview_schedule_id=_text(event.get("interviewScheduleId")),
                        interviewer_user_ids=_text_list(event.get("interviewerUserIds")),
                        created_at=_text(event.get("createdAt")),
                        updated_at=_text(event.get("updatedAt")),
                        start_time=_text(event.get("startTime")),
                        end_time=_text(event.get("endTime")),
                        feedback_link=_text(event.get("feedbackLink")),
                        location=_text(event.get("location")),
                        meeting_link=_text(event.get("meetingLink")),
                        has_submitted_feedback=_flag(event.get("hasSubmittedFeedback")),
                    )
                    for event in _as_dict_list(item.get("interviewEvents"))
                ],
            )
        )
    return schedules


def _pagination(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "more_data_available": _flag(data.get("moreDataAvailable")) or False,
        "next_cursor": _text(data.get("nextCursor")),
    }


# --- Input schemas (args_schema for each @tool) ----------------------------

_API_KEY_FIELD = "Ashby API key (provided by credential system)"
_CURSOR_FIELD = "Opaque pagination cursor from a previous response's next_cursor value"
_PER_PAGE_FIELD = "Number of results per page (default and max 100)"
_SYNC_TOKEN_FIELD = "Opaque token from a prior sync; returns only items changed since then"


class ListCandidatesInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    cursor: str | None = Field(default=None, description=_CURSOR_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    created_after: str | None = Field(
        default=None,
        description="Only return candidates created after this ISO 8601 timestamp",
    )


class GetCandidateInput(BaseModel):
    candidate_id: str = Field(description="The UUID of the candidate to fetch")
    api_key: str = Field(description=_API_KEY_FIELD)


class CreateCandidateInput(BaseModel):
    name: str = Field(description="The candidate's full name")
    api_key: str = Field(description=_API_KEY_FIELD)
    email: str | None = Field(default=None, description="Primary email address")
    phone_number: str | None = Field(default=None, description="Primary phone number")
    linkedin_url: str | None = Field(default=None, description="LinkedIn profile URL")
    github_url: str | None = Field(default=None, description="GitHub profile URL")
    website: str | None = Field(default=None, description="Personal website URL")
    source_id: str | None = Field(
        default=None, description="UUID of the source to attribute the candidate to"
    )
    credited_to_user_id: str | None = Field(
        default=None, description="UUID of the user credited with sourcing this candidate"
    )
    created_at: str | None = Field(
        default=None,
        description="Backdated ISO 8601 creation timestamp (defaults to now)",
    )
    alternate_email_addresses: list[str] | None = Field(
        default=None, description="Additional email addresses to add to the candidate"
    )


class UpdateCandidateInput(BaseModel):
    candidate_id: str = Field(description="The UUID of the candidate to update")
    api_key: str = Field(description=_API_KEY_FIELD)
    name: str | None = Field(default=None, description="Updated full name")
    email: str | None = Field(default=None, description="Updated primary email address")
    phone_number: str | None = Field(default=None, description="Updated primary phone number")
    linkedin_url: str | None = Field(default=None, description="LinkedIn profile URL")
    github_url: str | None = Field(default=None, description="GitHub profile URL")
    website_url: str | None = Field(default=None, description="Personal website URL")
    alternate_email: str | None = Field(
        default=None, description="An additional email address to add to the candidate"
    )
    source_id: str | None = Field(
        default=None, description="UUID of the source to attribute the candidate to"
    )
    credited_to_user_id: str | None = Field(
        default=None, description="UUID of the user credited with sourcing this candidate"
    )
    created_at: str | None = Field(
        default=None,
        description="Backdated ISO 8601 creation timestamp (only if originally backdated)",
    )
    send_notifications: bool | None = Field(
        default=None,
        description="Whether subscribed users are notified about the update (default true)",
    )
    social_links: list[dict[str, Any]] | None = Field(
        default=None,
        description=(
            'Social links to set, e.g. [{"type":"LinkedIn","url":"https://..."}]. '
            "Replaces existing social links."
        ),
    )


class SearchCandidatesInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    name: str | None = Field(default=None, description="Candidate name to search for")
    email: str | None = Field(default=None, description="Candidate email to search for")


class ListJobsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    cursor: str | None = Field(default=None, description=_CURSOR_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    status: str | None = Field(
        default=None, description="Filter by job status: Open, Closed, Archived, or Draft"
    )
    created_after: str | None = Field(
        default=None, description="Only return jobs created after this ISO 8601 timestamp"
    )
    opened_after: str | None = Field(
        default=None, description="Only return jobs opened after this ISO 8601 timestamp"
    )
    opened_before: str | None = Field(
        default=None, description="Only return jobs opened before this ISO 8601 timestamp"
    )
    closed_after: str | None = Field(
        default=None, description="Only return jobs closed after this ISO 8601 timestamp"
    )
    closed_before: str | None = Field(
        default=None, description="Only return jobs closed before this ISO 8601 timestamp"
    )


class GetJobInput(BaseModel):
    job_id: str = Field(description="The UUID of the job to fetch")
    api_key: str = Field(description=_API_KEY_FIELD)


class CreateNoteInput(BaseModel):
    candidate_id: str = Field(description="The UUID of the candidate to add the note to")
    note: str = Field(
        description=(
            "The note content. With note_type text/html these tags are supported: "
            "<b>, <i>, <u>, <a>, <ul>, <ol>, <li>, <code>, <pre>"
        )
    )
    api_key: str = Field(description=_API_KEY_FIELD)
    note_type: str | None = Field(
        default=None, description="Content type of the note: text/plain (default) or text/html"
    )
    send_notifications: bool | None = Field(
        default=None,
        description="Whether subscribed users are notified about the note (default false)",
    )
    is_private: bool | None = Field(
        default=None, description="Whether the note is private (author-visible only)"
    )
    created_at: str | None = Field(
        default=None, description="Backdated ISO 8601 creation timestamp (defaults to now)"
    )


class ListNotesInput(BaseModel):
    candidate_id: str = Field(description="The UUID of the candidate to list notes for")
    api_key: str = Field(description=_API_KEY_FIELD)
    cursor: str | None = Field(default=None, description=_CURSOR_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)


class ListApplicationsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    cursor: str | None = Field(default=None, description=_CURSOR_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    status: str | None = Field(
        default=None,
        description="Filter by application status: Active, Hired, Archived, or Lead",
    )
    job_id: str | None = Field(
        default=None, description="Filter applications by a specific job UUID"
    )
    created_after: str | None = Field(
        default=None, description="Only return applications created after this ISO 8601 timestamp"
    )


class GetApplicationInput(BaseModel):
    application_id: str = Field(description="The UUID of the application to fetch")
    api_key: str = Field(description=_API_KEY_FIELD)


class CreateApplicationInput(BaseModel):
    candidate_id: str = Field(description="The UUID of the candidate to consider for the job")
    job_id: str = Field(description="The UUID of the job to consider the candidate for")
    api_key: str = Field(description=_API_KEY_FIELD)
    interview_plan_id: str | None = Field(
        default=None, description="Interview plan UUID (defaults to the job's default plan)"
    )
    interview_stage_id: str | None = Field(
        default=None, description="Interview stage UUID (defaults to the first Lead stage)"
    )
    source_id: str | None = Field(
        default=None, description="UUID of the source to set on the application"
    )
    credited_to_user_id: str | None = Field(
        default=None, description="UUID of the user the application is credited to"
    )
    created_at: str | None = Field(
        default=None,
        description="ISO 8601 timestamp to set as the application creation date",
    )


class ChangeApplicationStageInput(BaseModel):
    application_id: str = Field(description="The UUID of the application to move")
    interview_stage_id: str = Field(description="The UUID of the interview stage to move to")
    api_key: str = Field(description=_API_KEY_FIELD)
    archive_reason_id: str | None = Field(
        default=None,
        description="Archive reason UUID; required when moving to an Archived stage",
    )


class AddCandidateTagInput(BaseModel):
    candidate_id: str = Field(description="The UUID of the candidate to add the tag to")
    tag_id: str = Field(description="The UUID of the tag to add")
    api_key: str = Field(description=_API_KEY_FIELD)


class RemoveCandidateTagInput(BaseModel):
    candidate_id: str = Field(description="The UUID of the candidate to remove the tag from")
    tag_id: str = Field(description="The UUID of the tag to remove")
    api_key: str = Field(description=_API_KEY_FIELD)


class ListOffersInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    cursor: str | None = Field(default=None, description=_CURSOR_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    created_after: str | None = Field(
        default=None, description="Only return offers created after this ISO 8601 timestamp"
    )
    sync_token: str | None = Field(default=None, description=_SYNC_TOKEN_FIELD)
    application_id: str | None = Field(
        default=None, description="Return only offers for the specified application UUID"
    )


class GetOfferInput(BaseModel):
    offer_id: str = Field(description="The UUID of the offer to fetch")
    api_key: str = Field(description=_API_KEY_FIELD)


class ListSourcesInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    include_archived: bool | None = Field(
        default=None, description="When true, includes archived sources (default false)"
    )


class ListCandidateTagsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    include_archived: bool | None = Field(
        default=None, description="When true, includes archived tags (default false)"
    )
    cursor: str | None = Field(default=None, description=_CURSOR_FIELD)
    sync_token: str | None = Field(default=None, description=_SYNC_TOKEN_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)


class ListArchiveReasonsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    include_archived: bool | None = Field(
        default=None, description="When true, includes archived archive reasons (default false)"
    )


class ListCustomFieldsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    cursor: str | None = Field(default=None, description=_CURSOR_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    sync_token: str | None = Field(default=None, description=_SYNC_TOKEN_FIELD)
    include_archived: bool | None = Field(
        default=None, description="When true, includes archived custom fields (default false)"
    )


class ListDepartmentsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    cursor: str | None = Field(default=None, description=_CURSOR_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    sync_token: str | None = Field(default=None, description=_SYNC_TOKEN_FIELD)
    include_archived: bool | None = Field(
        default=None, description="When true, includes archived departments (default false)"
    )


class ListLocationsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    cursor: str | None = Field(default=None, description=_CURSOR_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    sync_token: str | None = Field(default=None, description=_SYNC_TOKEN_FIELD)
    include_archived: bool | None = Field(
        default=None, description="When true, includes archived locations (default false)"
    )
    include_location_hierarchy: bool | None = Field(
        default=None,
        description="When true, includes location hierarchy components/regions (default false)",
    )


class ListJobPostingsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    location: str | None = Field(
        default=None, description="Filter by location name (case sensitive)"
    )
    department: str | None = Field(
        default=None, description="Filter by department name (case sensitive)"
    )
    listed_only: bool | None = Field(
        default=None,
        description="When true, only returns publicly listed job postings (default false)",
    )
    job_board_id: str | None = Field(
        default=None,
        description="Job board UUID to filter to; defaults to the primary external job board",
    )


class GetJobPostingInput(BaseModel):
    job_posting_id: str = Field(description="The UUID of the job posting to fetch")
    api_key: str = Field(description=_API_KEY_FIELD)
    job_board_id: str | None = Field(
        default=None,
        description="Job board UUID; defaults to the external job board when omitted",
    )
    expand_job: bool | None = Field(
        default=None, description="Whether to include the related job object in the response"
    )


class ListOpeningsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    cursor: str | None = Field(default=None, description=_CURSOR_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    created_after: str | None = Field(
        default=None, description="Only return openings created after this ISO 8601 timestamp"
    )


class ListUsersInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    cursor: str | None = Field(default=None, description=_CURSOR_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    include_deactivated: bool | None = Field(
        default=None, description="When true, includes deactivated users (default false)"
    )


class ListInterviewsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    application_id: str | None = Field(
        default=None, description="Only return interview schedules for this application UUID"
    )
    interview_stage_id: str | None = Field(
        default=None, description="Only return interview schedules for this interview stage UUID"
    )
    cursor: str | None = Field(default=None, description=_CURSOR_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    created_after: str | None = Field(
        default=None,
        description="Only return interview schedules created after this ISO 8601 timestamp",
    )


# --- @tool functions --------------------------------------------------------


@tool(args_schema=ListCandidatesInput)
@serialize_pydantic_return
async def list_candidates(
    api_key: str,
    cursor: str | None = None,
    per_page: int | None = None,
    created_after: str | None = None,
) -> ListCandidatesOutput:
    """List all candidates in an Ashby organization with cursor-based pagination."""
    if not api_key or not api_key.strip():
        return ListCandidatesOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if cursor:
        body["cursor"] = cursor
    if per_page:
        body["limit"] = per_page
    created_after_ms = _iso_to_ms(created_after)
    if created_after_ms is not None:
        body["createdAfter"] = created_after_ms

    data, error = await _call("candidate.list", api_key, body, "Failed to list candidates")
    if error is not None:
        return ListCandidatesOutput(success=False, error=error)

    return ListCandidatesOutput(
        success=True,
        candidates=[
            Candidate(**_candidate_fields(item)) for item in _as_dict_list(data.get("results"))
        ],
        **_pagination(data),
    )


@tool(args_schema=GetCandidateInput)
@serialize_pydantic_return
async def get_candidate(candidate_id: str, api_key: str) -> GetCandidateOutput:
    """Retrieve full details about a single candidate by their ID."""
    if not api_key or not api_key.strip():
        return GetCandidateOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"id": candidate_id.strip()}
    data, error = await _call("candidate.info", api_key, body, "Failed to get candidate")
    if error is not None:
        return GetCandidateOutput(success=False, error=error)

    return GetCandidateOutput(success=True, **_candidate_fields(data.get("results")))


@tool(args_schema=CreateCandidateInput)
@serialize_pydantic_return
async def create_candidate(
    name: str,
    api_key: str,
    email: str | None = None,
    phone_number: str | None = None,
    linkedin_url: str | None = None,
    github_url: str | None = None,
    website: str | None = None,
    source_id: str | None = None,
    credited_to_user_id: str | None = None,
    created_at: str | None = None,
    alternate_email_addresses: list[str] | None = None,
) -> CreateCandidateOutput:
    """Create a new candidate record in Ashby."""
    if not api_key or not api_key.strip():
        return CreateCandidateOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"name": name}
    if email:
        body["email"] = email
    if phone_number:
        body["phoneNumber"] = phone_number
    if linkedin_url:
        body["linkedInUrl"] = linkedin_url
    if github_url:
        body["githubUrl"] = github_url
    if website:
        body["website"] = website
    if source_id:
        body["sourceId"] = source_id.strip()
    if credited_to_user_id:
        body["creditedToUserId"] = credited_to_user_id.strip()
    if created_at:
        body["createdAt"] = created_at
    if alternate_email_addresses:
        body["alternateEmailAddresses"] = alternate_email_addresses

    data, error = await _call("candidate.create", api_key, body, "Failed to create candidate")
    if error is not None:
        return CreateCandidateOutput(success=False, error=error)

    return CreateCandidateOutput(success=True, **_candidate_fields(data.get("results")))


@tool(args_schema=UpdateCandidateInput)
@serialize_pydantic_return
async def update_candidate(
    candidate_id: str,
    api_key: str,
    name: str | None = None,
    email: str | None = None,
    phone_number: str | None = None,
    linkedin_url: str | None = None,
    github_url: str | None = None,
    website_url: str | None = None,
    alternate_email: str | None = None,
    source_id: str | None = None,
    credited_to_user_id: str | None = None,
    created_at: str | None = None,
    send_notifications: bool | None = None,
    social_links: list[dict[str, Any]] | None = None,
) -> UpdateCandidateOutput:
    """Update an existing candidate record. Only provided fields are changed."""
    if not api_key or not api_key.strip():
        return UpdateCandidateOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"candidateId": candidate_id.strip()}
    if name:
        body["name"] = name
    if email:
        body["email"] = email
    if phone_number:
        body["phoneNumber"] = phone_number
    if linkedin_url:
        body["linkedInUrl"] = linkedin_url
    if github_url:
        body["githubUrl"] = github_url
    if website_url:
        body["websiteUrl"] = website_url
    if alternate_email:
        body["alternateEmail"] = alternate_email
    if source_id:
        body["sourceId"] = source_id.strip()
    if credited_to_user_id:
        body["creditedToUserId"] = credited_to_user_id.strip()
    if created_at:
        body["createdAt"] = created_at
    if send_notifications is not None:
        body["sendNotifications"] = send_notifications
    if social_links:
        body["socialLinks"] = social_links

    data, error = await _call("candidate.update", api_key, body, "Failed to update candidate")
    if error is not None:
        return UpdateCandidateOutput(success=False, error=error)

    return UpdateCandidateOutput(success=True, **_candidate_fields(data.get("results")))


@tool(args_schema=SearchCandidatesInput)
@serialize_pydantic_return
async def search_candidates(
    api_key: str, name: str | None = None, email: str | None = None
) -> SearchCandidatesOutput:
    """Search candidates by name and/or email (AND logic, max 100 matches)."""
    if not api_key or not api_key.strip():
        return SearchCandidatesOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if name:
        body["name"] = name
    if email:
        body["email"] = email

    data, error = await _call("candidate.search", api_key, body, "Failed to search candidates")
    if error is not None:
        return SearchCandidatesOutput(success=False, error=error)

    return SearchCandidatesOutput(
        success=True,
        candidates=[
            Candidate(**_candidate_fields(item)) for item in _as_dict_list(data.get("results"))
        ],
    )


@tool(args_schema=ListJobsInput)
@serialize_pydantic_return
async def list_jobs(
    api_key: str,
    cursor: str | None = None,
    per_page: int | None = None,
    status: str | None = None,
    created_after: str | None = None,
    opened_after: str | None = None,
    opened_before: str | None = None,
    closed_after: str | None = None,
    closed_before: str | None = None,
) -> ListJobsOutput:
    """List jobs in an Ashby organization (Open, Closed and Archived by default)."""
    if not api_key or not api_key.strip():
        return ListJobsOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"expand": ["openings", "location"]}
    if cursor:
        body["cursor"] = cursor
    if per_page:
        body["limit"] = per_page
    if status:
        body["status"] = [status]
    for key, value in (
        ("createdAfter", created_after),
        ("openedAfter", opened_after),
        ("openedBefore", opened_before),
        ("closedAfter", closed_after),
        ("closedBefore", closed_before),
    ):
        milliseconds = _iso_to_ms(value)
        if milliseconds is not None:
            body[key] = milliseconds

    data, error = await _call("job.list", api_key, body, "Failed to list jobs")
    if error is not None:
        return ListJobsOutput(success=False, error=error)

    return ListJobsOutput(
        success=True,
        jobs=[Job(**_job_fields(item)) for item in _as_dict_list(data.get("results"))],
        **_pagination(data),
    )


@tool(args_schema=GetJobInput)
@serialize_pydantic_return
async def get_job(job_id: str, api_key: str) -> GetJobOutput:
    """Retrieve full details about a single job by its ID."""
    if not api_key or not api_key.strip():
        return GetJobOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {
        "id": job_id.strip(),
        "expand": ["openings", "location", "compensation"],
    }
    data, error = await _call("job.info", api_key, body, "Failed to get job")
    if error is not None:
        return GetJobOutput(success=False, error=error)

    return GetJobOutput(success=True, **_job_fields(data.get("results")))


@tool(args_schema=CreateNoteInput)
@serialize_pydantic_return
async def create_note(
    candidate_id: str,
    note: str,
    api_key: str,
    note_type: str | None = None,
    send_notifications: bool | None = None,
    is_private: bool | None = None,
    created_at: str | None = None,
) -> CreateNoteOutput:
    """Create a note on a candidate. Supports plain text and HTML content."""
    if not api_key or not api_key.strip():
        return CreateNoteOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {
        "candidateId": candidate_id.strip(),
        "sendNotifications": bool(send_notifications),
    }
    if note_type == "text/html":
        body["note"] = {"type": "text/html", "value": note}
    else:
        body["note"] = note
    if is_private is not None:
        body["isPrivate"] = is_private
    if created_at:
        body["createdAt"] = created_at

    data, error = await _call("candidate.createNote", api_key, body, "Failed to create note")
    if error is not None:
        return CreateNoteOutput(success=False, error=error)

    return CreateNoteOutput(success=True, **_note_fields(data.get("results")))


@tool(args_schema=ListNotesInput)
@serialize_pydantic_return
async def list_notes(
    candidate_id: str,
    api_key: str,
    cursor: str | None = None,
    per_page: int | None = None,
) -> ListNotesOutput:
    """List all notes on a candidate with cursor-based pagination."""
    if not api_key or not api_key.strip():
        return ListNotesOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"candidateId": candidate_id.strip()}
    if cursor:
        body["cursor"] = cursor
    if per_page:
        body["limit"] = per_page

    data, error = await _call("candidate.listNotes", api_key, body, "Failed to list notes")
    if error is not None:
        return ListNotesOutput(success=False, error=error)

    return ListNotesOutput(
        success=True,
        notes=[Note(**_note_fields(item)) for item in _as_dict_list(data.get("results"))],
        **_pagination(data),
    )


@tool(args_schema=ListApplicationsInput)
@serialize_pydantic_return
async def list_applications(
    api_key: str,
    cursor: str | None = None,
    per_page: int | None = None,
    status: str | None = None,
    job_id: str | None = None,
    created_after: str | None = None,
) -> ListApplicationsOutput:
    """List applications with pagination and optional status/job/date filters."""
    if not api_key or not api_key.strip():
        return ListApplicationsOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if cursor:
        body["cursor"] = cursor
    if per_page:
        body["limit"] = per_page
    if status:
        body["status"] = status
    if job_id:
        body["jobId"] = job_id.strip()
    created_after_ms = _iso_to_ms(created_after)
    if created_after_ms is not None:
        body["createdAfter"] = created_after_ms

    data, error = await _call("application.list", api_key, body, "Failed to list applications")
    if error is not None:
        return ListApplicationsOutput(success=False, error=error)

    return ListApplicationsOutput(
        success=True,
        applications=[
            Application(**_application_fields(item))
            for item in _as_dict_list(data.get("results"))
        ],
        **_pagination(data),
    )


@tool(args_schema=GetApplicationInput)
@serialize_pydantic_return
async def get_application(application_id: str, api_key: str) -> GetApplicationOutput:
    """Retrieve full details about a single application by its ID."""
    if not api_key or not api_key.strip():
        return GetApplicationOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"applicationId": application_id.strip()}
    data, error = await _call("application.info", api_key, body, "Failed to get application")
    if error is not None:
        return GetApplicationOutput(success=False, error=error)

    return GetApplicationOutput(success=True, **_application_fields(data.get("results")))


@tool(args_schema=CreateApplicationInput)
@serialize_pydantic_return
async def create_application(
    candidate_id: str,
    job_id: str,
    api_key: str,
    interview_plan_id: str | None = None,
    interview_stage_id: str | None = None,
    source_id: str | None = None,
    credited_to_user_id: str | None = None,
    created_at: str | None = None,
) -> CreateApplicationOutput:
    """Create a new application for a candidate on a job."""
    if not api_key or not api_key.strip():
        return CreateApplicationOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {
        "candidateId": candidate_id.strip(),
        "jobId": job_id.strip(),
    }
    if interview_plan_id:
        body["interviewPlanId"] = interview_plan_id.strip()
    if interview_stage_id:
        body["interviewStageId"] = interview_stage_id.strip()
    if source_id:
        body["sourceId"] = source_id.strip()
    if credited_to_user_id:
        body["creditedToUserId"] = credited_to_user_id.strip()
    if created_at:
        body["createdAt"] = created_at

    data, error = await _call("application.create", api_key, body, "Failed to create application")
    if error is not None:
        return CreateApplicationOutput(success=False, error=error)

    return CreateApplicationOutput(success=True, **_application_fields(data.get("results")))


@tool(args_schema=ChangeApplicationStageInput)
@serialize_pydantic_return
async def change_application_stage(
    application_id: str,
    interview_stage_id: str,
    api_key: str,
    archive_reason_id: str | None = None,
) -> ChangeApplicationStageOutput:
    """Move an application to a different interview stage."""
    if not api_key or not api_key.strip():
        return ChangeApplicationStageOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {
        "applicationId": application_id.strip(),
        "interviewStageId": interview_stage_id.strip(),
    }
    if archive_reason_id:
        body["archiveReasonId"] = archive_reason_id.strip()

    data, error = await _call(
        "application.changeStage", api_key, body, "Failed to change application stage"
    )
    if error is not None:
        return ChangeApplicationStageOutput(success=False, error=error)

    return ChangeApplicationStageOutput(success=True, **_application_fields(data.get("results")))


@tool(args_schema=AddCandidateTagInput)
@serialize_pydantic_return
async def add_candidate_tag(
    candidate_id: str, tag_id: str, api_key: str
) -> AddCandidateTagOutput:
    """Add a tag to a candidate and return the updated candidate."""
    if not api_key or not api_key.strip():
        return AddCandidateTagOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"candidateId": candidate_id.strip(), "tagId": tag_id.strip()}
    data, error = await _call(
        "candidate.addTag", api_key, body, "Failed to add tag to candidate"
    )
    if error is not None:
        return AddCandidateTagOutput(success=False, error=error)

    return AddCandidateTagOutput(success=True, **_candidate_fields(data.get("results")))


@tool(args_schema=RemoveCandidateTagInput)
@serialize_pydantic_return
async def remove_candidate_tag(
    candidate_id: str, tag_id: str, api_key: str
) -> RemoveCandidateTagOutput:
    """Remove a tag from a candidate and return the updated candidate."""
    if not api_key or not api_key.strip():
        return RemoveCandidateTagOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"candidateId": candidate_id.strip(), "tagId": tag_id.strip()}
    data, error = await _call(
        "candidate.removeTag", api_key, body, "Failed to remove tag from candidate"
    )
    if error is not None:
        return RemoveCandidateTagOutput(success=False, error=error)

    return RemoveCandidateTagOutput(success=True, **_candidate_fields(data.get("results")))


@tool(args_schema=ListOffersInput)
@serialize_pydantic_return
async def list_offers(
    api_key: str,
    cursor: str | None = None,
    per_page: int | None = None,
    created_after: str | None = None,
    sync_token: str | None = None,
    application_id: str | None = None,
) -> ListOffersOutput:
    """List offers with their latest version."""
    if not api_key or not api_key.strip():
        return ListOffersOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if cursor:
        body["cursor"] = cursor
    if per_page:
        body["limit"] = per_page
    created_after_ms = _iso_to_ms(created_after)
    if created_after_ms is not None:
        body["createdAfter"] = created_after_ms
    if sync_token:
        body["syncToken"] = sync_token
    if application_id:
        body["applicationId"] = application_id.strip()

    data, error = await _call("offer.list", api_key, body, "Failed to list offers")
    if error is not None:
        return ListOffersOutput(success=False, error=error)

    return ListOffersOutput(
        success=True,
        offers=[Offer(**_offer_fields(item)) for item in _as_dict_list(data.get("results"))],
        **_pagination(data),
    )


@tool(args_schema=GetOfferInput)
@serialize_pydantic_return
async def get_offer(offer_id: str, api_key: str) -> GetOfferOutput:
    """Retrieve full details about a single offer by its ID."""
    if not api_key or not api_key.strip():
        return GetOfferOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"offerId": offer_id.strip()}
    data, error = await _call("offer.info", api_key, body, "Failed to get offer")
    if error is not None:
        return GetOfferOutput(success=False, error=error)

    return GetOfferOutput(success=True, **_offer_fields(data.get("results")))


@tool(args_schema=ListSourcesInput)
@serialize_pydantic_return
async def list_sources(
    api_key: str, include_archived: bool | None = None
) -> ListSourcesOutput:
    """List all candidate sources configured in Ashby."""
    if not api_key or not api_key.strip():
        return ListSourcesOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if include_archived is not None:
        body["includeArchived"] = include_archived

    data, error = await _call("source.list", api_key, body, "Failed to list sources")
    if error is not None:
        return ListSourcesOutput(success=False, error=error)

    sources = [_source(item) for item in _as_dict_list(data.get("results"))]
    return ListSourcesOutput(
        success=True, sources=[item for item in sources if item is not None]
    )


@tool(args_schema=ListCandidateTagsInput)
@serialize_pydantic_return
async def list_candidate_tags(
    api_key: str,
    include_archived: bool | None = None,
    cursor: str | None = None,
    sync_token: str | None = None,
    per_page: int | None = None,
) -> ListCandidateTagsOutput:
    """List all candidate tags configured in Ashby."""
    if not api_key or not api_key.strip():
        return ListCandidateTagsOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if include_archived is not None:
        body["includeArchived"] = include_archived
    if cursor:
        body["cursor"] = cursor
    if sync_token:
        body["syncToken"] = sync_token
    if per_page:
        body["limit"] = per_page

    data, error = await _call("candidateTag.list", api_key, body, "Failed to list candidate tags")
    if error is not None:
        return ListCandidateTagsOutput(success=False, error=error)

    return ListCandidateTagsOutput(
        success=True,
        tags=_tags(data.get("results")),
        sync_token=_text(data.get("syncToken")),
        **_pagination(data),
    )


@tool(args_schema=ListArchiveReasonsInput)
@serialize_pydantic_return
async def list_archive_reasons(
    api_key: str, include_archived: bool | None = None
) -> ListArchiveReasonsOutput:
    """List all archive reasons configured in Ashby."""
    if not api_key or not api_key.strip():
        return ListArchiveReasonsOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if include_archived is not None:
        body["includeArchived"] = include_archived

    data, error = await _call(
        "archiveReason.list", api_key, body, "Failed to list archive reasons"
    )
    if error is not None:
        return ListArchiveReasonsOutput(success=False, error=error)

    return ListArchiveReasonsOutput(
        success=True,
        archive_reasons=[
            ArchiveReason(
                id=_text(item.get("id")),
                text=_text(item.get("text")),
                reason_type=_text(item.get("reasonType")),
                is_archived=_flag(item.get("isArchived")),
            )
            for item in _as_dict_list(data.get("results"))
        ],
    )


@tool(args_schema=ListCustomFieldsInput)
@serialize_pydantic_return
async def list_custom_fields(
    api_key: str,
    cursor: str | None = None,
    per_page: int | None = None,
    sync_token: str | None = None,
    include_archived: bool | None = None,
) -> ListCustomFieldsOutput:
    """List all custom field definitions configured in Ashby."""
    if not api_key or not api_key.strip():
        return ListCustomFieldsOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if cursor:
        body["cursor"] = cursor
    if per_page:
        body["limit"] = per_page
    if sync_token:
        body["syncToken"] = sync_token
    if include_archived is not None:
        body["includeArchived"] = include_archived

    data, error = await _call("customField.list", api_key, body, "Failed to list custom fields")
    if error is not None:
        return ListCustomFieldsOutput(success=False, error=error)

    return ListCustomFieldsOutput(
        success=True,
        custom_fields=[
            CustomFieldDefinition(
                id=_text(item.get("id")),
                title=_text(item.get("title")),
                is_private=_flag(item.get("isPrivate")),
                field_type=_text(item.get("fieldType")),
                object_type=_text(item.get("objectType")),
                is_archived=_flag(item.get("isArchived")),
                is_required=_flag(item.get("isRequired")),
                selectable_values=[
                    CustomFieldSelectableValue(
                        label=_text(value.get("label")),
                        value=_text(value.get("value")),
                        is_archived=_flag(value.get("isArchived")),
                    )
                    for value in _as_dict_list(item.get("selectableValues"))
                ],
            )
            for item in _as_dict_list(data.get("results"))
        ],
        sync_token=_text(data.get("syncToken")),
        **_pagination(data),
    )


@tool(args_schema=ListDepartmentsInput)
@serialize_pydantic_return
async def list_departments(
    api_key: str,
    cursor: str | None = None,
    per_page: int | None = None,
    sync_token: str | None = None,
    include_archived: bool | None = None,
) -> ListDepartmentsOutput:
    """List all departments in Ashby."""
    if not api_key or not api_key.strip():
        return ListDepartmentsOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if cursor:
        body["cursor"] = cursor
    if per_page:
        body["limit"] = per_page
    if sync_token:
        body["syncToken"] = sync_token
    if include_archived is not None:
        body["includeArchived"] = include_archived

    data, error = await _call("department.list", api_key, body, "Failed to list departments")
    if error is not None:
        return ListDepartmentsOutput(success=False, error=error)

    return ListDepartmentsOutput(
        success=True,
        departments=[
            Department(
                id=_text(item.get("id")),
                name=_text(item.get("name")),
                external_name=_text(item.get("externalName")),
                is_archived=_flag(item.get("isArchived")),
                parent_id=_text(item.get("parentId")),
                created_at=_text(item.get("createdAt")),
                updated_at=_text(item.get("updatedAt")),
                extra_data=(
                    item.get("extraData") if isinstance(item.get("extraData"), dict) else None
                ),
            )
            for item in _as_dict_list(data.get("results"))
        ],
        sync_token=_text(data.get("syncToken")),
        **_pagination(data),
    )


@tool(args_schema=ListLocationsInput)
@serialize_pydantic_return
async def list_locations(
    api_key: str,
    cursor: str | None = None,
    per_page: int | None = None,
    sync_token: str | None = None,
    include_archived: bool | None = None,
    include_location_hierarchy: bool | None = None,
) -> ListLocationsOutput:
    """List all locations configured in Ashby."""
    if not api_key or not api_key.strip():
        return ListLocationsOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if cursor:
        body["cursor"] = cursor
    if per_page:
        body["limit"] = per_page
    if sync_token:
        body["syncToken"] = sync_token
    if include_archived is not None:
        body["includeArchived"] = include_archived
    if include_location_hierarchy is not None:
        body["includeLocationHierarchy"] = include_location_hierarchy

    data, error = await _call("location.list", api_key, body, "Failed to list locations")
    if error is not None:
        return ListLocationsOutput(success=False, error=error)

    locations: list[Location] = []
    for item in _as_dict_list(data.get("results")):
        address = item.get("address")
        postal = address.get("postalAddress") if isinstance(address, dict) else None
        locations.append(
            Location(
                id=_text(item.get("id")),
                name=_text(item.get("name")),
                external_name=_text(item.get("externalName")),
                is_archived=_flag(item.get("isArchived")),
                is_remote=_flag(item.get("isRemote")),
                workplace_type=_text(item.get("workplaceType")),
                parent_location_id=_text(item.get("parentLocationId")),
                type=_text(item.get("type")),
                address=_postal_address(postal),
                extra_data=(
                    item.get("extraData") if isinstance(item.get("extraData"), dict) else None
                ),
            )
        )

    return ListLocationsOutput(
        success=True,
        locations=locations,
        sync_token=_text(data.get("syncToken")),
        **_pagination(data),
    )


@tool(args_schema=ListJobPostingsInput)
@serialize_pydantic_return
async def list_job_postings(
    api_key: str,
    location: str | None = None,
    department: str | None = None,
    listed_only: bool | None = None,
    job_board_id: str | None = None,
) -> ListJobPostingsOutput:
    """List job postings on a job board."""
    if not api_key or not api_key.strip():
        return ListJobPostingsOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if location:
        body["location"] = location
    if department:
        body["department"] = department
    if listed_only is not None:
        body["listedOnly"] = listed_only
    if job_board_id:
        body["jobBoardId"] = job_board_id.strip()

    data, error = await _call("jobPosting.list", api_key, body, "Failed to list job postings")
    if error is not None:
        return ListJobPostingsOutput(success=False, error=error)

    return ListJobPostingsOutput(
        success=True,
        job_postings=[
            JobPostingSummary(
                id=_text(item.get("id")),
                title=_text(item.get("title")),
                job_id=_text(item.get("jobId")),
                department_name=_text(item.get("departmentName")),
                team_name=_text(item.get("teamName")),
                location_name=_text(item.get("locationName")),
                location_ids=_job_posting_location_ids(item.get("locationIds")),
                workplace_type=_text(item.get("workplaceType")),
                employment_type=_text(item.get("employmentType")),
                is_listed=_flag(item.get("isListed")),
                published_date=_text(item.get("publishedDate")),
                application_deadline=_text(item.get("applicationDeadline")),
                external_link=_text(item.get("externalLink")),
                apply_link=_text(item.get("applyLink")),
                compensation_tier_summary=_text(item.get("compensationTierSummary")),
                should_display_compensation_on_job_board=_flag(
                    item.get("shouldDisplayCompensationOnJobBoard")
                ),
                updated_at=_text(item.get("updatedAt")),
            )
            for item in _as_dict_list(data.get("results"))
        ],
    )


@tool(args_schema=GetJobPostingInput)
@serialize_pydantic_return
async def get_job_posting(
    job_posting_id: str,
    api_key: str,
    job_board_id: str | None = None,
    expand_job: bool | None = None,
) -> GetJobPostingOutput:
    """Retrieve full details about a single job posting by its ID."""
    if not api_key or not api_key.strip():
        return GetJobPostingOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"jobPostingId": job_posting_id.strip()}
    if job_board_id:
        body["jobBoardId"] = job_board_id.strip()
    if expand_job:
        body["expand"] = ["job"]

    data, error = await _call("jobPosting.info", api_key, body, "Failed to get job posting")
    if error is not None:
        return GetJobPostingOutput(success=False, error=error)

    return GetJobPostingOutput(success=True, **_job_posting_fields(data.get("results")))


@tool(args_schema=ListOpeningsInput)
@serialize_pydantic_return
async def list_openings(
    api_key: str,
    cursor: str | None = None,
    per_page: int | None = None,
    created_after: str | None = None,
) -> ListOpeningsOutput:
    """List headcount openings in Ashby with cursor-based pagination."""
    if not api_key or not api_key.strip():
        return ListOpeningsOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if cursor:
        body["cursor"] = cursor
    if per_page:
        body["limit"] = per_page
    created_after_ms = _iso_to_ms(created_after)
    if created_after_ms is not None:
        body["createdAfter"] = created_after_ms

    data, error = await _call("opening.list", api_key, body, "Failed to list openings")
    if error is not None:
        return ListOpeningsOutput(success=False, error=error)

    return ListOpeningsOutput(
        success=True, openings=_openings(data.get("results")), **_pagination(data)
    )


@tool(args_schema=ListUsersInput)
@serialize_pydantic_return
async def list_users(
    api_key: str,
    cursor: str | None = None,
    per_page: int | None = None,
    include_deactivated: bool | None = None,
) -> ListUsersOutput:
    """List users in the Ashby organization with cursor-based pagination."""
    if not api_key or not api_key.strip():
        return ListUsersOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if cursor:
        body["cursor"] = cursor
    if per_page:
        body["limit"] = per_page
    if include_deactivated is not None:
        body["includeDeactivated"] = include_deactivated

    data, error = await _call("user.list", api_key, body, "Failed to list users")
    if error is not None:
        return ListUsersOutput(success=False, error=error)

    users = [_user_summary(item) for item in _as_dict_list(data.get("results"))]
    return ListUsersOutput(
        success=True,
        users=[item for item in users if item is not None],
        **_pagination(data),
    )


@tool(args_schema=ListInterviewsInput)
@serialize_pydantic_return
async def list_interviews(
    api_key: str,
    application_id: str | None = None,
    interview_stage_id: str | None = None,
    cursor: str | None = None,
    per_page: int | None = None,
    created_after: str | None = None,
) -> ListInterviewsOutput:
    """List interview schedules, optionally filtered by application or stage."""
    if not api_key or not api_key.strip():
        return ListInterviewsOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if application_id:
        body["applicationId"] = application_id.strip()
    if interview_stage_id:
        body["interviewStageId"] = interview_stage_id.strip()
    if cursor:
        body["cursor"] = cursor
    if per_page:
        body["limit"] = per_page
    created_after_ms = _iso_to_ms(created_after)
    if created_after_ms is not None:
        body["createdAfter"] = created_after_ms

    data, error = await _call(
        "interviewSchedule.list", api_key, body, "Failed to list interview schedules"
    )
    if error is not None:
        return ListInterviewsOutput(success=False, error=error)

    return ListInterviewsOutput(
        success=True,
        interview_schedules=_interview_schedules(data.get("results")),
        **_pagination(data),
    )
