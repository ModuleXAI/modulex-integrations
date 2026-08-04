"""Greenhouse LangChain ``@tool`` functions.

Eleven async read tools over the Greenhouse **Harvest API**
(``https://harvest.greenhouse.io/v1``). The calling convention is the
modulex *api_key* one: the ``ToolExecutor`` injects an ``api_key: str``
directly (resolved from the user's ``api_key`` credential), not an
``auth_type``/``auth_data`` pair.

Transport notes that shape every function below:

* Auth is **HTTP Basic with the API key as the username and an empty
  password**, i.e. ``Authorization: Basic <base64("<key>:")>``.
  Unauthenticated requests answer 401; a key that lacks the per-endpoint
  permission answers 403.
* Greenhouse runs several separate APIs (Harvest, Job Board, Onboarding,
  Ingestion) on different hosts with different credentials. Every action
  here targets **Harvest only**, and the host is a module-level constant
  — no action parameter ever reaches the netloc. Path ids are
  percent-encoded with ``quote(..., safe="")`` before interpolation.
* ``On-Behalf-Of`` (a Greenhouse user id) is required for ``POST``,
  ``PATCH`` and ``DELETE`` requests. All eleven actions are ``GET``
  reads, so no action sends it.
* List endpoints answer with a **top-level JSON array** and paginate
  through the RFC 5988 ``Link`` response header, not a body cursor.
  ``page``/``per_page`` are passed straight through and the ``Link``
  header's ``rel="next"`` page number is surfaced as ``next_page`` —
  a single call is always a single bounded request.

Error model: every call is wrapped in try/except and returns the typed
output with ``success=False`` + ``error`` for non-2xx responses,
unexpected response shapes, timeouts and unexpected exceptions rather
than raising. Nothing between ``response.json()`` and the ``return`` may
raise: the payload shape is checked explicitly and every field is routed
through a scalar coercer, so a wrong-typed attribute degrades to ``None``
instead of surfacing a ``ValidationError`` past the ``@tool`` boundary.
"""
from __future__ import annotations

import base64
import re
from typing import Any
from urllib.parse import parse_qs, quote, urlsplit

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.greenhouse.outputs import (
    Answer,
    ApplicationLocation,
    ApplicationSummary,
    Attachment,
    CandidateSummary,
    Department,
    DepartmentRef,
    Education,
    Employment,
    GetApplicationOutput,
    GetCandidateOutput,
    GetJobOutput,
    GetUserOutput,
    HiringTeam,
    HiringTeamMember,
    Interview,
    InterviewKit,
    InterviewKitQuestion,
    JobStage,
    JobSummary,
    ListApplicationsOutput,
    ListCandidatesOutput,
    ListDepartmentsOutput,
    ListJobsOutput,
    ListJobStagesOutput,
    ListOfficesOutput,
    ListUsersOutput,
    NamedRef,
    Office,
    OfficeLocation,
    OfficeRef,
    Opening,
    RejectionReason,
    Source,
    TypedValue,
    User,
    UserRef,
)

__all__ = [
    "get_application",
    "get_candidate",
    "get_job",
    "get_user",
    "list_applications",
    "list_candidates",
    "list_departments",
    "list_job_stages",
    "list_jobs",
    "list_offices",
    "list_users",
]

_HARVEST_API_BASE = "https://harvest.greenhouse.io/v1"
_TIMEOUT = 30.0
_EMPTY_KEY_ERROR = (
    "Greenhouse API key is empty. Please configure a valid Greenhouse credential."
)
_SHAPE_ERROR = "The Greenhouse API returned an unexpected response shape."


# --- Auth + transport helpers ----------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    """Harvest Basic auth: API key as username, empty password."""
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }


# ``rel=next`` entry of an RFC 5988 Link header, e.g.
# ``<https://harvest.greenhouse.io/v1/candidates?page=2&per_page=2>; rel="next"``
_LINK_NEXT_RE = re.compile(r'<([^>]*)>\s*;\s*[^,]*rel\s*=\s*"?next"?', re.IGNORECASE)


def _next_page(link_header: str | None) -> int | None:
    """Page number of the ``Link`` header's ``rel="next"`` entry, if any.

    Harvest paginates with ``Link`` headers rather than a body cursor.
    ``None`` means the response was the last page (or the header was
    absent/unparseable) — callers must not loop blindly.
    """
    if not link_header:
        return None
    match = _LINK_NEXT_RE.search(link_header)
    if match is None:
        return None
    try:
        query = parse_qs(urlsplit(match.group(1)).query)
    except ValueError:
        return None
    values = query.get("page")
    if not values:
        return None
    page = values[0]
    return int(page) if page.isdigit() else None


