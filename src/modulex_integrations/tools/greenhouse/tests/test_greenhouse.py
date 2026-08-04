"""Happy-path tests per action plus failure-path, shape-confusion,
type-confusion, path-encoding and empty-credential tests.

Harvest list endpoints answer with a top-level JSON array and paginate
through the RFC 5988 ``Link`` header, so both the array shape and the
header parsing are exercised. The hand-built Basic auth header is
checked byte for byte against ``httpx.BasicAuth``.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx
import pytest

from modulex_integrations.tools.greenhouse import (
    TOOLS,
    get_application,
    get_candidate,
    get_job,
    get_user,
    list_applications,
    list_candidates,
    list_departments,
    list_job_stages,
    list_jobs,
    list_offices,
    list_users,
    manifest,
)
from modulex_integrations.tools.greenhouse.outputs import (
    GetApplicationOutput,
    GetCandidateOutput,
    GetJobOutput,
    GetUserOutput,
    ListApplicationsOutput,
    ListCandidatesOutput,
    ListDepartmentsOutput,
    ListJobsOutput,
    ListJobStagesOutput,
    ListOfficesOutput,
    ListUsersOutput,
)
from modulex_integrations.tools.greenhouse.tools import _headers, _next_page

API = "https://harvest.greenhouse.io/v1"
_API_KEY = "fake-api-key"
_EXPECTED_BASIC = "Basic " + base64.b64encode(f"{_API_KEY}:".encode()).decode()

_USER_REF: dict[str, Any] = {
    "id": 92120,
    "first_name": "Greenhouse",
    "last_name": "Admin",
    "name": "Greenhouse Admin",
    "employee_id": "67890",
}

_CANDIDATE_RAW: dict[str, Any] = {
    "id": 53883394,
    "first_name": "John",
    "last_name": "Locke",
    "company": "The Tustin Box Company",
    "title": "Customer Success Representative",
    "created_at": "2017-08-15T03:31:46.591Z",
    "updated_at": "2017-09-28T12:29:30.497Z",
    "last_activity": "2017-09-28T12:29:30.481Z",
    "is_private": False,
    "can_email": True,
    "email_addresses": [{"value": "test@work.com", "type": "work"}],
    "phone_numbers": [{"value": "555-555-5555", "type": "mobile"}],
    "addresses": [{"value": "123 City Street", "type": "home"}],
    "website_addresses": [{"value": "mysite.com", "type": "personal"}],
    "social_media_addresses": [{"value": "twitter.com/test"}],
    "tags": ["Python", "Ruby"],
    "application_ids": [69102626, 65153308],
    "recruiter": _USER_REF,
    "coordinator": {
        "id": 453636,
        "first_name": "Jane",
        "last_name": "Smith",
        "name": "Jane Smith",
        "employee_id": "12345",
    },
    "attachments": [
        {
            "filename": "John_Locke_Offer_Packet.pdf",
            "url": "https://prod-heroku.s3.amazonaws.com/offer.pdf",
            "type": "offer_packet",
            "created_at": "2020-09-27T18:45:27.137Z",
        }
    ],
    "educations": [
        {
            "id": 561227,
            "school_name": "University of Michigan - Ann Arbor",
            "degree": "Bachelor's Degree",
            "discipline": "Computer Science",
            "start_date": "2012-08-15T00:00:00.000Z",
            "end_date": "2016-05-15T00:00:00.000Z",
        }
    ],
    "employments": [
        {
            "id": 8485064,
            "company_name": "Greenhouse",
            "title": "Engineer",
            "start_date": "2012-08-15T00:00:00.000Z",
            "end_date": "2016-05-15T00:00:00.000Z",
        }
    ],
    "custom_fields": {"desired_salary": "1000000000", "work_remotely": True},
}

_JOB_RAW: dict[str, Any] = {
    "id": 6404,
    "name": "Archaeologist",
    "requisition_id": "abc123",
    "notes": "<p>Resistance to electro-magnetic radiation a plus!</p>",
    "confidential": False,
    "status": "closed",
    "created_at": "2013-12-10T14:42:58Z",
    "opened_at": "2013-12-11T14:42:58Z",
    "closed_at": "2013-12-12T14:42:58Z",
    "updated_at": "2013-12-12T14:42:58Z",
    "is_template": False,
    "departments": [
        {"id": 25907, "name": "Second-Level department", "parent_id": 25908}
    ],
    "offices": [
        {
            "id": 47012,
            "name": "New York",
            "location": {"name": "New York, United States"},
        }
    ],
    "hiring_team": {
        "hiring_managers": [
            {
                "id": 84275,
                "first_name": "Kaylee",
                "last_name": "Prime",
                "name": "Kaylee Prime",
                "employee_id": "13636",
            }
        ],
        "recruiters": [
            {
                "id": 81111,
                "first_name": "Samuel",
                "last_name": "Skateboard",
                "name": "Samuel Skateboard",
                "employee_id": "34531",
                "responsible": True,
            }
        ],
        "coordinators": [],
        "sourcers": [],
    },
    "openings": [
        {
            "id": 123,
            "opening_id": "3-1",
            "status": "open",
            "opened_at": "2015-11-20T23:14:14.736Z",
            "closed_at": None,
            "application_id": None,
            "close_reason": {"id": 678, "name": "Hired - Backfill"},
        }
    ],
    "custom_fields": {"employment_type": "Full-Time"},
}

_APPLICATION_RAW: dict[str, Any] = {
    "id": 985314,
    "candidate_id": 978031,
    "prospect": False,
    "applied_at": "2016-03-26T20:11:39.000Z",
    "rejected_at": "2016-08-17T21:08:29.686Z",
    "last_activity_at": "2016-08-27T16:13:15.000Z",
    "location": {"address": "New York, New York, USA"},
    "source": {"id": 1871, "public_name": "Happy Hour"},
    "credited_to": _USER_REF,
    "recruiter": _USER_REF,
    "coordinator": _USER_REF,
    "rejection_reason": {
        "id": 8,
        "name": "Lacking skill(s)/qualification(s)",
        "type": {"id": 1, "name": "We rejected them"},
    },
    "jobs": [{"id": 123, "name": "Accounting Manager"}],
    "job_post_id": 123,
    "status": "rejected",
    "current_stage": {"id": 62828, "name": "Recruiter Phone Screen"},
    "answers": [{"question": "Why do you want to work for us?", "answer": "You're awesome!"}],
    "attachments": [
        {
            "filename": "resume.pdf",
            "url": "https://prod-heroku.s3.amazonaws.com/resume.pdf",
            "type": "resume",
            "created_at": "2020-09-27T18:45:27.137Z",
        }
    ],
    "custom_fields": {"bio": "This is a bio"},
}

_USER_RAW: dict[str, Any] = {
    "id": 112,
    "name": "Juliet Burke",
    "first_name": "Juliet",
    "last_name": "Burke",
    "primary_email_address": "juliet.burke@example.com",
    "updated_at": "2016-11-17T16:13:48.888Z",
    "created_at": "2015-11-18T22:26:32.243Z",
    "disabled": False,
    "site_admin": True,
    "emails": ["juliet.burke@example.com", "other.woman@example.com"],
    "employee_id": "221",
    "linked_candidate_ids": [123, 654],
}

_DEPARTMENT_RAW: dict[str, Any] = {
    "id": 12345,
    "name": "Technology",
    "parent_id": 12000,
    "child_ids": [34065, 25908],
    "external_id": "89076",
}

_OFFICE_RAW: dict[str, Any] = {
    "id": 47012,
    "name": "New York",
    "location": {"name": "New York, United States"},
    "primary_contact_user_id": 485538,
    "parent_id": 50849,
    "child_ids": [50891, 50852],
    "external_id": "12345",
}

_JOB_STAGE_RAW: dict[str, Any] = {
    "id": 72200,
    "name": "Face to Face",
    "created_at": "2016-10-22T05:31:37.263Z",
    "updated_at": "2016-10-22T05:31:37.263Z",
    "active": True,
    "job_id": 98765,
    "priority": 0,
    "interviews": [
        {
            "id": 6001,
            "name": "Cultural Fit Interview",
            "schedulable": True,
            "estimated_minutes": 30,
            "default_interviewer_users": [
                {
                    "id": 821,
                    "first_name": "Robert",
                    "last_name": "Robertson",
                    "name": "Robert Robertson",
                    "employee_id": "100377",
                }
            ],
            "interview_kit": {
                "id": 9123,
                "content": "<h5>Purpose</h5>",
                "questions": [{"id": 11052, "question": "Is this person a good fit?"}],
            },
        }
    ],
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_11_actions(self) -> None:
        assert len(manifest.actions) == 11

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Candidates -------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_candidates(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/candidates?per_page=2&job_id=6404&email=test@work.com",
        json=[_CANDIDATE_RAW],
        headers={
            "link": f'<{API}/candidates?page=2&per_page=2>; rel="next"',
        },
    )

    result_dict = await list_candidates.ainvoke(
        _args(per_page=2, job_id="6404", email="test@work.com")
    )

    assert isinstance(result_dict, dict)
    result = ListCandidatesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.next_page == 2
    assert result.candidates[0].id == 53883394
    assert result.candidates[0].tags == ["Python", "Ruby"]
    assert result.candidates[0].email_addresses[0].value == "test@work.com"
    request = httpx_mock.get_requests()[0]
    assert request.headers["Authorization"] == _EXPECTED_BASIC


@pytest.mark.asyncio
async def test_get_candidate(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET", url=f"{API}/candidates/53883394", json=_CANDIDATE_RAW
    )

    result_dict = await get_candidate.ainvoke(_args(candidate_id="53883394"))

    assert isinstance(result_dict, dict)
    result = GetCandidateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.first_name == "John"
    assert result.phone_numbers[0].value == "555-555-5555"
    assert result.educations[0].school_name == "University of Michigan - Ann Arbor"
    assert result.employments[0].company_name == "Greenhouse"
    assert result.recruiter is not None
    assert result.recruiter.name == "Greenhouse Admin"
    assert result.custom_fields["work_remotely"] is True


# --- Jobs -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_jobs(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/jobs?status=open&department_id=25907&office_id=47012",
        json=[_JOB_RAW],
    )

    result_dict = await list_jobs.ainvoke(
        _args(status="open", department_id="25907", office_id="47012")
    )

    assert isinstance(result_dict, dict)
    result = ListJobsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.next_page is None
    assert result.jobs[0].name == "Archaeologist"
    assert result.jobs[0].departments[0].id == 25907
    assert result.jobs[0].offices[0].location is not None
    assert result.jobs[0].offices[0].location.name == "New York, United States"


@pytest.mark.asyncio
async def test_get_job(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/jobs/6404", json=_JOB_RAW)

    result_dict = await get_job.ainvoke(_args(job_id="6404"))

    assert isinstance(result_dict, dict)
    result = GetJobOutput.model_validate(result_dict)
    assert result.success is True
    assert result.requisition_id == "abc123"
    assert result.hiring_team is not None
    assert result.hiring_team.recruiters[0].responsible is True
    assert result.openings[0].close_reason is not None
    assert result.openings[0].close_reason.name == "Hired - Backfill"
    assert result.custom_fields["employment_type"] == "Full-Time"


# --- Applications -----------------------------------------------------------


@pytest.mark.asyncio
async def test_list_applications(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/applications?per_page=1&status=rejected&job_id=123",
        json=[_APPLICATION_RAW],
    )

    result_dict = await list_applications.ainvoke(
        _args(per_page=1, status="rejected", job_id="123")
    )

    assert isinstance(result_dict, dict)
    result = ListApplicationsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.applications[0].candidate_id == 978031
    assert result.applications[0].current_stage is not None
    assert result.applications[0].current_stage.name == "Recruiter Phone Screen"
    assert result.applications[0].jobs[0].name == "Accounting Manager"


@pytest.mark.asyncio
async def test_get_application(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET", url=f"{API}/applications/985314", json=_APPLICATION_RAW
    )

    result_dict = await get_application.ainvoke(_args(application_id="985314"))

    assert isinstance(result_dict, dict)
    result = GetApplicationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.source is not None
    assert result.source.public_name == "Happy Hour"
    assert result.rejection_reason is not None
    assert result.rejection_reason.type is not None
    assert result.rejection_reason.type.name == "We rejected them"
    assert result.answers[0].answer == "You're awesome!"
    assert result.attachments[0].type == "resume"
    assert result.location is not None
    assert result.location.address == "New York, New York, USA"


# --- Users ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_users(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users?email=juliet.burke@example.com",
        json=[_USER_RAW],
    )

    result_dict = await list_users.ainvoke(_args(email="juliet.burke@example.com"))

    assert isinstance(result_dict, dict)
    result = ListUsersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.users[0].site_admin is True
    assert result.users[0].emails == [
        "juliet.burke@example.com",
        "other.woman@example.com",
    ]
    assert result.users[0].linked_candidate_ids == [123, 654]


@pytest.mark.asyncio
async def test_get_user(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/users/112", json=_USER_RAW)

    result_dict = await get_user.ainvoke(_args(user_id="112"))

    assert isinstance(result_dict, dict)
    result = GetUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "Juliet Burke"
    assert result.employee_id == "221"
    assert result.disabled is False


# --- Organization structure -------------------------------------------------


@pytest.mark.asyncio
async def test_list_departments(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET", url=f"{API}/departments?per_page=100", json=[_DEPARTMENT_RAW]
    )

    result_dict = await list_departments.ainvoke(_args(per_page=100))

    assert isinstance(result_dict, dict)
    result = ListDepartmentsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.departments[0].name == "Technology"
    assert result.departments[0].child_ids == [34065, 25908]


@pytest.mark.asyncio
async def test_list_offices(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/offices?page=2", json=[_OFFICE_RAW])

    result_dict = await list_offices.ainvoke(_args(page=2))

    assert isinstance(result_dict, dict)
    result = ListOfficesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.offices[0].primary_contact_user_id == 485538
    assert result.offices[0].location is not None
    assert result.offices[0].location.name == "New York, United States"


@pytest.mark.asyncio
async def test_list_job_stages(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET", url=f"{API}/jobs/98765/stages", json=[_JOB_STAGE_RAW]
    )

    result_dict = await list_job_stages.ainvoke(_args(job_id="98765"))

    assert isinstance(result_dict, dict)
    result = ListJobStagesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.stages[0].name == "Face to Face"
    assert result.stages[0].interviews[0].estimated_minutes == 30
    assert result.stages[0].interviews[0].default_interviewer_users[0].name == "Robert Robertson"
    kit = result.stages[0].interviews[0].interview_kit
    assert kit is not None
    assert kit.questions[0].question == "Is this person a good fit?"


# --- Failure paths ----------------------------------------------------------


@pytest.mark.asyncio
async def test_unauthorized_returns_error(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET", url=f"{API}/candidates", status_code=401, text="Invalid Basic Auth"
    )

    result_dict = await list_candidates.ainvoke(_args())

    result = ListCandidatesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_forbidden_returns_error(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/112",
        status_code=403,
        text="You do not have permission",
    )

    result_dict = await get_user.ainvoke(_args(user_id="112"))

    result = GetUserOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "403" in result.error


@pytest.mark.asyncio
async def test_object_where_array_expected_degrades(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """A list endpoint answering with an object must not raise past the tool."""
    httpx_mock.add_response(method="GET", url=f"{API}/jobs", json={"error": "nope"})

    result_dict = await list_jobs.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListJobsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "unexpected response shape" in result.error


@pytest.mark.asyncio
async def test_array_where_object_expected_degrades(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """A retrieve endpoint answering with a bare array must not raise either."""
    httpx_mock.add_response(method="GET", url=f"{API}/candidates/1", json=[])

    result_dict = await get_candidate.ainvoke(_args(candidate_id="1"))

    assert isinstance(result_dict, dict)
    result = GetCandidateOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "unexpected response shape" in result.error


@pytest.mark.asyncio
async def test_wrong_typed_fields_degrade_to_none(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """A 200 whose fields carry the wrong TYPE must still return an envelope.

    Without the scalar coercers this raises ``pydantic.ValidationError``
    straight through the ``@tool`` boundary: the model construction sits
    after the ``except`` clauses, so guarding only the parse is not enough.
    """
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/candidates/1",
        json={
            "id": "53883394",
            "first_name": 42,
            "is_private": "yes",
            "can_email": 1,
            "tags": [1, "Ruby", None],
            "application_ids": ["69102626", 65153308],
            "email_addresses": {"value": "not-a-list"},
            "recruiter": "Greenhouse Admin",
            "attachments": [{"filename": 7, "url": None, "type": ["resume"]}],
            "custom_fields": ["not", "an", "object"],
        },
    )

    result_dict = await get_candidate.ainvoke(_args(candidate_id="1"))

    assert isinstance(result_dict, dict)
    result = GetCandidateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id is None  # "53883394" is a str, not an int
    assert result.first_name == "42"  # scalar widened to str
    assert result.is_private is None  # "yes" is not a bool
    assert result.can_email is None  # 1 is not a bool
    assert result.tags == ["Ruby"]  # non-str members dropped
    assert result.application_ids == [65153308]
    assert result.email_addresses == []
    assert result.recruiter is None
    assert result.attachments[0].filename == "7"
    assert result.attachments[0].type is None
    assert result.custom_fields == {}


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits() -> None:
    result_dict = await list_candidates.ainvoke({"api_key": "   "})

    result = ListCandidatesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits_for_retrieves() -> None:
    result_dict = await get_job.ainvoke({"job_id": "6404", "api_key": ""})

    result = GetJobOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error


@pytest.mark.asyncio
async def test_blank_path_id_short_circuits() -> None:
    """An empty id would otherwise silently hit the collection endpoint."""
    result_dict = await get_candidate.ainvoke(_args(candidate_id="   "))

    result = GetCandidateOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "candidate_id is required."


# --- Transport invariants ---------------------------------------------------


@pytest.mark.asyncio
async def test_path_id_cannot_escape_its_segment(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    """A hostile id must stay inside the path segment of the fixed host."""
    httpx_mock.add_response(json=_CANDIDATE_RAW)

    await get_candidate.ainvoke(_args(candidate_id="1@attacker.example/../../users"))

    request = httpx_mock.get_requests()[0]
    assert request.url.host == "harvest.greenhouse.io"
    # raw_path is what goes on the wire; ``url.path`` reports the decoded form.
    assert request.url.raw_path == b"/v1/candidates/1%40attacker.example%2F..%2F..%2Fusers"


@pytest.mark.parametrize(
    "key",
    [
        "fake-api-key",
        "",
        "a" * 300,
        "key:with:colons",
        "unicøde-key",
        "key with spaces",
        "+/=padding+/=",
        # Payloads that exercise the two alphabet-specific base64 characters:
        # "ab~:" encodes to "YWJ+Og==" (a ``+``) and "ÿÿ:" to "w7/Dvzo=" (a
        # ``/``). Without them a URL-safe encoder would satisfy every other
        # case here, since none of the keys above produce either character.
        "ab~",
        "ÿÿ",
    ],
)
def test_basic_auth_header_matches_httpx_reference(key: str) -> None:
    """The hand-built Basic header must equal httpx's own RFC 7617
    implementation for every key shape, including the trailing colon
    that encodes Harvest's empty password. Asserting only the ``Basic ``
    prefix would pass with a wrong credential and 401 in production.
    """
    request = httpx.Request("GET", f"{API}/candidates")
    expected = next(httpx.BasicAuth(key, "").auth_flow(request)).headers["Authorization"]

    actual = _headers(key)["Authorization"]

    assert actual == expected
    assert base64.b64decode(actual.split(" ", 1)[1]) == f"{key}:".encode()


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, None),
        ("", None),
        (f'<{API}/candidates?page=2&per_page=100>; rel="next"', 2),
        (
            f'<{API}/candidates?page=4&per_page=100>; rel="last",'
            f'<{API}/candidates?page=2&per_page=100>; rel="next"',
            2,
        ),
        (f"<{API}/candidates?page=3>; rel=next", 3),
        (f'<{API}/candidates?page=4&per_page=100>; rel="last"', None),
        (f'<{API}/candidates?per_page=100>; rel="next"', None),
        (f'<{API}/candidates?page=abc>; rel="next"', None),
        ("garbage", None),
    ],
)
def test_next_page_parses_link_header(header: str | None, expected: int | None) -> None:
    """Harvest paginates via Link headers; a missing rel=next means last page.

    Reading it wrong either stops pagination early or loops forever, and
    neither failure shows up as an error.
    """
    assert _next_page(header) == expected
