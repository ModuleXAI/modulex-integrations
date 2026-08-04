"""Happy-path tests per action plus failure-path, envelope-failure and
empty-credential tests.

Ashby answers what would normally be a 4XX with HTTP 200 and
``"success": false``, so the failure tests cover both that envelope and
a real non-2xx (401 with a plain-text body).
"""
from __future__ import annotations

import base64
from typing import Any

import httpx
import pytest

from modulex_integrations.tools.ashby import (
    TOOLS,
    add_candidate_tag,
    change_application_stage,
    create_application,
    create_candidate,
    create_note,
    get_application,
    get_candidate,
    get_job,
    get_job_posting,
    get_offer,
    list_applications,
    list_archive_reasons,
    list_candidate_tags,
    list_candidates,
    list_custom_fields,
    list_departments,
    list_interviews,
    list_job_postings,
    list_jobs,
    list_locations,
    list_notes,
    list_offers,
    list_openings,
    list_sources,
    list_users,
    manifest,
    remove_candidate_tag,
    search_candidates,
    update_candidate,
)
from modulex_integrations.tools.ashby.outputs import (
    AddCandidateTagOutput,
    ChangeApplicationStageOutput,
    CreateApplicationOutput,
    CreateCandidateOutput,
    CreateNoteOutput,
    GetApplicationOutput,
    GetCandidateOutput,
    GetJobOutput,
    GetJobPostingOutput,
    GetOfferOutput,
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
    RemoveCandidateTagOutput,
    SearchCandidatesOutput,
    UpdateCandidateOutput,
)
from modulex_integrations.tools.ashby.tools import _headers, _iso_to_ms

API = "https://api.ashbyhq.com"
_API_KEY = "fake-api-key"
_EXPECTED_BASIC = "Basic " + base64.b64encode(f"{_API_KEY}:".encode()).decode()

_CANDIDATE_RAW: dict[str, Any] = {
    "id": "cand_1",
    "name": "Jane Smith",
    "primaryEmailAddress": {"value": "jane@example.com", "type": "Personal", "isPrimary": True},
    "primaryPhoneNumber": {"value": "+1555", "type": "Mobile", "isPrimary": True},
    "emailAddresses": [{"value": "jane@example.com", "type": "Personal", "isPrimary": True}],
    "phoneNumbers": [{"value": "+1555", "type": "Mobile", "isPrimary": True}],
    "socialLinks": [
        {"type": "LinkedIn", "url": "https://linkedin.com/in/jane"},
        {"type": "GitHub", "url": "https://github.com/jane"},
    ],
    "profileUrl": "https://app.ashbyhq.com/candidates/cand_1",
    "position": "Engineer",
    "company": "Acme",
    "school": "MIT",
    "timezone": "America/New_York",
    "location": {
        "id": "loc_1",
        "locationSummary": "New York, NY",
        "locationComponents": [{"type": "city", "name": "New York"}],
    },
    "tags": [{"id": "tag_1", "title": "Referral", "isArchived": False}],
    "applicationIds": ["app_1"],
    "customFields": [
        {"id": "cf_1", "title": "Seniority", "isPrivate": False, "valueLabel": "L5", "value": "L5"}
    ],
    "resumeFileHandle": {"id": "file_1", "name": "cv.pdf", "handle": "handle_1"},
    "fileHandles": [{"id": "file_1", "name": "cv.pdf", "handle": "handle_1"}],
    "source": {
        "id": "src_1",
        "title": "Referral",
        "isArchived": False,
        "sourceType": {"id": "st_1", "title": "Employee Referral", "isArchived": False},
    },
    "creditedToUser": {
        "id": "usr_1",
        "firstName": "Ada",
        "lastName": "Lovelace",
        "email": "ada@example.com",
        "globalRole": "Admin",
        "isEnabled": True,
        "updatedAt": "2024-01-02T00:00:00Z",
    },
    "fraudStatus": "NotFraudulent",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-02T00:00:00Z",
}