async def _call(
    path: str, api_key: str, params: dict[str, Any], failure: str
) -> tuple[Any, int | None, str | None]:
    """GET a Harvest endpoint and return ``(payload, next_page, error)``.

    ``path`` is assembled from module-level constants plus ids that the
    caller has already percent-encoded, so the host can never be
    influenced by an action parameter.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_HARVEST_API_BASE}/{path}", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return None, None, f"Greenhouse API error ({response.status_code}): {response.text}"
        payload = response.json()
        next_page = _next_page(response.headers.get("link"))
    except httpx.TimeoutException:
        return None, None, "Request to the Greenhouse API timed out."
    except Exception as exc:
        return None, None, f"{failure}: {exc}"
    return payload, next_page, None


def _path_id(value: str) -> str:
    """Percent-encode a path id so it cannot escape its URL segment."""
    return quote(value.strip(), safe="")


def _page_params(per_page: int | None, page: int | None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if per_page:
        params["per_page"] = per_page
    if page:
        params["page"] = page
    return params


def _add(params: dict[str, Any], **values: str | None) -> None:
    """Append the non-empty query filters to ``params``."""
    for key, value in values.items():
        if value:
            params[key] = value


# --- Scalar coercers --------------------------------------------------------
#
# Greenhouse fields are permissive: an attribute can be null, and a custom or
# externally-synced value can arrive with an unexpected type. Coercing here
# (rather than at each call site) is what keeps a wrong-typed attribute from
# raising a pydantic ValidationError after the try/except has been left.


def _as_str(value: Any) -> str | None:
    if value is None or isinstance(value, (dict, list, bool)):
        return None
    return value if isinstance(value, str) else str(value)


def _as_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _as_int_list(value: Any) -> list[int]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, int) and not isinstance(item, bool)]


def _object(payload: Any) -> dict[str, Any] | None:
    """A retrieve endpoint must answer with a JSON object."""
    return payload if isinstance(payload, dict) else None


def _array(payload: Any) -> list[Any] | None:
    """A list endpoint must answer with a top-level JSON array."""
    return payload if isinstance(payload, list) else None


# --- Response mappers -------------------------------------------------------


def _parse_named_ref(raw: Any) -> NamedRef | None:
    if not isinstance(raw, dict):
        return None
    return NamedRef(id=_as_int(raw.get("id")), name=_as_str(raw.get("name")))


def _parse_named_refs(raw: Any) -> list[NamedRef]:
    return [
        NamedRef(id=_as_int(item.get("id")), name=_as_str(item.get("name")))
        for item in _as_dict_list(raw)
    ]


def _parse_typed_values(raw: Any) -> list[TypedValue]:
    return [
        TypedValue(value=_as_str(item.get("value")), type=_as_str(item.get("type")))
        for item in _as_dict_list(raw)
    ]


def _parse_user_ref(raw: Any) -> UserRef | None:
    if not isinstance(raw, dict):
        return None
    return UserRef(
        id=_as_int(raw.get("id")),
        first_name=_as_str(raw.get("first_name")),
        last_name=_as_str(raw.get("last_name")),
        name=_as_str(raw.get("name")),
        employee_id=_as_str(raw.get("employee_id")),
    )


def _parse_user_refs(raw: Any) -> list[UserRef]:
    mapped = [_parse_user_ref(item) for item in _as_dict_list(raw)]
    return [item for item in mapped if item is not None]


def _parse_team_members(raw: Any) -> list[HiringTeamMember]:
    return [
        HiringTeamMember(
            id=_as_int(item.get("id")),
            first_name=_as_str(item.get("first_name")),
            last_name=_as_str(item.get("last_name")),
            name=_as_str(item.get("name")),
            employee_id=_as_str(item.get("employee_id")),
            responsible=_as_bool(item.get("responsible")),
        )
        for item in _as_dict_list(raw)
    ]


def _parse_hiring_team(raw: Any) -> HiringTeam:
    data = _as_dict(raw)
    return HiringTeam(
        hiring_managers=_parse_team_members(data.get("hiring_managers")),
        recruiters=_parse_team_members(data.get("recruiters")),
        coordinators=_parse_team_members(data.get("coordinators")),
        sourcers=_parse_team_members(data.get("sourcers")),
    )


def _parse_attachments(raw: Any) -> list[Attachment]:
    return [
        Attachment(
            filename=_as_str(item.get("filename")),
            url=_as_str(item.get("url")),
            type=_as_str(item.get("type")),
            created_at=_as_str(item.get("created_at")),
        )
        for item in _as_dict_list(raw)
    ]


def _parse_educations(raw: Any) -> list[Education]:
    return [
        Education(
            id=_as_int(item.get("id")),
            school_name=_as_str(item.get("school_name")),
            degree=_as_str(item.get("degree")),
            discipline=_as_str(item.get("discipline")),
            start_date=_as_str(item.get("start_date")),
            end_date=_as_str(item.get("end_date")),
        )
        for item in _as_dict_list(raw)
    ]


def _parse_employments(raw: Any) -> list[Employment]:
    return [
        Employment(
            id=_as_int(item.get("id")),
            company_name=_as_str(item.get("company_name")),
            title=_as_str(item.get("title")),
            start_date=_as_str(item.get("start_date")),
            end_date=_as_str(item.get("end_date")),
        )
        for item in _as_dict_list(raw)
    ]


def _parse_office_location(raw: Any) -> OfficeLocation | None:
    if not isinstance(raw, dict):
        return None
    return OfficeLocation(name=_as_str(raw.get("name")))


def _parse_department_refs(raw: Any) -> list[DepartmentRef]:
    return [
        DepartmentRef(
            id=_as_int(item.get("id")),
            name=_as_str(item.get("name")),
            parent_id=_as_int(item.get("parent_id")),
        )
        for item in _as_dict_list(raw)
    ]


def _parse_office_refs(raw: Any) -> list[OfficeRef]:
    return [
        OfficeRef(
            id=_as_int(item.get("id")),
            name=_as_str(item.get("name")),
            location=_parse_office_location(item.get("location")),
        )
        for item in _as_dict_list(raw)
    ]


def _parse_openings(raw: Any) -> list[Opening]:
    return [
        Opening(
            id=_as_int(item.get("id")),
            opening_id=_as_str(item.get("opening_id")),
            status=_as_str(item.get("status")),
            opened_at=_as_str(item.get("opened_at")),
            closed_at=_as_str(item.get("closed_at")),
            application_id=_as_int(item.get("application_id")),
            close_reason=_parse_named_ref(item.get("close_reason")),
        )
        for item in _as_dict_list(raw)
    ]


def _parse_source(raw: Any) -> Source | None:
    if not isinstance(raw, dict):
        return None
    return Source(id=_as_int(raw.get("id")), public_name=_as_str(raw.get("public_name")))


def _parse_rejection_reason(raw: Any) -> RejectionReason | None:
    if not isinstance(raw, dict):
        return None
    return RejectionReason(
        id=_as_int(raw.get("id")),
        name=_as_str(raw.get("name")),
        type=_parse_named_ref(raw.get("type")),
    )


def _parse_application_location(raw: Any) -> ApplicationLocation | None:
    if not isinstance(raw, dict):
        return None
    return ApplicationLocation(address=_as_str(raw.get("address")))


def _parse_answers(raw: Any) -> list[Answer]:
    return [
        Answer(question=_as_str(item.get("question")), answer=_as_str(item.get("answer")))
        for item in _as_dict_list(raw)
    ]


def _parse_candidate_summary(raw: dict[str, Any]) -> CandidateSummary:
    return CandidateSummary(
        id=_as_int(raw.get("id")),
        first_name=_as_str(raw.get("first_name")),
        last_name=_as_str(raw.get("last_name")),
        company=_as_str(raw.get("company")),
        title=_as_str(raw.get("title")),
        is_private=_as_bool(raw.get("is_private")),
        can_email=_as_bool(raw.get("can_email")),
        email_addresses=_parse_typed_values(raw.get("email_addresses")),
        tags=_as_str_list(raw.get("tags")),
        application_ids=_as_int_list(raw.get("application_ids")),
        created_at=_as_str(raw.get("created_at")),
        updated_at=_as_str(raw.get("updated_at")),
        last_activity=_as_str(raw.get("last_activity")),
    )


def _candidate_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a raw candidate object onto ``GetCandidateOutput`` keywords."""
    return {
        "id": _as_int(raw.get("id")),
        "first_name": _as_str(raw.get("first_name")),
        "last_name": _as_str(raw.get("last_name")),
        "company": _as_str(raw.get("company")),
        "title": _as_str(raw.get("title")),
        "is_private": _as_bool(raw.get("is_private")),
        "can_email": _as_bool(raw.get("can_email")),
        "created_at": _as_str(raw.get("created_at")),
        "updated_at": _as_str(raw.get("updated_at")),
        "last_activity": _as_str(raw.get("last_activity")),
        "email_addresses": _parse_typed_values(raw.get("email_addresses")),
        "phone_numbers": _parse_typed_values(raw.get("phone_numbers")),
        "addresses": _parse_typed_values(raw.get("addresses")),
        "website_addresses": _parse_typed_values(raw.get("website_addresses")),
        "social_media_addresses": _parse_typed_values(raw.get("social_media_addresses")),
        "tags": _as_str_list(raw.get("tags")),
        "application_ids": _as_int_list(raw.get("application_ids")),
        "recruiter": _parse_user_ref(raw.get("recruiter")),
        "coordinator": _parse_user_ref(raw.get("coordinator")),
        "attachments": _parse_attachments(raw.get("attachments")),
        "educations": _parse_educations(raw.get("educations")),
        "employments": _parse_employments(raw.get("employments")),
        "custom_fields": _as_dict(raw.get("custom_fields")),
    }


