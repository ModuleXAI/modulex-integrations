"""Greenhouse integration manifest.

Declares the Greenhouse Harvest API tool's actions, parameters, and the
single API-key (BYOK) credential schema the modulex runtime uses to
drive credential UI, validation, and tool discovery.

Greenhouse's Harvest API authenticates with HTTP Basic auth where the
API key is the username and the password is empty, so the credential
test is declared with ``BasicAuthSpec(username_placeholder="api_key",
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


_PER_PAGE = ParameterDef(
    type="integer",
    description="Number of results per page, between 1 and 500 (default 100)",
)
_PAGE = ParameterDef(
    type="integer",
    description="Page number to return; combine with next_page from a previous response",
)
_CREATED_AFTER = ParameterDef(
    type="string",
    description=(
        "Return only records created at or after this ISO 8601 timestamp "
        "(e.g. 2024-01-01T00:00:00Z)"
    ),
)
_CREATED_BEFORE = ParameterDef(
    type="string",
    description=(
        "Return only records created before this ISO 8601 timestamp "
        "(e.g. 2024-01-01T00:00:00Z)"
    ),
)
_UPDATED_AFTER = ParameterDef(
    type="string",
    description=(
        "Return only records updated at or after this ISO 8601 timestamp "
        "(e.g. 2024-01-01T00:00:00Z)"
    ),
)
_UPDATED_BEFORE = ParameterDef(
    type="string",
    description=(
        "Return only records updated before this ISO 8601 timestamp "
        "(e.g. 2024-01-01T00:00:00Z)"
    ),
)


manifest = IntegrationManifest(
    name="greenhouse",
    display_name="Greenhouse",
    description=(
        "Work with the Greenhouse applicant tracking system. List and retrieve "
        "candidates, jobs, applications, and users, and browse the organization "
        "structure behind them — departments, offices, and the interview stages "
        "configured on each job."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:greenhouse-themed",
    app_url="https://www.greenhouse.com",
    categories=["Productivity & Collaboration", "hr", "recruiting", "ats"],
    actions=[
        ActionDefinition(
            name="list_candidates",
            description="List candidates with optional date, job, email or id filters.",
            parameters={
                "per_page": _PER_PAGE,
                "page": _PAGE,
                "created_after": _CREATED_AFTER,
                "created_before": _CREATED_BEFORE,
                "updated_after": _UPDATED_AFTER,
                "updated_before": _UPDATED_BEFORE,
                "job_id": ParameterDef(
                    type="string",
                    description=(
                        "Only return candidates who applied to this job id "
                        "(prospects on the job are excluded)"
                    ),
                ),
                "email": ParameterDef(
                    type="string",
                    description="Only return candidates with this email address",
                ),
                "candidate_ids": ParameterDef(
                    type="string",
                    description=(
                        'Comma-separated candidate ids to fetch, e.g. "123,456" '
                        "(max 50; ignored when email is also supplied)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_candidate",
            description=(
                "Retrieve one candidate with contact details, education and employment."
            ),
            parameters={
                "candidate_id": ParameterDef(
                    type="string",
                    description="The id of the candidate to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_jobs",
            description="List jobs with optional status, department, office or date filters.",
            parameters={
                "per_page": _PER_PAGE,
                "page": _PAGE,
                "status": ParameterDef(
                    type="string",
                    description="Filter by job status: open, closed or draft",
                ),
                "created_after": _CREATED_AFTER,
                "created_before": _CREATED_BEFORE,
                "updated_after": _UPDATED_AFTER,
                "updated_before": _UPDATED_BEFORE,
                "department_id": ParameterDef(
                    type="string",
                    description="Only return jobs in this department id",
                ),
                "office_id": ParameterDef(
                    type="string",
                    description="Only return jobs in this office id",
                ),
            },
        ),
        ActionDefinition(
            name="get_job",
            description="Retrieve one job with its hiring team, openings and custom fields.",
            parameters={
                "job_id": ParameterDef(
                    type="string",
                    description="The id of the job to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_applications",
            description="List applications with optional job, status or date filters.",
            parameters={
                "per_page": _PER_PAGE,
                "page": _PAGE,
                "job_id": ParameterDef(
                    type="string",
                    description="Only return applications that involve this job id",
                ),
                "status": ParameterDef(
                    type="string",
                    description=(
                        "Filter by application status: active, converted, hired or rejected"
                    ),
                ),
                "created_after": _CREATED_AFTER,
                "created_before": _CREATED_BEFORE,
                "last_activity_after": ParameterDef(
                    type="string",
                    description=(
                        "Only return applications whose last activity is at or after this "
                        "ISO 8601 timestamp"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_application",
            description=(
                "Retrieve one application with its source, stage, answers and attachments."
            ),
            parameters={
                "application_id": ParameterDef(
                    type="string",
                    description="The id of the application to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_users",
            description=(
                "List Greenhouse users (recruiters, coordinators, hiring managers, admins)."
            ),
            parameters={
                "per_page": _PER_PAGE,
                "page": _PAGE,
                "created_after": _CREATED_AFTER,
                "created_before": _CREATED_BEFORE,
                "updated_after": _UPDATED_AFTER,
                "updated_before": _UPDATED_BEFORE,
                "email": ParameterDef(
                    type="string",
                    description=(
                        "Return the user with this address as a primary or secondary email"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="get_user",
            description="Retrieve one Greenhouse user by id.",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="The id of the user to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_departments",
            description="List all departments configured in the organization.",
            parameters={
                "per_page": _PER_PAGE,
                "page": _PAGE,
            },
        ),
        ActionDefinition(
            name="list_offices",
            description="List all offices configured in the organization.",
            parameters={
                "per_page": _PER_PAGE,
                "page": _PAGE,
            },
        ),
        ActionDefinition(
            name="list_job_stages",
            description="List the interview stages configured on a specific job.",
            parameters={
                "job_id": ParameterDef(
                    type="string",
                    description="The id of the job whose interview stages to list",
                    required=True,
                ),
                "per_page": _PER_PAGE,
                "page": _PAGE,
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using a Greenhouse Harvest API key",
            setup_instructions=[
                "Sign in to Greenhouse as a user with the \"Can manage ALL organization's "
                'API credentials" permission and open Configure -> Dev Center -> '
                "API Credential Management",
                "Click Create New API Key, choose API type 'Harvest', name the key, then "
                "copy it — Greenhouse shows the full key only once",
                "Click Manage permissions on the key and grant GET access to Candidates, "
                "Jobs, Applications, Users, Departments, Offices and Job Stages",
                "Paste the key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="GREENHOUSE_API_KEY",
                    display_name="Greenhouse Harvest API Key",
                    description=(
                        "Your Greenhouse Harvest API key from Configure -> Dev Center -> "
                        "API Credential Management"
                    ),
                    required=True,
                    sensitive=True,
                    about_url="https://developers.greenhouse.io/harvest.html#authentication",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://harvest.greenhouse.io/v1/candidates",
                method="GET",
                headers={"Content-Type": "application/json"},
                params={"per_page": "1"},
                auth=BasicAuthSpec(
                    username_placeholder="api_key",
                    password_placeholder="",
                ),
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description=(
                    "Validates the API key by fetching a single candidate; requires the "
                    "credential's GET Candidates permission"
                ),
            ),
        ),
    ],
)