_JOB_RAW: dict[str, Any] = {
    "id": "job_1",
    "title": "Staff Engineer",
    "confidential": False,
    "status": "Open",
    "employmentType": "FullTime",
    "locationId": "loc_1",
    "departmentId": "dep_1",
    "defaultInterviewPlanId": "plan_1",
    "interviewPlanIds": ["plan_1"],
    "customFields": [],
    "jobPostingIds": ["post_1"],
    "customRequisitionId": "REQ-1",
    "brandId": "brand_1",
    "hiringTeam": [
        {
            "userId": "usr_1",
            "firstName": "Ada",
            "lastName": "Lovelace",
            "email": "ada@example.com",
            "role": "Recruiter",
        }
    ],
    "author": {"id": "usr_1", "firstName": "Ada", "isEnabled": True},
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-02T00:00:00Z",
    "openedAt": "2024-01-01T00:00:00Z",
    "closedAt": None,
    "location": {
        "id": "loc_1",
        "name": "New York",
        "externalName": "NYC",
        "isArchived": False,
        "isRemote": False,
        "workplaceType": "OnSite",
        "parentLocationId": None,
        "type": "Location",
        "address": {
            "postalAddress": {
                "addressCountry": "USA",
                "addressRegion": "NY",
                "addressLocality": "New York",
                "postalCode": "10001",
                "streetAddress": "1 Main St",
            }
        },
    },
    "openings": [
        {
            "id": "open_1",
            "openedAt": "2024-01-01T00:00:00Z",
            "isArchived": False,
            "openingState": "Open",
            "latestVersion": {
                "id": "ver_1",
                "identifier": "OPEN-1",
                "jobIds": ["job_1"],
                "isBackfill": False,
                "locationIds": ["loc_1"],
                "hiringTeam": [],
                "customFields": [],
            },
        }
    ],
    "compensation": {
        "compensationTiers": [
            {
                "id": "tier_1",
                "title": "Base",
                "additionalInformation": "plus equity",
                "tierSummary": "$200k",
            }
        ]
    },
}

_APPLICATION_RAW: dict[str, Any] = {
    "id": "app_1",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-02T00:00:00Z",
    "status": "Active",
    "customFields": [],
    "candidate": {
        "id": "cand_1",
        "name": "Jane Smith",
        "primaryEmailAddress": {"value": "jane@example.com", "type": "Personal", "isPrimary": True},
    },
    "currentInterviewStage": {
        "id": "stage_1",
        "title": "Phone Screen",
        "type": "Active",
        "orderInInterviewPlan": 2,
        "interviewStageGroupId": "grp_1",
        "interviewPlanId": "plan_1",
    },
    "source": {"id": "src_1", "title": "Referral", "isArchived": False},
    "archiveReason": None,
    "archivedAt": None,
    "job": {"id": "job_1", "title": "Staff Engineer", "locationId": "loc_1"},
    "creditedToUser": {"id": "usr_1", "firstName": "Ada", "isEnabled": True},
    "hiringTeam": [],
    "appliedViaJobPostingId": "post_1",
    "submitterClientIp": "10.0.0.1",
    "submitterUserAgent": "Mozilla/5.0",
    "applicationHistory": [
        {
            "id": "hist_1",
            "stageId": "stage_1",
            "stageNumber": 2,
            "title": "Phone Screen",
            "enteredStageAt": "2024-01-01T00:00:00Z",
            "actorId": "usr_1",
        }
    ],
}