def _parse_job_summary(raw: dict[str, Any]) -> JobSummary:
    return JobSummary(
        id=_as_int(raw.get("id")),
        name=_as_str(raw.get("name")),
        status=_as_str(raw.get("status")),
        confidential=_as_bool(raw.get("confidential")),
        departments=_parse_department_refs(raw.get("departments")),
        offices=_parse_office_refs(raw.get("offices")),
        opened_at=_as_str(raw.get("opened_at")),
        closed_at=_as_str(raw.get("closed_at")),
        created_at=_as_str(raw.get("created_at")),
        updated_at=_as_str(raw.get("updated_at")),
    )


def _job_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a raw job object onto ``GetJobOutput`` keywords."""
    return {
        "id": _as_int(raw.get("id")),
        "name": _as_str(raw.get("name")),
        "requisition_id": _as_str(raw.get("requisition_id")),
        "status": _as_str(raw.get("status")),
        "confidential": _as_bool(raw.get("confidential")),
        "created_at": _as_str(raw.get("created_at")),
        "opened_at": _as_str(raw.get("opened_at")),
        "closed_at": _as_str(raw.get("closed_at")),
        "updated_at": _as_str(raw.get("updated_at")),
        "is_template": _as_bool(raw.get("is_template")),
        "notes": _as_str(raw.get("notes")),
        "departments": _parse_department_refs(raw.get("departments")),
        "offices": _parse_office_refs(raw.get("offices")),
        "hiring_team": _parse_hiring_team(raw.get("hiring_team")),
        "openings": _parse_openings(raw.get("openings")),
        "custom_fields": _as_dict(raw.get("custom_fields")),
    }


def _parse_application_summary(raw: dict[str, Any]) -> ApplicationSummary:
    return ApplicationSummary(
        id=_as_int(raw.get("id")),
        candidate_id=_as_int(raw.get("candidate_id")),
        prospect=_as_bool(raw.get("prospect")),
        status=_as_str(raw.get("status")),
        current_stage=_parse_named_ref(raw.get("current_stage")),
        jobs=_parse_named_refs(raw.get("jobs")),
        applied_at=_as_str(raw.get("applied_at")),
        rejected_at=_as_str(raw.get("rejected_at")),
        last_activity_at=_as_str(raw.get("last_activity_at")),
    )


def _application_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a raw application object onto ``GetApplicationOutput`` keywords."""
    return {
        "id": _as_int(raw.get("id")),
        "candidate_id": _as_int(raw.get("candidate_id")),
        "prospect": _as_bool(raw.get("prospect")),
        "status": _as_str(raw.get("status")),
        "applied_at": _as_str(raw.get("applied_at")),
        "rejected_at": _as_str(raw.get("rejected_at")),
        "last_activity_at": _as_str(raw.get("last_activity_at")),
        "location": _parse_application_location(raw.get("location")),
        "source": _parse_source(raw.get("source")),
        "credited_to": _parse_user_ref(raw.get("credited_to")),
        "recruiter": _parse_user_ref(raw.get("recruiter")),
        "coordinator": _parse_user_ref(raw.get("coordinator")),
        "current_stage": _parse_named_ref(raw.get("current_stage")),
        "rejection_reason": _parse_rejection_reason(raw.get("rejection_reason")),
        "jobs": _parse_named_refs(raw.get("jobs")),
        "job_post_id": _as_int(raw.get("job_post_id")),
        "answers": _parse_answers(raw.get("answers")),
        "attachments": _parse_attachments(raw.get("attachments")),
        "custom_fields": _as_dict(raw.get("custom_fields")),
    }


