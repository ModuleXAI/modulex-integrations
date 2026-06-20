"""Vanta integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    CustomAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


# Reusable pagination parameters shared by every list action.
_PAGE_SIZE = ParameterDef(
    type="integer",
    description="Maximum number of items per page (1-100, default 10).",
)
_PAGE_CURSOR = ParameterDef(
    type="string",
    description=(
        "Pagination cursor: pass the end_cursor from a previous response to "
        "fetch the next page."
    ),
)
_MAX_PAGES = ParameterDef(
    type="integer",
    description="Maximum number of pages to fetch when auto-paginating (default 1).",
    default=1,
)
_PAGINATION = {
    "page_size": _PAGE_SIZE,
    "page_cursor": _PAGE_CURSOR,
    "max_pages": _MAX_PAGES,
}


manifest = IntegrationManifest(
    name="vanta",
    display_name="Vanta",
    description=(
        "Query compliance posture and manage evidence in Vanta. Monitor "
        "frameworks, controls, and automated tests; find failing test "
        "entities; manage evidence documents including file upload, download, "
        "and submission; and track people, policies, vendors, monitored "
        "computers, vulnerabilities, and risk scenarios."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:vanta-themed",
    app_url="https://www.vanta.com",
    categories=["Monitoring & Observability", "Security", "Compliance", "GRC"],
    actions=[
        ActionDefinition(
            name="list_frameworks",
            description=(
                "List the compliance frameworks (e.g., SOC 2, ISO 27001) "
                "available in a Vanta account with completion counts."
            ),
            parameters=dict(_PAGINATION),
        ),
        ActionDefinition(
            name="get_framework",
            description=(
                "Get a Vanta compliance framework by ID, including its "
                "requirement categories and mapped controls."
            ),
            parameters={
                "framework_id": ParameterDef(
                    type="string",
                    description="Unique ID of the framework (e.g., soc2).",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_framework_controls",
            description="List the controls that belong to a specific Vanta compliance framework.",
            parameters={
                "framework_id": ParameterDef(
                    type="string",
                    description="Unique ID of the framework (e.g., soc2).",
                    required=True,
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="list_controls",
            description=(
                "List the security controls in a Vanta account, optionally "
                "filtered by framework."
            ),
            parameters={
                "framework_matches_any": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated framework IDs to filter controls by "
                        "(e.g., soc2,iso27001)."
                    ),
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="get_control",
            description=(
                "Get a Vanta security control by ID, including its status and "
                "evidence pass/fail counts."
            ),
            parameters={
                "control_id": ParameterDef(
                    type="string", description="Unique ID of the control.", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_control_tests",
            description="List the automated tests mapped to a specific Vanta control.",
            parameters={
                "control_id": ParameterDef(
                    type="string", description="Unique ID of the control.", required=True
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="list_control_documents",
            description="List the evidence documents mapped to a specific Vanta control.",
            parameters={
                "control_id": ParameterDef(
                    type="string", description="Unique ID of the control.", required=True
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="list_tests",
            description=(
                "List the automated compliance tests in a Vanta account, with "
                "filters for status, framework, integration, control, owner, and category."
            ),
            parameters={
                "status_filter": ParameterDef(
                    type="string",
                    description=(
                        "Filter by test status: OK, DEACTIVATED, NEEDS_ATTENTION, "
                        "IN_PROGRESS, INVALID, or NOT_APPLICABLE."
                    ),
                ),
                "framework_filter": ParameterDef(
                    type="string", description="Filter by framework ID (e.g., soc2)."
                ),
                "integration_filter": ParameterDef(
                    type="string", description="Filter by integration ID (e.g., aws)."
                ),
                "control_filter": ParameterDef(type="string", description="Filter by control ID."),
                "owner_filter": ParameterDef(type="string", description="Filter by owner user ID."),
                "category_filter": ParameterDef(
                    type="string",
                    description=(
                        "Filter by test category (e.g., ACCOUNTS_ACCESS, COMPUTERS, "
                        "INFRASTRUCTURE, POLICIES, VULNERABILITY_MANAGEMENT)."
                    ),
                ),
                "is_in_rollout": ParameterDef(
                    type="boolean", description="Filter by whether the test is in rollout."
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="get_test",
            description=(
                "Get a Vanta automated compliance test by ID, including its "
                "status and remediation info."
            ),
            parameters={
                "test_id": ParameterDef(
                    type="string",
                    description="Unique ID of the test (e.g., test-aws-cloudtrail-enabled).",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_test_entities",
            description=(
                "List the failing or deactivated resource entities for a "
                "specific Vanta test, useful for finding exactly which resources need remediation."
            ),
            parameters={
                "test_id": ParameterDef(
                    type="string",
                    description="Unique ID of the test (e.g., test-aws-cloudtrail-enabled).",
                    required=True,
                ),
                "entity_status": ParameterDef(
                    type="string",
                    description="Filter entities by status: FAILING or DEACTIVATED.",
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="list_documents",
            description=(
                "List the evidence documents in a Vanta account, optionally "
                "filtered by framework or document status."
            ),
            parameters={
                "framework_matches_any": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated framework IDs to filter documents by "
                        "(e.g., soc2,iso27001)."
                    ),
                ),
                "status_matches_any": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated document statuses to filter by: "
                        '"Needs document", "Needs update", "Not relevant", "OK".'
                    ),
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="get_document",
            description=(
                "Get a Vanta evidence document by ID, including its renewal "
                "schedule and deactivation status."
            ),
            parameters={
                "document_id": ParameterDef(
                    type="string", description="Unique ID of the document.", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_document_uploads",
            description="List the files uploaded to a specific Vanta evidence document.",
            parameters={
                "document_id": ParameterDef(
                    type="string", description="Unique ID of the document.", required=True
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="upload_document_file",
            description=(
                "Upload an evidence file to a Vanta document. Requires "
                "credentials with the vanta-api.documents:upload scope."
            ),
            parameters={
                "document_id": ParameterDef(
                    type="string",
                    description="Unique ID of the document to attach the file to.",
                    required=True,
                ),
                "file_content": ParameterDef(
                    type="string",
                    description="Base64-encoded content of the evidence file to upload.",
                    required=True,
                ),
                "file_name": ParameterDef(
                    type="string",
                    description="File name for the upload (e.g., access-review.pdf).",
                    required=True,
                ),
                "mime_type": ParameterDef(
                    type="string",
                    description="MIME type of the file (e.g., application/pdf).",
                ),
                "description": ParameterDef(
                    type="string",
                    description=(
                        "Description of the uploaded evidence "
                        '(e.g., "Q3 access review evidence").'
                    ),
                ),
                "effective_at_date": ParameterDef(
                    type="string",
                    description="ISO 8601 date indicating when the document is effective from.",
                ),
            },
        ),
        ActionDefinition(
            name="download_document_file",
            description=(
                "Download a file previously uploaded to a Vanta evidence "
                "document (returned as base64 content)."
            ),
            parameters={
                "document_id": ParameterDef(
                    type="string", description="Unique ID of the document.", required=True
                ),
                "uploaded_file_id": ParameterDef(
                    type="string",
                    description="Unique ID of the uploaded file (from list_document_uploads).",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="submit_document",
            description=(
                "Submit a Vanta document collection for review so uploaded "
                "evidence becomes visible to auditors. Requires credentials with write access."
            ),
            parameters={
                "document_id": ParameterDef(
                    type="string",
                    description="Unique ID of the document to submit.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_people",
            description=(
                "List the people tracked in a Vanta account with employment "
                "status, group membership, and security task completion."
            ),
            parameters={
                "email_and_name_filter": ParameterDef(
                    type="string", description="Filter people by email address or name."
                ),
                "employment_status": ParameterDef(
                    type="string",
                    description=(
                        "Filter by employment status: UPCOMING, CURRENT, "
                        "ON_LEAVE, INACTIVE, or FORMER."
                    ),
                ),
                "group_ids_matches_any": ParameterDef(
                    type="string", description="Comma-separated group IDs to filter people by."
                ),
                "tasks_summary_status_matches_any": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated task summary statuses: NONE, DUE_SOON, OVERDUE, "
                        "COMPLETE, PAUSED, OFFBOARDING_DUE_SOON, OFFBOARDING_OVERDUE, "
                        "OFFBOARDING_COMPLETE."
                    ),
                ),
                "task_type_matches_any": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated task types: COMPLETE_TRAININGS, ACCEPT_POLICIES, "
                        "COMPLETE_CUSTOM_TASKS, COMPLETE_CUSTOM_OFFBOARDING_TASKS, "
                        "INSTALL_DEVICE_MONITORING, COMPLETE_BACKGROUND_CHECKS."
                    ),
                ),
                "task_status_matches_any": ParameterDef(
                    type="string",
                    description="Comma-separated task statuses: COMPLETE, DUE_SOON, OVERDUE, NONE.",
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="get_person",
            description=(
                "Get a person tracked in Vanta by ID, including employment, "
                "leave, and security task status."
            ),
            parameters={
                "person_id": ParameterDef(
                    type="string", description="Unique ID of the person.", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_policies",
            description=(
                "List the security policies in a Vanta account with approval "
                "status and version info."
            ),
            parameters=dict(_PAGINATION),
        ),
        ActionDefinition(
            name="get_policy",
            description=(
                "Get a Vanta security policy by ID, including its approval "
                "status and latest approved version documents."
            ),
            parameters={
                "policy_id": ParameterDef(
                    type="string", description="Unique ID of the policy.", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_vendors",
            description=(
                "List the vendors tracked in a Vanta account with risk levels, "
                "contract dates, and security review schedules."
            ),
            parameters={
                "name": ParameterDef(type="string", description="Filter vendors by name."),
                "status_matches_any": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated vendor statuses: MANAGED, ARCHIVED, "
                        "IN_PROCUREMENT."
                    ),
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="get_vendor",
            description=(
                "Get a Vanta vendor by ID, including risk levels, contract "
                "details, and authentication info."
            ),
            parameters={
                "vendor_id": ParameterDef(
                    type="string", description="Unique ID of the vendor.", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_monitored_computers",
            description=(
                "List the monitored computers in a Vanta account with "
                "screenlock, disk encryption, password manager, and antivirus check outcomes."
            ),
            parameters={
                "compliance_status_filter_matches_any": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated compliance issues: PWM_NOT_INSTALLED, "
                        "HD_NOT_ENCRYPTED, AV_NOT_INSTALLED, SCREENLOCK_NOT_CONFIGURED, "
                        "LAST_CHECK_OVER_14_DAYS."
                    ),
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="list_vulnerabilities",
            description=(
                "List the vulnerabilities detected across a Vanta account with "
                "filters for severity, fixability, SLA deadlines, package, and integration."
            ),
            parameters={
                "q": ParameterDef(type="string", description="Search query for vulnerabilities."),
                "severity": ParameterDef(
                    type="string", description="Filter by severity: LOW, MEDIUM, HIGH, or CRITICAL."
                ),
                "is_fix_available": ParameterDef(
                    type="boolean", description="Filter by whether a fix is available."
                ),
                "is_deactivated": ParameterDef(
                    type="boolean",
                    description="Filter by whether vulnerability monitoring is deactivated.",
                ),
                "include_vulnerabilities_without_slas": ParameterDef(
                    type="boolean", description="Include vulnerabilities that have no SLA deadline."
                ),
                "package_identifier": ParameterDef(
                    type="string", description="Filter by the affected package identifier."
                ),
                "external_vulnerability_id": ParameterDef(
                    type="string",
                    description="Filter by external vulnerability ID (e.g., a CVE identifier).",
                ),
                "integration_id": ParameterDef(
                    type="string",
                    description="Filter by the integration that detected the vulnerability.",
                ),
                "vulnerable_asset_id": ParameterDef(
                    type="string", description="Filter by the vulnerable asset ID."
                ),
                "sla_deadline_after_date": ParameterDef(
                    type="string",
                    description=(
                        "Only include vulnerabilities with an SLA deadline after "
                        "this ISO 8601 date."
                    ),
                ),
                "sla_deadline_before_date": ParameterDef(
                    type="string",
                    description=(
                        "Only include vulnerabilities with an SLA deadline before "
                        "this ISO 8601 date."
                    ),
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="list_vulnerability_remediations",
            description=(
                "List remediated vulnerabilities in a Vanta account with "
                "detection, SLA deadline, and remediation dates."
            ),
            parameters={
                "integration_id": ParameterDef(
                    type="string",
                    description="Filter by the integration that detected the vulnerability.",
                ),
                "severity": ParameterDef(
                    type="string", description="Filter by severity: LOW, MEDIUM, HIGH, or CRITICAL."
                ),
                "is_remediated_on_time": ParameterDef(
                    type="boolean",
                    description=(
                        "Filter by whether the vulnerability was remediated before "
                        "its SLA deadline."
                    ),
                ),
                "remediated_after_date": ParameterDef(
                    type="string",
                    description="Only include remediations completed after this ISO 8601 date.",
                ),
                "remediated_before_date": ParameterDef(
                    type="string",
                    description="Only include remediations completed before this ISO 8601 date.",
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="list_vulnerable_assets",
            description=(
                "List the assets associated with vulnerabilities in a Vanta "
                "account (servers, repositories, workstations, and more)."
            ),
            parameters={
                "q": ParameterDef(type="string", description="Search query for vulnerable assets."),
                "integration_id": ParameterDef(
                    type="string", description="Filter by the integration scanning the asset."
                ),
                "asset_type": ParameterDef(
                    type="string",
                    description=(
                        "Filter by asset type: SERVER, SERVERLESS_FUNCTION, CONTAINER, "
                        "CONTAINER_REPOSITORY, CONTAINER_REPOSITORY_IMAGE, CODE_REPOSITORY, "
                        "MANIFEST_FILE, WORKSTATION, or OTHER."
                    ),
                ),
                "asset_external_account_id": ParameterDef(
                    type="string",
                    description="Filter by the external account ID the asset belongs to.",
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="get_vulnerable_asset",
            description=(
                "Get a vulnerable asset in Vanta by ID, including the scanners "
                "reporting it and per-scanner asset details."
            ),
            parameters={
                "vulnerable_asset_id": ParameterDef(
                    type="string", description="Unique ID of the vulnerable asset.", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_risk_scenarios",
            description=(
                "List the risk scenarios in a Vanta risk register with "
                "likelihood/impact scores, treatment decisions, and review status."
            ),
            parameters={
                "search_string": ParameterDef(
                    type="string", description="Search string to filter risk scenarios."
                ),
                "include_ignored": ParameterDef(
                    type="boolean", description="Include ignored risk scenarios."
                ),
                "type": ParameterDef(
                    type="string",
                    description='Filter by scenario type: "Risk Scenario" or "Enterprise Risk".',
                ),
                "owner_matches_any": ParameterDef(
                    type="string", description="Comma-separated owner emails to filter by."
                ),
                "category_matches_any": ParameterDef(
                    type="string", description="Comma-separated risk categories to filter by."
                ),
                "cia_category_matches_any": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated CIA categories: Confidentiality, "
                        "Integrity, Availability."
                    ),
                ),
                "treatment_type_matches_any": ParameterDef(
                    type="string",
                    description="Comma-separated treatments: Mitigate, Transfer, Avoid, Accept.",
                ),
                "inherent_score_group_matches_any": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated inherent score groups: "
                        '"Very low", Low, Med, High, Critical.'
                    ),
                ),
                "residual_score_group_matches_any": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated residual score groups: "
                        '"Very low", Low, Med, High, Critical.'
                    ),
                ),
                "review_status_matches_any": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated review statuses: APPROVED, DRAFT, NOT_REVIEWED, "
                        "AWAITING_SUBMISSION, PENDING_APPROVAL, REQUESTED_CHANGES."
                    ),
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Field to order results by: description or createdAt.",
                ),
                **_PAGINATION,
            },
        ),
        ActionDefinition(
            name="get_risk_scenario",
            description=(
                "Get a Vanta risk scenario by ID, including its scores, "
                "treatment decision, and review status."
            ),
            parameters={
                "risk_scenario_id": ParameterDef(
                    type="string", description="Unique ID of the risk scenario.", required=True
                ),
            },
        ),
    ],
    auth_schemas=[
        CustomAuthSchema(
            display_name="Vanta OAuth Client Credentials",
            description=(
                "Authenticate with a Vanta OAuth application's Client ID + "
                "Client Secret (machine-to-machine client_credentials grant). "
                "The tool exchanges them for a short-lived access token on each "
                "request. Evidence uploads require the "
                "vanta-api.documents:upload scope."
            ),
            setup_instructions=[
                "Sign in to Vanta as an administrator",
                "Go to Settings -> Developer Console and create an API application",
                "Copy the generated Client ID and Client Secret (the Secret is shown only once)",
                (
                    "Grant the application the read scopes (and the "
                    "documents:upload / write scopes if you need evidence upload "
                    "or document submission)"
                ),
                "Choose your region: 'us' (api.vanta.com, default) or 'gov' (api.vanta-gov.com)",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="VANTA_CLIENT_ID",
                    display_name="Client ID",
                    description="Vanta OAuth application client ID",
                    required=True,
                    sensitive=False,
                    inject_into_auth_data=True,
                    about_url="https://developer.vanta.com/docs/api-access-setup",
                ),
                EnvVar(
                    name="VANTA_CLIENT_SECRET",
                    display_name="Client Secret",
                    description=(
                        "Vanta OAuth application client secret (shown only once "
                        "at creation)"
                    ),
                    required=True,
                    sensitive=True,
                    inject_into_auth_data=True,
                    about_url="https://developer.vanta.com/docs/api-access-setup",
                ),
                EnvVar(
                    name="VANTA_REGION",
                    display_name="Region",
                    description=(
                        'Vanta API region: "us" (api.vanta.com, default) or '
                        '"gov" (api.vanta-gov.com)'
                    ),
                    required=False,
                    sensitive=False,
                    inject_into_auth_data=True,
                    sample_format="us",
                    about_url="https://developer.vanta.com/docs/vanta-api-overview",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.vanta.com/v1/frameworks",
                method="GET",
                params={"pageSize": "1"},
                # The runtime cannot mint the client_credentials access token
                # for a header placeholder, so this endpoint only confirms the
                # host is reachable; full credential validation happens on the
                # first real action call via the in-tool token exchange.
                success_indicators=SuccessIndicators(
                    status_codes=[200, 401],
                ),
                cost_level="free",
                description="Confirms the Vanta API host is reachable",
            ),
        ),
    ],
)
