"""Ashby integration manifest.

Declares the Ashby ATS tool's actions, parameters, and the single
API-key (BYOK) credential schema the modulex runtime uses to drive
credential UI, validation, and tool discovery.

Ashby authenticates with HTTP Basic auth where the API key is the
username and the password is empty, so the credential test is declared
with ``BasicAuthSpec(username_placeholder="api_key",
password_placeholder="")`` and the runtime synthesizes the
``Authorization`` header.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    BasicAuthSpec,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


_CURSOR = ParameterDef(
    type="string",
    description="Opaque pagination cursor from a previous response's next_cursor value",
)
_PER_PAGE = ParameterDef(
    type="integer",
    description="Number of results per page (default and max 100)",
)
_SYNC_TOKEN = ParameterDef(
    type="string",
    description="Opaque token from a prior sync; returns only items changed since then",
)


manifest = IntegrationManifest(
    name="ashby",
    display_name="Ashby",
    description=(
        "Manage recruiting in Ashby. Work with candidates (list, get, create, "
        "update, search, tag), applications (list, get, create, change stage), "
        "jobs, job postings, offers, notes, interview schedules, and reference "
        "data such as sources, tags, archive reasons, custom fields, "
        "departments, locations, openings, and users."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:ashby-themed",
    app_url="https://ashbyhq.com",
    categories=["Productivity & Collaboration", "hr", "recruiting", "ats"],
    actions=[
        ActionDefinition(
            name="list_candidates",
            description=(
                "List all candidates in an Ashby organization with cursor-based pagination."
            ),
            parameters={
                "cursor": _CURSOR,
                "per_page": _PER_PAGE,
                "created_after": ParameterDef(
                    type="string",
                    description=(
                        "Only return candidates created after this ISO 8601 timestamp "
                        "(e.g. 2024-01-01T00:00:00Z)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_candidate",
            description="Retrieve full details about a single candidate by their ID.",
            parameters={
                "candidate_id": ParameterDef(
                    type="string",
                    description="The UUID of the candidate to fetch",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_candidate",
            description="Create a new candidate record in Ashby.",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="The candidate's full name (e.g. Jane Smith)",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="Primary email address for the candidate",
                ),
                "phone_number": ParameterDef(
                    type="string",
                    description="Primary phone number for the candidate",
                ),
                "linkedin_url": ParameterDef(
                    type="string",
                    description="LinkedIn profile URL",
                ),
                "github_url": ParameterDef(
                    type="string",
                    description="GitHub profile URL",
                ),
                "website": ParameterDef(
                    type="string",
                    description="Personal website URL",
                ),
                "source_id": ParameterDef(
                    type="string",
                    description="UUID of the source to attribute the candidate to",
                ),
                "credited_to_user_id": ParameterDef(
                    type="string",
                    description="UUID of the Ashby user credited with sourcing this candidate",
                ),
                "created_at": ParameterDef(
                    type="string",
                    description=(
                        "Backdated ISO 8601 creation timestamp "
                        "(e.g. 2024-01-01T00:00:00Z); defaults to now"
                    ),
                ),
                "alternate_email_addresses": ParameterDef(
                    type="array",
                    description="Additional email address strings to add to the candidate",
                ),
            },
        ),
        ActionDefinition(
            name="update_candidate",
            description=(
                "Update an existing candidate record in Ashby. Only provided fields change."
            ),
            parameters={
                "candidate_id": ParameterDef(
                    type="string",
                    description="The UUID of the candidate to update",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Updated full name",
                ),
                "email": ParameterDef(
                    type="string",
                    description="Updated primary email address",
                ),
                "phone_number": ParameterDef(
                    type="string",
                    description="Updated primary phone number",
                ),
                "linkedin_url": ParameterDef(
                    type="string",
                    description="LinkedIn profile URL",
                ),
                "github_url": ParameterDef(
                    type="string",
                    description="GitHub profile URL",
                ),
                "website_url": ParameterDef(
                    type="string",
                    description="Personal website URL",
                ),
                "alternate_email": ParameterDef(
                    type="string",
                    description="An additional email address to add to the candidate",
                ),
                "source_id": ParameterDef(
                    type="string",
                    description="UUID of the source to attribute the candidate to",
                ),
                "credited_to_user_id": ParameterDef(
                    type="string",
                    description="UUID of the Ashby user credited with sourcing this candidate",
                ),
                "created_at": ParameterDef(
                    type="string",
                    description=(
                        "Backdated ISO 8601 creation timestamp; only updatable if the "
                        "candidate was originally backdated"
                    ),
                ),
                "send_notifications": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether subscribed users are notified about the update (default true)"
                    ),
                ),
                "social_links": ParameterDef(
                    type="array",
                    description=(
                        'Social link objects to set, e.g. [{"type":"LinkedIn",'
                        '"url":"https://..."}]. Replaces existing social links.'
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="search_candidates",
            description=(
                "Search candidates by name and/or email using AND logic. "
                "Limited to 100 matches; use list_candidates for full pagination."
            ),
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Candidate name to search for",
                ),
                "email": ParameterDef(
                    type="string",
                    description="Candidate email to search for",
                ),
            },
        ),
        ActionDefinition(
            name="list_jobs",
            description=(
                "List jobs in an Ashby organization. Returns Open, Closed and Archived "
                "jobs by default; pass status to filter."
            ),
            parameters={
                "cursor": _CURSOR,
                "per_page": _PER_PAGE,
                "status": ParameterDef(
                    type="string",
                    description="Filter by job status: Open, Closed, Archived, or Draft",
                ),
                "created_after": ParameterDef(
                    type="string",
                    description="Only return jobs created after this ISO 8601 timestamp",
                ),
                "opened_after": ParameterDef(
                    type="string",
                    description="Only return jobs opened after this ISO 8601 timestamp",
                ),
                "opened_before": ParameterDef(
                    type="string",
                    description="Only return jobs opened before this ISO 8601 timestamp",
                ),
                "closed_after": ParameterDef(
                    type="string",
                    description="Only return jobs closed after this ISO 8601 timestamp",
                ),
                "closed_before": ParameterDef(
                    type="string",
                    description="Only return jobs closed before this ISO 8601 timestamp",
                ),
            },
        ),
        ActionDefinition(
            name="get_job",
            description="Retrieve full details about a single job by its ID.",
            parameters={
                "job_id": ParameterDef(
                    type="string",
                    description="The UUID of the job to fetch",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_note",
            description=(
                "Create a note on a candidate. Supports plain text and HTML content "
                "(bold, italic, underline, links, lists, code)."
            ),
            parameters={
                "candidate_id": ParameterDef(
                    type="string",
                    description="The UUID of the candidate to add the note to",
                    required=True,
                ),
                "note": ParameterDef(
                    type="string",
                    description=(
                        "The note content. With note_type text/html these tags are "
                        "supported: <b>, <i>, <u>, <a>, <ul>, <ol>, <li>, <code>, <pre>"
                    ),
                    required=True,
                ),
                "note_type": ParameterDef(
                    type="string",
                    description="Content type of the note: 'text/plain' or 'text/html'",
                    default="text/plain",
                ),
                "send_notifications": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether subscribed users are notified about the note (default false)"
                    ),
                    default=False,
                ),
                "is_private": ParameterDef(
                    type="boolean",
                    description="Whether the note is private (visible to the author only)",
                ),
                "created_at": ParameterDef(
                    type="string",
                    description="Backdated ISO 8601 creation timestamp; defaults to now",
                ),
            },
        ),
        ActionDefinition(
            name="list_notes",
            description="List all notes on a candidate with cursor-based pagination.",
            parameters={
                "candidate_id": ParameterDef(
                    type="string",
                    description="The UUID of the candidate to list notes for",
                    required=True,
                ),
                "cursor": _CURSOR,
                "per_page": _PER_PAGE,
            },
        ),
        ActionDefinition(
            name="list_applications",
            description=(
                "List applications with pagination and optional status, job and "
                "creation-date filters."
            ),
            parameters={
                "cursor": _CURSOR,
                "per_page": _PER_PAGE,
                "status": ParameterDef(
                    type="string",
                    description=(
                        "Filter by application status: Active, Hired, Archived, or Lead"
                    ),
                ),
                "job_id": ParameterDef(
                    type="string",
                    description="Filter applications by a specific job UUID",
                ),
                "created_after": ParameterDef(
                    type="string",
                    description="Only return applications created after this ISO 8601 timestamp",
                ),
            },
        ),
        ActionDefinition(
            name="get_application",
            description="Retrieve full details about a single application by its ID.",
            parameters={
                "application_id": ParameterDef(
                    type="string",
                    description="The UUID of the application to fetch",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_application",
            description=(
                "Create a new application for a candidate on a job, optionally setting "
                "interview plan, stage, source and credited user."
            ),
            parameters={
                "candidate_id": ParameterDef(
                    type="string",
                    description="The UUID of the candidate to consider for the job",
                    required=True,
                ),
                "job_id": ParameterDef(
                    type="string",
                    description="The UUID of the job to consider the candidate for",
                    required=True,
                ),
                "interview_plan_id": ParameterDef(
                    type="string",
                    description="Interview plan UUID (defaults to the job's default plan)",
                ),
                "interview_stage_id": ParameterDef(
                    type="string",
                    description="Interview stage UUID (defaults to the first Lead stage)",
                ),
                "source_id": ParameterDef(
                    type="string",
                    description="UUID of the source to set on the application",
                ),
                "credited_to_user_id": ParameterDef(
                    type="string",
                    description="UUID of the user the application is credited to",
                ),
                "created_at": ParameterDef(
                    type="string",
                    description=(
                        "ISO 8601 timestamp to set as the application creation date "
                        "(defaults to now)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="change_application_stage",
            description=(
                "Move an application to a different interview stage. An archive reason "
                "is required when moving to an Archived stage."
            ),
            parameters={
                "application_id": ParameterDef(
                    type="string",
                    description="The UUID of the application to move",
                    required=True,
                ),
                "interview_stage_id": ParameterDef(
                    type="string",
                    description="The UUID of the interview stage to move the application to",
                    required=True,
                ),
                "archive_reason_id": ParameterDef(
                    type="string",
                    description=(
                        "Archive reason UUID; required when moving to an Archived stage, "
                        "ignored otherwise"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="add_candidate_tag",
            description="Add a tag to a candidate and return the updated candidate.",
            parameters={
                "candidate_id": ParameterDef(
                    type="string",
                    description="The UUID of the candidate to add the tag to",
                    required=True,
                ),
                "tag_id": ParameterDef(
                    type="string",
                    description="The UUID of the tag to add",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="remove_candidate_tag",
            description="Remove a tag from a candidate and return the updated candidate.",
            parameters={
                "candidate_id": ParameterDef(
                    type="string",
                    description="The UUID of the candidate to remove the tag from",
                    required=True,
                ),
                "tag_id": ParameterDef(
                    type="string",
                    description="The UUID of the tag to remove",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_offers",
            description="List offers with their latest version.",
            parameters={
                "cursor": _CURSOR,
                "per_page": _PER_PAGE,
                "created_after": ParameterDef(
                    type="string",
                    description="Only return offers created after this ISO 8601 timestamp",
                ),
                "sync_token": _SYNC_TOKEN,
                "application_id": ParameterDef(
                    type="string",
                    description="Return only offers for the specified application UUID",
                ),
            },
        ),
        ActionDefinition(
            name="get_offer",
            description="Retrieve full details about a single offer by its ID.",
            parameters={
                "offer_id": ParameterDef(
                    type="string",
                    description="The UUID of the offer to fetch",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_sources",
            description="List all candidate sources configured in Ashby.",
            parameters={
                "include_archived": ParameterDef(
                    type="boolean",
                    description="When true, includes archived sources (default false)",
                ),
            },
        ),
        ActionDefinition(
            name="list_candidate_tags",
            description="List all candidate tags configured in Ashby.",
            parameters={
                "include_archived": ParameterDef(
                    type="boolean",
                    description="When true, includes archived candidate tags (default false)",
                ),
                "cursor": _CURSOR,
                "sync_token": _SYNC_TOKEN,
                "per_page": _PER_PAGE,
            },
        ),
        ActionDefinition(
            name="list_archive_reasons",
            description="List all archive reasons configured in Ashby.",
            parameters={
                "include_archived": ParameterDef(
                    type="boolean",
                    description="When true, includes archived archive reasons (default false)",
                ),
            },
        ),
        ActionDefinition(
            name="list_custom_fields",
            description="List all custom field definitions configured in Ashby.",
            parameters={
                "cursor": _CURSOR,
                "per_page": _PER_PAGE,
                "sync_token": _SYNC_TOKEN,
                "include_archived": ParameterDef(
                    type="boolean",
                    description="When true, includes archived custom fields (default false)",
                ),
            },
        ),
        ActionDefinition(
            name="list_departments",
            description="List all departments in Ashby.",
            parameters={
                "cursor": _CURSOR,
                "per_page": _PER_PAGE,
                "sync_token": _SYNC_TOKEN,
                "include_archived": ParameterDef(
                    type="boolean",
                    description="When true, includes archived departments (default false)",
                ),
            },
        ),
        ActionDefinition(
            name="list_locations",
            description="List all locations configured in Ashby.",
            parameters={
                "cursor": _CURSOR,
                "per_page": _PER_PAGE,
                "sync_token": _SYNC_TOKEN,
                "include_archived": ParameterDef(
                    type="boolean",
                    description="When true, includes archived locations (default false)",
                ),
                "include_location_hierarchy": ParameterDef(
                    type="boolean",
                    description=(
                        "When true, includes location hierarchy components/regions "
                        "(default false)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="list_job_postings",
            description="List job postings on a job board.",
            parameters={
                "location": ParameterDef(
                    type="string",
                    description="Filter by location name (case sensitive)",
                ),
                "department": ParameterDef(
                    type="string",
                    description="Filter by department name (case sensitive)",
                ),
                "listed_only": ParameterDef(
                    type="boolean",
                    description=(
                        "When true, only returns publicly listed job postings (default false)"
                    ),
                ),
                "job_board_id": ParameterDef(
                    type="string",
                    description=(
                        "Job board UUID to filter to; defaults to the primary external "
                        "job board"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_job_posting",
            description="Retrieve full details about a single job posting by its ID.",
            parameters={
                "job_posting_id": ParameterDef(
                    type="string",
                    description="The UUID of the job posting to fetch",
                    required=True,
                ),
                "job_board_id": ParameterDef(
                    type="string",
                    description=(
                        "Job board UUID; defaults to the external job board when omitted"
                    ),
                ),
                "expand_job": ParameterDef(
                    type="boolean",
                    description="Whether to include the related job object in the response",
                ),
            },
        ),
        ActionDefinition(
            name="list_openings",
            description="List headcount openings in Ashby with cursor-based pagination.",
            parameters={
                "cursor": _CURSOR,
                "per_page": _PER_PAGE,
                "created_after": ParameterDef(
                    type="string",
                    description="Only return openings created after this ISO 8601 timestamp",
                ),
            },
        ),
        ActionDefinition(
            name="list_users",
            description="List users in the Ashby organization with cursor-based pagination.",
            parameters={
                "cursor": _CURSOR,
                "per_page": _PER_PAGE,
                "include_deactivated": ParameterDef(
                    type="boolean",
                    description="When true, includes deactivated users (default false)",
                ),
            },
        ),
        ActionDefinition(
            name="list_interviews",
            description=(
                "List interview schedules, optionally filtered by application or "
                "interview stage."
            ),
            parameters={
                "application_id": ParameterDef(
                    type="string",
                    description="Only return interview schedules for this application UUID",
                ),
                "interview_stage_id": ParameterDef(
                    type="string",
                    description="Only return interview schedules for this interview stage UUID",
                ),
                "cursor": _CURSOR,
                "per_page": _PER_PAGE,
                "created_after": ParameterDef(
                    type="string",
                    description=(
                        "Only return interview schedules created after this ISO 8601 timestamp"
                    ),
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using an Ashby API key",
            setup_instructions=[
                "Sign in to Ashby as an admin and open Settings -> Integrations -> API",
                "Create a new API key and grant it the permissions you need "
                "(candidates, jobs, offers, organization, hiring process metadata)",
                "Also grant the 'API Keys' read permission so the credential can be "
                "validated",
                "Copy the generated key (it is shown only once) and paste it below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="ASHBY_API_KEY",
                    display_name="Ashby API Key",
                    description="Your Ashby API key from Settings -> Integrations -> API",
                    required=True,
                    sensitive=True,
                    about_url="https://developers.ashbyhq.com/docs/authentication",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.ashbyhq.com/apiKey.info",
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json; version=1",
                },
                body={},
                auth=BasicAuthSpec(
                    username_placeholder="api_key",
                    password_placeholder="",
                ),
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description="Validates the API key by fetching its own key metadata",
            ),
        ),
    ],
)