def _user_fields(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a raw user object onto ``User``/``GetUserOutput`` keywords."""
    return {
        "id": _as_int(raw.get("id")),
        "name": _as_str(raw.get("name")),
        "first_name": _as_str(raw.get("first_name")),
        "last_name": _as_str(raw.get("last_name")),
        "primary_email_address": _as_str(raw.get("primary_email_address")),
        "disabled": _as_bool(raw.get("disabled")),
        "site_admin": _as_bool(raw.get("site_admin")),
        "emails": _as_str_list(raw.get("emails")),
        "employee_id": _as_str(raw.get("employee_id")),
        "linked_candidate_ids": _as_int_list(raw.get("linked_candidate_ids")),
        "created_at": _as_str(raw.get("created_at")),
        "updated_at": _as_str(raw.get("updated_at")),
    }


def _parse_department(raw: dict[str, Any]) -> Department:
    return Department(
        id=_as_int(raw.get("id")),
        name=_as_str(raw.get("name")),
        parent_id=_as_int(raw.get("parent_id")),
        child_ids=_as_int_list(raw.get("child_ids")),
        external_id=_as_str(raw.get("external_id")),
    )


def _parse_office(raw: dict[str, Any]) -> Office:
    return Office(
        id=_as_int(raw.get("id")),
        name=_as_str(raw.get("name")),
        location=_parse_office_location(raw.get("location")),
        primary_contact_user_id=_as_int(raw.get("primary_contact_user_id")),
        parent_id=_as_int(raw.get("parent_id")),
        child_ids=_as_int_list(raw.get("child_ids")),
        external_id=_as_str(raw.get("external_id")),
    )


def _parse_interview_kit(raw: Any) -> InterviewKit | None:
    if not isinstance(raw, dict):
        return None
    return InterviewKit(
        id=_as_int(raw.get("id")),
        content=_as_str(raw.get("content")),
        questions=[
            InterviewKitQuestion(
                id=_as_int(item.get("id")), question=_as_str(item.get("question"))
            )
            for item in _as_dict_list(raw.get("questions"))
        ],
    )


def _parse_interviews(raw: Any) -> list[Interview]:
    return [
        Interview(
            id=_as_int(item.get("id")),
            name=_as_str(item.get("name")),
            schedulable=_as_bool(item.get("schedulable")),
            estimated_minutes=_as_int(item.get("estimated_minutes")),
            default_interviewer_users=_parse_user_refs(item.get("default_interviewer_users")),
            interview_kit=_parse_interview_kit(item.get("interview_kit")),
        )
        for item in _as_dict_list(raw)
    ]


def _parse_job_stage(raw: dict[str, Any]) -> JobStage:
    return JobStage(
        id=_as_int(raw.get("id")),
        name=_as_str(raw.get("name")),
        created_at=_as_str(raw.get("created_at")),
        updated_at=_as_str(raw.get("updated_at")),
        job_id=_as_int(raw.get("job_id")),
        priority=_as_int(raw.get("priority")),
        active=_as_bool(raw.get("active")),
        interviews=_parse_interviews(raw.get("interviews")),
    )


# --- Input schemas (args_schema for each @tool) ----------------------------

_API_KEY_FIELD = "Greenhouse Harvest API key (provided by credential system)"
_PER_PAGE_FIELD = "Number of results per page, between 1 and 500 (default 100)"
_PAGE_FIELD = "Page number to return; combine with next_page from a previous response"
_CREATED_AFTER = "Return only records created at or after this ISO 8601 timestamp"
_CREATED_BEFORE = "Return only records created before this ISO 8601 timestamp"
_UPDATED_AFTER = "Return only records updated at or after this ISO 8601 timestamp"
_UPDATED_BEFORE = "Return only records updated before this ISO 8601 timestamp"


class ListCandidatesInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    page: int | None = Field(default=None, description=_PAGE_FIELD)
    created_after: str | None = Field(default=None, description=_CREATED_AFTER)
    created_before: str | None = Field(default=None, description=_CREATED_BEFORE)
    updated_after: str | None = Field(default=None, description=_UPDATED_AFTER)
    updated_before: str | None = Field(default=None, description=_UPDATED_BEFORE)
    job_id: str | None = Field(
        default=None,
        description="Only return candidates who applied to this job id (prospects excluded)",
    )
    email: str | None = Field(
        default=None, description="Only return candidates with this email address"
    )
    candidate_ids: str | None = Field(
        default=None,
        description=(
            'Comma-separated candidate ids to fetch, e.g. "123,456" (max 50; '
            "ignored when email is also supplied)"
        ),
    )


class GetCandidateInput(BaseModel):
    candidate_id: str = Field(description="The id of the candidate to retrieve")
    api_key: str = Field(description=_API_KEY_FIELD)


class ListJobsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    page: int | None = Field(default=None, description=_PAGE_FIELD)
    status: str | None = Field(
        default=None, description="Filter by job status: open, closed or draft"
    )
    created_after: str | None = Field(default=None, description=_CREATED_AFTER)
    created_before: str | None = Field(default=None, description=_CREATED_BEFORE)
    updated_after: str | None = Field(default=None, description=_UPDATED_AFTER)
    updated_before: str | None = Field(default=None, description=_UPDATED_BEFORE)
    department_id: str | None = Field(
        default=None, description="Only return jobs in this department id"
    )
    office_id: str | None = Field(default=None, description="Only return jobs in this office id")


class GetJobInput(BaseModel):
    job_id: str = Field(description="The id of the job to retrieve")
    api_key: str = Field(description=_API_KEY_FIELD)


class ListApplicationsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    page: int | None = Field(default=None, description=_PAGE_FIELD)
    job_id: str | None = Field(
        default=None, description="Only return applications that involve this job id"
    )
    status: str | None = Field(
        default=None,
        description="Filter by application status: active, converted, hired or rejected",
    )
    created_after: str | None = Field(default=None, description=_CREATED_AFTER)
    created_before: str | None = Field(default=None, description=_CREATED_BEFORE)
    last_activity_after: str | None = Field(
        default=None,
        description="Only return applications whose last activity is at or after this timestamp",
    )


class GetApplicationInput(BaseModel):
    application_id: str = Field(description="The id of the application to retrieve")
    api_key: str = Field(description=_API_KEY_FIELD)


class ListUsersInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    page: int | None = Field(default=None, description=_PAGE_FIELD)
    created_after: str | None = Field(default=None, description=_CREATED_AFTER)
    created_before: str | None = Field(default=None, description=_CREATED_BEFORE)
    updated_after: str | None = Field(default=None, description=_UPDATED_AFTER)
    updated_before: str | None = Field(default=None, description=_UPDATED_BEFORE)
    email: str | None = Field(
        default=None,
        description="Return the user with this address as a primary or secondary email",
    )


class GetUserInput(BaseModel):
    user_id: str = Field(description="The id of the user to retrieve")
    api_key: str = Field(description=_API_KEY_FIELD)


class ListDepartmentsInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    page: int | None = Field(default=None, description=_PAGE_FIELD)


class ListOfficesInput(BaseModel):
    api_key: str = Field(description=_API_KEY_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    page: int | None = Field(default=None, description=_PAGE_FIELD)


class ListJobStagesInput(BaseModel):
    job_id: str = Field(description="The id of the job whose interview stages to list")
    api_key: str = Field(description=_API_KEY_FIELD)
    per_page: int | None = Field(default=None, description=_PER_PAGE_FIELD)
    page: int | None = Field(default=None, description=_PAGE_FIELD)


# --- @tool functions --------------------------------------------------------


@tool(args_schema=ListCandidatesInput)
@serialize_pydantic_return
async def list_candidates(
    api_key: str,
    per_page: int | None = None,
    page: int | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    job_id: str | None = None,
    email: str | None = None,
    candidate_ids: str | None = None,
) -> ListCandidatesOutput:
    """List candidates with optional date, job, email or id filters."""
    if not api_key or not api_key.strip():
        return ListCandidatesOutput(success=False, error=_EMPTY_KEY_ERROR)

    params = _page_params(per_page, page)
    _add(
        params,
        created_after=created_after,
        created_before=created_before,
        updated_after=updated_after,
        updated_before=updated_before,
        job_id=job_id,
        email=email,
        candidate_ids=candidate_ids,
    )

    payload, next_page, error = await _call(
        "candidates", api_key, params, "Failed to list candidates"
    )
    if error is not None:
        return ListCandidatesOutput(success=False, error=error)
    items = _array(payload)
    if items is None:
        return ListCandidatesOutput(success=False, error=_SHAPE_ERROR)

    candidates = [_parse_candidate_summary(item) for item in _as_dict_list(items)]
    return ListCandidatesOutput(
        success=True, candidates=candidates, count=len(candidates), next_page=next_page
    )


@tool(args_schema=GetCandidateInput)
@serialize_pydantic_return
async def get_candidate(candidate_id: str, api_key: str) -> GetCandidateOutput:
    """Retrieve one candidate with contact details, education and employment."""
    if not api_key or not api_key.strip():
        return GetCandidateOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not candidate_id or not candidate_id.strip():
        return GetCandidateOutput(success=False, error="candidate_id is required.")

    payload, _, error = await _call(
        f"candidates/{_path_id(candidate_id)}", api_key, {}, "Failed to get candidate"
    )
    if error is not None:
        return GetCandidateOutput(success=False, error=error)
    data = _object(payload)
    if data is None:
        return GetCandidateOutput(success=False, error=_SHAPE_ERROR)

    return GetCandidateOutput(success=True, **_candidate_fields(data))


@tool(args_schema=ListJobsInput)
@serialize_pydantic_return
async def list_jobs(
    api_key: str,
    per_page: int | None = None,
    page: int | None = None,
    status: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    department_id: str | None = None,
    office_id: str | None = None,
) -> ListJobsOutput:
    """List jobs with optional status, department, office or date filters."""
    if not api_key or not api_key.strip():
        return ListJobsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params = _page_params(per_page, page)
    _add(
        params,
        status=status,
        created_after=created_after,
        created_before=created_before,
        updated_after=updated_after,
        updated_before=updated_before,
        department_id=department_id,
        office_id=office_id,
    )

    payload, next_page, error = await _call("jobs", api_key, params, "Failed to list jobs")
    if error is not None:
        return ListJobsOutput(success=False, error=error)
    items = _array(payload)
    if items is None:
        return ListJobsOutput(success=False, error=_SHAPE_ERROR)

    jobs = [_parse_job_summary(item) for item in _as_dict_list(items)]
    return ListJobsOutput(success=True, jobs=jobs, count=len(jobs), next_page=next_page)


@tool(args_schema=GetJobInput)
@serialize_pydantic_return
async def get_job(job_id: str, api_key: str) -> GetJobOutput:
    """Retrieve one job with its hiring team, openings and custom fields."""
    if not api_key or not api_key.strip():
        return GetJobOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not job_id or not job_id.strip():
        return GetJobOutput(success=False, error="job_id is required.")

    payload, _, error = await _call(
        f"jobs/{_path_id(job_id)}", api_key, {}, "Failed to get job"
    )
    if error is not None:
        return GetJobOutput(success=False, error=error)
    data = _object(payload)
    if data is None:
        return GetJobOutput(success=False, error=_SHAPE_ERROR)

    return GetJobOutput(success=True, **_job_fields(data))


@tool(args_schema=ListApplicationsInput)
@serialize_pydantic_return
async def list_applications(
    api_key: str,
    per_page: int | None = None,
    page: int | None = None,
    job_id: str | None = None,
    status: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    last_activity_after: str | None = None,
) -> ListApplicationsOutput:
    """List applications with optional job, status or date filters."""
    if not api_key or not api_key.strip():
        return ListApplicationsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params = _page_params(per_page, page)
    _add(
        params,
        job_id=job_id,
        status=status,
        created_after=created_after,
        created_before=created_before,
        last_activity_after=last_activity_after,
    )

    payload, next_page, error = await _call(
        "applications", api_key, params, "Failed to list applications"
    )
    if error is not None:
        return ListApplicationsOutput(success=False, error=error)
    items = _array(payload)
    if items is None:
        return ListApplicationsOutput(success=False, error=_SHAPE_ERROR)

    applications = [_parse_application_summary(item) for item in _as_dict_list(items)]
    return ListApplicationsOutput(
        success=True, applications=applications, count=len(applications), next_page=next_page
    )


@tool(args_schema=GetApplicationInput)
@serialize_pydantic_return
async def get_application(application_id: str, api_key: str) -> GetApplicationOutput:
    """Retrieve one application with its source, stage, answers and attachments."""
    if not api_key or not api_key.strip():
        return GetApplicationOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not application_id or not application_id.strip():
        return GetApplicationOutput(success=False, error="application_id is required.")

    payload, _, error = await _call(
        f"applications/{_path_id(application_id)}", api_key, {}, "Failed to get application"
    )
    if error is not None:
        return GetApplicationOutput(success=False, error=error)
    data = _object(payload)
    if data is None:
        return GetApplicationOutput(success=False, error=_SHAPE_ERROR)

    return GetApplicationOutput(success=True, **_application_fields(data))


@tool(args_schema=ListUsersInput)
@serialize_pydantic_return
async def list_users(
    api_key: str,
    per_page: int | None = None,
    page: int | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    email: str | None = None,
) -> ListUsersOutput:
    """List Greenhouse users (recruiters, coordinators, hiring managers, admins)."""
    if not api_key or not api_key.strip():
        return ListUsersOutput(success=False, error=_EMPTY_KEY_ERROR)

    params = _page_params(per_page, page)
    _add(
        params,
        created_after=created_after,
        created_before=created_before,
        updated_after=updated_after,
        updated_before=updated_before,
        email=email,
    )

    payload, next_page, error = await _call("users", api_key, params, "Failed to list users")
    if error is not None:
        return ListUsersOutput(success=False, error=error)
    items = _array(payload)
    if items is None:
        return ListUsersOutput(success=False, error=_SHAPE_ERROR)

    users = [User(**_user_fields(item)) for item in _as_dict_list(items)]
    return ListUsersOutput(success=True, users=users, count=len(users), next_page=next_page)


@tool(args_schema=GetUserInput)
@serialize_pydantic_return
async def get_user(user_id: str, api_key: str) -> GetUserOutput:
    """Retrieve one Greenhouse user by id."""
    if not api_key or not api_key.strip():
        return GetUserOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not user_id or not user_id.strip():
        return GetUserOutput(success=False, error="user_id is required.")

    payload, _, error = await _call(
        f"users/{_path_id(user_id)}", api_key, {}, "Failed to get user"
    )
    if error is not None:
        return GetUserOutput(success=False, error=error)
    data = _object(payload)
    if data is None:
        return GetUserOutput(success=False, error=_SHAPE_ERROR)

    return GetUserOutput(success=True, **_user_fields(data))


@tool(args_schema=ListDepartmentsInput)
@serialize_pydantic_return
async def list_departments(
    api_key: str, per_page: int | None = None, page: int | None = None
) -> ListDepartmentsOutput:
    """List all departments configured in the organization."""
    if not api_key or not api_key.strip():
        return ListDepartmentsOutput(success=False, error=_EMPTY_KEY_ERROR)

    payload, next_page, error = await _call(
        "departments", api_key, _page_params(per_page, page), "Failed to list departments"
    )
    if error is not None:
        return ListDepartmentsOutput(success=False, error=error)
    items = _array(payload)
    if items is None:
        return ListDepartmentsOutput(success=False, error=_SHAPE_ERROR)

    departments = [_parse_department(item) for item in _as_dict_list(items)]
    return ListDepartmentsOutput(
        success=True, departments=departments, count=len(departments), next_page=next_page
    )


@tool(args_schema=ListOfficesInput)
@serialize_pydantic_return
async def list_offices(
    api_key: str, per_page: int | None = None, page: int | None = None
) -> ListOfficesOutput:
    """List all offices configured in the organization."""
    if not api_key or not api_key.strip():
        return ListOfficesOutput(success=False, error=_EMPTY_KEY_ERROR)

    payload, next_page, error = await _call(
        "offices", api_key, _page_params(per_page, page), "Failed to list offices"
    )
    if error is not None:
        return ListOfficesOutput(success=False, error=error)
    items = _array(payload)
    if items is None:
        return ListOfficesOutput(success=False, error=_SHAPE_ERROR)

    offices = [_parse_office(item) for item in _as_dict_list(items)]
    return ListOfficesOutput(
        success=True, offices=offices, count=len(offices), next_page=next_page
    )


@tool(args_schema=ListJobStagesInput)
@serialize_pydantic_return
async def list_job_stages(
    job_id: str, api_key: str, per_page: int | None = None, page: int | None = None
) -> ListJobStagesOutput:
    """List the interview stages configured on a specific job."""
    if not api_key or not api_key.strip():
        return ListJobStagesOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not job_id or not job_id.strip():
        return ListJobStagesOutput(success=False, error="job_id is required.")

    payload, next_page, error = await _call(
        f"jobs/{_path_id(job_id)}/stages",
        api_key,
        _page_params(per_page, page),
        "Failed to list job stages",
    )
    if error is not None:
        return ListJobStagesOutput(success=False, error=error)
    items = _array(payload)
    if items is None:
        return ListJobStagesOutput(success=False, error=_SHAPE_ERROR)

    stages = [_parse_job_stage(item) for item in _as_dict_list(items)]
    return ListJobStagesOutput(
        success=True, stages=stages, count=len(stages), next_page=next_page
    )