_OFFER_RAW: dict[str, Any] = {
    "id": "offer_1",
    "decidedAt": "2024-02-01T00:00:00Z",
    "applicationId": "app_1",
    "acceptanceStatus": "Accepted",
    "offerStatus": "CandidateAccepted",
    "latestVersion": {
        "id": "ver_1",
        "startDate": "2024-03-01",
        "salary": {"currencyCode": "USD", "value": 200000},
        "createdAt": "2024-01-20T00:00:00Z",
        "openingId": "open_1",
        "customFields": [],
        "fileHandles": [{"id": "file_2", "name": "offer.pdf", "handle": "handle_2"}],
        "author": {"id": "usr_1", "firstName": "Ada", "isEnabled": True},
        "approvalStatus": "Approved",
    },
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


def _ok(results: Any, **extra: Any) -> dict[str, Any]:
    return {"success": True, "results": results, **extra}


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_28_actions(self) -> None:
        assert len(manifest.actions) == 28

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Candidates -------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_candidates(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/candidate.list",
        json=_ok([_CANDIDATE_RAW], moreDataAvailable=True, nextCursor="qA"),
    )

    result_dict = await list_candidates.ainvoke(
        _args(per_page=25, created_after="2024-01-01T00:00:00Z")
    )

    assert isinstance(result_dict, dict)
    result = ListCandidatesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.more_data_available is True
    assert result.next_cursor == "qA"
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.name == "Jane Smith"
    assert candidate.linkedin_url == "https://linkedin.com/in/jane"
    assert candidate.github_url == "https://github.com/jane"
    assert candidate.primary_email_address is not None
    assert candidate.primary_email_address.value == "jane@example.com"

    request = httpx_mock.get_requests()[0]
    assert request.headers["Authorization"] == _EXPECTED_BASIC
    assert request.headers["Accept"] == "application/json; version=1"
    assert b'"limit":25' in request.content.replace(b" ", b"")
    assert b'"createdAfter":1704067200000' in request.content.replace(b" ", b"")


@pytest.mark.asyncio
async def test_get_candidate(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/candidate.info", json=_ok(_CANDIDATE_RAW)
    )

    result_dict = await get_candidate.ainvoke(_args(candidate_id=" cand_1 "))

    assert isinstance(result_dict, dict)
    result = GetCandidateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "cand_1"
    assert result.source is not None
    assert result.source.source_type is not None
    assert result.source.source_type.title == "Employee Referral"
    assert b'"id":"cand_1"' in httpx_mock.get_requests()[0].content.replace(b" ", b"")


@pytest.mark.asyncio
async def test_create_candidate(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/candidate.create", json=_ok(_CANDIDATE_RAW)
    )

    result_dict = await create_candidate.ainvoke(
        _args(
            name="Jane Smith",
            email="jane@example.com",
            linkedin_url="https://linkedin.com/in/jane",
            alternate_email_addresses=["jane.work@example.com"],
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateCandidateOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "Jane Smith"
    body = httpx_mock.get_requests()[0].content.replace(b" ", b"")
    assert b'"linkedInUrl":"https://linkedin.com/in/jane"' in body
    assert b'"alternateEmailAddresses":["jane.work@example.com"]' in body


@pytest.mark.asyncio
async def test_update_candidate(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/candidate.update", json=_ok(_CANDIDATE_RAW)
    )

    result_dict = await update_candidate.ainvoke(
        _args(
            candidate_id="cand_1",
            name="Jane S.",
            send_notifications=False,
            social_links=[{"type": "Twitter", "url": "https://twitter.com/jane"}],
        )
    )

    assert isinstance(result_dict, dict)
    result = UpdateCandidateOutput.model_validate(result_dict)
    assert result.success is True
    body = httpx_mock.get_requests()[0].content.replace(b" ", b"")
    assert b'"candidateId":"cand_1"' in body
    assert b'"sendNotifications":false' in body


@pytest.mark.asyncio
async def test_search_candidates(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/candidate.search", json=_ok([_CANDIDATE_RAW])
    )

    result_dict = await search_candidates.ainvoke(
        _args(name="Jane Smith", email="jane@example.com")
    )

    assert isinstance(result_dict, dict)
    result = SearchCandidatesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.candidates) == 1
    assert result.candidates[0].id == "cand_1"


@pytest.mark.asyncio
async def test_add_candidate_tag(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/candidate.addTag", json=_ok(_CANDIDATE_RAW)
    )

    result_dict = await add_candidate_tag.ainvoke(_args(candidate_id="cand_1", tag_id="tag_1"))

    assert isinstance(result_dict, dict)
    result = AddCandidateTagOutput.model_validate(result_dict)
    assert result.success is True
    assert [tag.title for tag in result.tags] == ["Referral"]


@pytest.mark.asyncio
async def test_remove_candidate_tag(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/candidate.removeTag", json=_ok(_CANDIDATE_RAW)
    )

    result_dict = await remove_candidate_tag.ainvoke(
        _args(candidate_id="cand_1", tag_id="tag_1")
    )

    assert isinstance(result_dict, dict)
    result = RemoveCandidateTagOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "cand_1"


# --- Notes ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_note(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/candidate.createNote",
        json=_ok(
            {
                "id": "note_1",
                "createdAt": "2024-01-03T00:00:00Z",
                "isPrivate": False,
                "content": "<b>Strong</b> candidate",
                "author": {
                    "id": "usr_1",
                    "firstName": "Ada",
                    "lastName": "Lovelace",
                    "email": "ada@example.com",
                },
            }
        ),
    )

    result_dict = await create_note.ainvoke(
        _args(candidate_id="cand_1", note="<b>Strong</b> candidate", note_type="text/html")
    )

    assert isinstance(result_dict, dict)
    result = CreateNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "note_1"
    assert result.author is not None
    assert result.author.email == "ada@example.com"
    body = httpx_mock.get_requests()[0].content.replace(b" ", b"")
    assert b'"note":{"type":"text/html","value":"<b>Strong</b>candidate"}' in body


@pytest.mark.asyncio
async def test_list_notes(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/candidate.listNotes",
        json=_ok(
            [
                {
                    "id": "note_1",
                    "content": "Great call",
                    "isPrivate": False,
                    "author": {"id": "usr_1", "firstName": "Ada"},
                    "createdAt": "2024-01-03T00:00:00Z",
                }
            ],
            moreDataAvailable=False,
            nextCursor=None,
        ),
    )

    result_dict = await list_notes.ainvoke(_args(candidate_id="cand_1", per_page=10))

    assert isinstance(result_dict, dict)
    result = ListNotesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.notes) == 1
    assert result.notes[0].content == "Great call"
    assert result.more_data_available is False


# --- Jobs -------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_jobs(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/job.list",
        json=_ok([_JOB_RAW], moreDataAvailable=False, nextCursor=None),
    )

    result_dict = await list_jobs.ainvoke(
        _args(status="Open", opened_after="2024-01-01T00:00:00Z")
    )

    assert isinstance(result_dict, dict)
    result = ListJobsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.jobs) == 1
    job = result.jobs[0]
    assert job.title == "Staff Engineer"
    assert job.location is not None
    assert job.location.address is not None
    assert job.location.address.postal_code == "10001"
    assert len(job.openings) == 1
    body = httpx_mock.get_requests()[0].content.replace(b" ", b"")
    assert b'"expand":["openings","location"]' in body
    assert b'"status":["Open"]' in body


@pytest.mark.asyncio
async def test_get_job(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/job.info", json=_ok(_JOB_RAW))

    result_dict = await get_job.ainvoke(_args(job_id="job_1"))

    assert isinstance(result_dict, dict)
    result = GetJobOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "job_1"
    assert result.compensation is not None
    assert result.compensation.compensation_tiers[0].tier_summary == "$200k"
    body = httpx_mock.get_requests()[0].content.replace(b" ", b"")
    assert b'"expand":["openings","location","compensation"]' in body


# --- Applications -----------------------------------------------------------


@pytest.mark.asyncio
async def test_list_applications(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/application.list",
        json=_ok([_APPLICATION_RAW], moreDataAvailable=True, nextCursor="Rl"),
    )

    result_dict = await list_applications.ainvoke(_args(status="Active", job_id="job_1"))

    assert isinstance(result_dict, dict)
    result = ListApplicationsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.applications) == 1
    application = result.applications[0]
    assert application.candidate is not None
    assert application.candidate.name == "Jane Smith"
    assert application.current_interview_stage is not None
    assert application.current_interview_stage.order_in_interview_plan == 2
    assert result.next_cursor == "Rl"


@pytest.mark.asyncio
async def test_get_application(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/application.info", json=_ok(_APPLICATION_RAW)
    )

    result_dict = await get_application.ainvoke(_args(application_id="app_1"))

    assert isinstance(result_dict, dict)
    result = GetApplicationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "app_1"
    assert len(result.application_history) == 1
    assert result.application_history[0].stage_number == 2


@pytest.mark.asyncio
async def test_create_application(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/application.create", json=_ok(_APPLICATION_RAW)
    )

    result_dict = await create_application.ainvoke(
        _args(candidate_id="cand_1", job_id="job_1", interview_stage_id="stage_1")
    )

    assert isinstance(result_dict, dict)
    result = CreateApplicationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.job is not None
    assert result.job.title == "Staff Engineer"
    body = httpx_mock.get_requests()[0].content.replace(b" ", b"")
    assert b'"interviewStageId":"stage_1"' in body


@pytest.mark.asyncio
async def test_change_application_stage(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/application.changeStage", json=_ok(_APPLICATION_RAW)
    )

    result_dict = await change_application_stage.ainvoke(
        _args(application_id="app_1", interview_stage_id="stage_2", archive_reason_id="ar_1")
    )

    assert isinstance(result_dict, dict)
    result = ChangeApplicationStageOutput.model_validate(result_dict)
    assert result.success is True
    body = httpx_mock.get_requests()[0].content.replace(b" ", b"")
    assert b'"archiveReasonId":"ar_1"' in body


# --- Offers -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_offers(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/offer.list",
        json=_ok([_OFFER_RAW], moreDataAvailable=False, nextCursor=None),
    )

    result_dict = await list_offers.ainvoke(_args(application_id="app_1", sync_token="mqXvvQBWO"))

    assert isinstance(result_dict, dict)
    result = ListOffersOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.offers) == 1
    assert result.offers[0].latest_version is not None
    assert result.offers[0].latest_version.salary is not None
    assert result.offers[0].latest_version.salary.value == 200000.0


@pytest.mark.asyncio
async def test_get_offer(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/offer.info", json=_ok(_OFFER_RAW))

    result_dict = await get_offer.ainvoke(_args(offer_id="offer_1"))

    assert isinstance(result_dict, dict)
    result = GetOfferOutput.model_validate(result_dict)
    assert result.success is True
    assert result.offer_status == "CandidateAccepted"


# --- Reference data ---------------------------------------------------------


@pytest.mark.asyncio
async def test_list_sources(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/source.list",
        json=_ok(
            [
                {
                    "id": "src_1",
                    "title": "Referral",
                    "isArchived": False,
                    "sourceType": {
                        "id": "st_1",
                        "title": "Employee Referral",
                        "isArchived": False,
                    },
                }
            ]
        ),
    )

    result_dict = await list_sources.ainvoke(_args(include_archived=True))

    assert isinstance(result_dict, dict)
    result = ListSourcesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sources[0].source_type is not None
    assert result.sources[0].source_type.id == "st_1"


@pytest.mark.asyncio
async def test_list_candidate_tags(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/candidateTag.list",
        json=_ok(
            [{"id": "tag_1", "title": "Referral", "isArchived": False}],
            moreDataAvailable=False,
            nextCursor=None,
            syncToken="6W05prn4d",
        ),
    )

    result_dict = await list_candidate_tags.ainvoke(_args(include_archived=False))

    assert isinstance(result_dict, dict)
    result = ListCandidateTagsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.tags[0].title == "Referral"
    assert result.sync_token == "6W05prn4d"


@pytest.mark.asyncio
async def test_list_archive_reasons(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/archiveReason.list",
        json=_ok(
            [
                {
                    "id": "ar_1",
                    "text": "Rejected by org",
                    "reasonType": "RejectedByOrg",
                    "isArchived": False,
                }
            ]
        ),
    )

    result_dict = await list_archive_reasons.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListArchiveReasonsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.archive_reasons[0].reason_type == "RejectedByOrg"


@pytest.mark.asyncio
async def test_list_custom_fields(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/customField.list",
        json=_ok(
            [
                {
                    "id": "cf_1",
                    "title": "Seniority",
                    "isPrivate": False,
                    "fieldType": "ValueSelect",
                    "objectType": "Candidate",
                    "isArchived": False,
                    "isRequired": True,
                    "selectableValues": [
                        {"label": "L5", "value": "l5", "isArchived": False},
                    ],
                }
            ],
            moreDataAvailable=False,
            nextCursor=None,
            syncToken="jYnEBmjzR",
        ),
    )

    result_dict = await list_custom_fields.ainvoke(_args(per_page=100))

    assert isinstance(result_dict, dict)
    result = ListCustomFieldsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.custom_fields[0].field_type == "ValueSelect"
    assert result.custom_fields[0].selectable_values[0].label == "L5"
    assert result.sync_token == "jYnEBmjzR"


@pytest.mark.asyncio
async def test_list_departments(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/department.list",
        json=_ok(
            [
                {
                    "id": "dep_1",
                    "name": "Engineering",
                    "externalName": "Eng",
                    "isArchived": False,
                    "parentId": None,
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-02T00:00:00Z",
                    "extraData": {"code": "ENG"},
                }
            ],
            moreDataAvailable=False,
            nextCursor=None,
            syncToken="dep-sync",
        ),
    )

    result_dict = await list_departments.ainvoke(_args(include_archived=False))

    assert isinstance(result_dict, dict)
    result = ListDepartmentsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.departments[0].external_name == "Eng"
    assert result.departments[0].extra_data == {"code": "ENG"}


@pytest.mark.asyncio
async def test_list_locations(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/location.list",
        json=_ok(
            [
                {
                    "id": "loc_1",
                    "name": "New York",
                    "externalName": "NYC",
                    "isArchived": False,
                    "isRemote": False,
                    "workplaceType": "OnSite",
                    "parentLocationId": None,
                    "type": "Location",
                    "address": {
                        "postalAddress": {
                            "addressCountry": "USA",
                            "addressRegion": "NY",
                            "addressLocality": "New York",
                            "postalCode": "10001",
                            "streetAddress": "1 Main St",
                        }
                    },
                    "extraData": None,
                }
            ],
            moreDataAvailable=False,
            nextCursor=None,
            syncToken="loc-sync",
        ),
    )

    result_dict = await list_locations.ainvoke(_args(include_location_hierarchy=True))

    assert isinstance(result_dict, dict)
    result = ListLocationsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.locations[0].address is not None
    assert result.locations[0].address.address_locality == "New York"
    body = httpx_mock.get_requests()[0].content.replace(b" ", b"")
    assert b'"includeLocationHierarchy":true' in body


# --- Job postings -----------------------------------------------------------


@pytest.mark.asyncio
async def test_list_job_postings(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/jobPosting.list",
        json=_ok(
            [
                {
                    "id": "post_1",
                    "title": "Staff Engineer",
                    "jobId": "job_1",
                    "departmentName": "Engineering",
                    "teamName": "Platform",
                    "locationName": "New York",
                    "locationIds": {
                        "primaryLocationId": "loc_1",
                        "secondaryLocationIds": ["loc_2"],
                    },
                    "workplaceType": "OnSite",
                    "employmentType": "FullTime",
                    "isListed": True,
                    "publishedDate": "2024-01-05",
                    "applicationDeadline": None,
                    "externalLink": "https://jobs.ashbyhq.com/acme/post_1",
                    "applyLink": "https://jobs.ashbyhq.com/acme/post_1/application",
                    "compensationTierSummary": "$200k",
                    "shouldDisplayCompensationOnJobBoard": True,
                    "updatedAt": "2024-01-06T00:00:00Z",
                }
            ]
        ),
    )

    result_dict = await list_job_postings.ainvoke(_args(location="New York", listed_only=True))

    assert isinstance(result_dict, dict)
    result = ListJobPostingsOutput.model_validate(result_dict)
    assert result.success is True
    posting = result.job_postings[0]
    assert posting.location_ids is not None
    assert posting.location_ids.secondary_location_ids == ["loc_2"]
    assert posting.should_display_compensation_on_job_board is True


@pytest.mark.asyncio
async def test_get_job_posting(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/jobPosting.info",
        json=_ok(
            {
                "id": "post_1",
                "title": "Staff Engineer",
                "descriptionPlain": "Build things",
                "descriptionHtml": "<p>Build things</p>",
                "descriptionSocial": "Build things",
                "descriptionParts": {
                    "descriptionOpening": {"html": "<p>Hi</p>", "plain": "Hi"},
                    "descriptionBody": {"html": "<p>Body</p>", "plain": "Body"},
                    "descriptionClosing": None,
                },
                "departmentName": "Engineering",
                "teamName": "Platform",
                "teamNameHierarchy": ["Engineering", "Platform"],
                "jobId": "job_1",
                "locationName": "New York",
                "locationIds": {"primaryLocationId": "loc_1", "secondaryLocationIds": []},
                "address": {
                    "postalAddress": {
                        "addressCountry": "USA",
                        "addressRegion": "NY",
                        "addressLocality": "New York",
                        "postalCode": "10001",
                        "streetAddress": "1 Main St",
                    }
                },
                "isRemote": False,
                "workplaceType": "OnSite",
                "employmentType": "FullTime",
                "isListed": True,
                "suppressDescriptionOpening": False,
                "suppressDescriptionClosing": False,
                "publishedDate": "2024-01-05",
                "applicationDeadline": None,
                "externalLink": "https://jobs.ashbyhq.com/acme/post_1",
                "applyLink": "https://jobs.ashbyhq.com/acme/post_1/application",
                "compensation": {
                    "compensationTierSummary": "$200k",
                    "summaryComponents": [
                        {
                            "summary": "$200k",
                            "compensationTypeLabel": "Salary",
                            "interval": "1 YEAR",
                            "currencyCode": "USD",
                            "minValue": 190000,
                            "maxValue": 210000,
                        }
                    ],
                    "shouldDisplayCompensationOnJobBoard": True,
                },
                "applicationLimitCalloutHtml": None,
                "updatedAt": "2024-01-06T00:00:00Z",
                "job": {"id": "job_1", "title": "Staff Engineer"},
            }
        ),
    )

    result_dict = await get_job_posting.ainvoke(_args(job_posting_id="post_1", expand_job=True))

    assert isinstance(result_dict, dict)
    result = GetJobPostingOutput.model_validate(result_dict)
    assert result.success is True
    assert result.description_parts is not None
    assert result.description_parts.description_body is not None
    assert result.description_parts.description_body.plain == "Body"
    assert result.compensation is not None
    assert result.compensation.summary_components[0].max_value == 210000.0
    assert result.job == {"id": "job_1", "title": "Staff Engineer"}
    body = httpx_mock.get_requests()[0].content.replace(b" ", b"")
    assert b'"expand":["job"]' in body


# --- Openings / users / interviews ------------------------------------------


@pytest.mark.asyncio
async def test_list_openings(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/opening.list",
        json=_ok(
            [
                {
                    "id": "open_1",
                    "openedAt": "2024-01-01T00:00:00Z",
                    "closedAt": None,
                    "isArchived": False,
                    "archivedAt": None,
                    "closeReasonId": None,
                    "openingState": "Open",
                    "latestVersion": {
                        "id": "ver_1",
                        "identifier": "OPEN-1",
                        "description": "Backfill",
                        "authorId": "usr_1",
                        "createdAt": "2024-01-01T00:00:00Z",
                        "teamId": "team_1",
                        "jobIds": ["job_1"],
                        "targetHireDate": "2024-03-01",
                        "targetStartDate": "2024-04-01",
                        "isBackfill": True,
                        "employmentType": "FullTime",
                        "locationIds": ["loc_1"],
                        "hiringTeam": [],
                        "customFields": [],
                    },
                }
            ],
            moreDataAvailable=False,
            nextCursor=None,
        ),
    )

    result_dict = await list_openings.ainvoke(_args(created_after="1704067200000"))

    assert isinstance(result_dict, dict)
    result = ListOpeningsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.openings[0].latest_version is not None
    assert result.openings[0].latest_version.is_backfill is True
    body = httpx_mock.get_requests()[0].content.replace(b" ", b"")
    assert b'"createdAfter":1704067200000' in body


@pytest.mark.asyncio
async def test_list_users(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/user.list",
        json=_ok(
            [
                {
                    "id": "usr_1",
                    "firstName": "Ada",
                    "lastName": "Lovelace",
                    "email": "ada@example.com",
                    "globalRole": "Admin",
                    "isEnabled": True,
                    "updatedAt": "2024-01-02T00:00:00Z",
                    "managerId": None,
                }
            ],
            moreDataAvailable=False,
            nextCursor=None,
        ),
    )

    result_dict = await list_users.ainvoke(_args(include_deactivated=True))

    assert isinstance(result_dict, dict)
    result = ListUsersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.users[0].global_role == "Admin"


@pytest.mark.asyncio
async def test_list_interviews(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/interviewSchedule.list",
        json=_ok(
            [
                {
                    "id": "sched_1",
                    "status": "Scheduled",
                    "applicationId": "app_1",
                    "interviewStageId": "stage_1",
                    "scheduledBy": {"id": "usr_1", "firstName": "Ada", "isEnabled": True},
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-02T00:00:00Z",
                    "interviewEvents": [
                        {
                            "id": "evt_1",
                            "interviewId": "int_1",
                            "interviewScheduleId": "sched_1",
                            "interviewerUserIds": ["usr_1"],
                            "createdAt": "2024-01-01T00:00:00Z",
                            "updatedAt": "2024-01-02T00:00:00Z",
                            "startTime": "2024-01-10T15:00:00Z",
                            "endTime": "2024-01-10T16:00:00Z",
                            "feedbackLink": "https://app.ashbyhq.com/feedback/evt_1",
                            "location": "Zoom",
                            "meetingLink": "https://zoom.us/j/1",
                            "hasSubmittedFeedback": False,
                        }
                    ],
                }
            ],
            moreDataAvailable=False,
            nextCursor=None,
        ),
    )

    result_dict = await list_interviews.ainvoke(_args(application_id="app_1"))

    assert isinstance(result_dict, dict)
    result = ListInterviewsOutput.model_validate(result_dict)
    assert result.success is True
    schedule = result.interview_schedules[0]
    assert schedule.status == "Scheduled"
    assert schedule.interview_events[0].interviewer_user_ids == ["usr_1"]


# --- Failure paths ----------------------------------------------------------


@pytest.mark.asyncio
async def test_envelope_failure_is_not_success(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/application.info",
        status_code=200,
        json={
            "success": False,
            "errorInfo": {
                "code": "application_not_found",
                "message": "Application not found",
                "requestId": "req_1",
            },
        },
    )

    result_dict = await get_application.ainvoke(_args(application_id="missing"))

    result = GetApplicationOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "Application not found (application_not_found)"


@pytest.mark.asyncio
async def test_envelope_errors_array_is_joined(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/candidate.list",
        status_code=200,
        json={"success": False, "errors": [{"message": "Bad cursor"}, "Try again"]},
    )

    result_dict = await list_candidates.ainvoke(_args(cursor="bogus"))

    result = ListCandidatesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "Bad cursor; Try again"


@pytest.mark.asyncio
async def test_unauthorized_returns_error(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{API}/candidate.list", status_code=401, text="Unauthorized"
    )

    result_dict = await list_candidates.ainvoke(_args())

    result = ListCandidatesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_non_object_body_degrades(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/user.list", status_code=200, json=[])

    result_dict = await list_users.ainvoke(_args())

    result = ListUsersOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "Failed to list users"


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits() -> None:
    result_dict = await list_candidates.ainvoke({"api_key": "   "})

    result = ListCandidatesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits_for_writes() -> None:
    result_dict = await create_candidate.ainvoke({"name": "Jane", "api_key": ""})

    result = CreateCandidateOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error


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
    ],
)
def test_basic_auth_header_matches_httpx_reference(key: str) -> None:
    """The hand-built Basic header must equal httpx's own RFC 7617
    implementation for every key shape, including the trailing colon
    that encodes Ashby's empty password. Asserting only the ``Basic ``
    prefix would pass with a wrong credential and 401 in production.
    """
    request = httpx.Request("POST", f"{API}/apiKey.info")
    expected = next(httpx.BasicAuth(key, "").auth_flow(request)).headers["Authorization"]

    actual = _headers(key)["Authorization"]

    assert actual == expected
    assert base64.b64decode(actual.split(" ", 1)[1]) == f"{key}:".encode()


@pytest.mark.parametrize(
    ("supplied", "expected"),
    [
        ("1767225600", 1767225600000),        # epoch seconds -> promoted to ms
        ("1767225600000", 1767225600000),     # epoch milliseconds -> unchanged
        ("2026-01-01T00:00:00Z", 1767225600000),
        ("2026-01-01T00:00:00+00:00", 1767225600000),
        ("2026-01-01T00:00:00", 1767225600000),  # naive input is read as UTC
        ("not-a-date", None),
        ("", None),
        (None, None),
    ],
)
def test_iso_to_ms_accepts_seconds_and_milliseconds(
    supplied: str | None, expected: int | None
) -> None:
    """Epoch seconds must not be sent as milliseconds.

    A 10-digit epoch-seconds value passed straight through resolves to early
    1970, so a date filter silently matches everything — wrong results with no
    error. The two ranges never overlap for a real date.
    """
    assert _iso_to_ms(supplied) == expected
