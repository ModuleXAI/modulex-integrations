"""Vanta LangChain @tool functions.

Authentication is a machine-to-machine OAuth2 ``client_credentials`` grant.
Each tool exchanges the application's Client ID + Client Secret for a
short-lived bearer token (``POST /oauth/token``) and then calls the Vanta v1
REST API with ``Authorization: Bearer <access_token>``. The credential fields
(``client_id``, ``client_secret``, ``region``) arrive in ``auth_data`` via the
manifest's ``inject_into_auth_data`` EnvVars.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.vanta.outputs import (
    Control,
    ControlDetail,
    Document,
    DocumentDetail,
    DownloadDocumentFileOutput,
    Framework,
    FrameworkDetail,
    GetControlOutput,
    GetDocumentOutput,
    GetFrameworkOutput,
    GetPersonOutput,
    GetPolicyOutput,
    GetRiskScenarioOutput,
    GetTestOutput,
    GetVendorOutput,
    GetVulnerableAssetOutput,
    ListControlDocumentsOutput,
    ListControlsOutput,
    ListControlTestsOutput,
    ListDocumentsOutput,
    ListDocumentUploadsOutput,
    ListFrameworkControlsOutput,
    ListFrameworksOutput,
    ListMonitoredComputersOutput,
    ListPeopleOutput,
    ListPoliciesOutput,
    ListRiskScenariosOutput,
    ListTestEntitiesOutput,
    ListTestsOutput,
    ListVendorsOutput,
    ListVulnerabilitiesOutput,
    ListVulnerabilityRemediationsOutput,
    ListVulnerableAssetsOutput,
    MonitoredComputer,
    PageInfo,
    Person,
    Policy,
    RiskScenario,
    SubmitDocumentOutput,
    Test,
    TestEntity,
    UploadDocumentFileOutput,
    UploadedFile,
    Vendor,
    Vulnerability,
    VulnerabilityRemediation,
    VulnerableAsset,
)

__all__ = [
    "download_document_file",
    "get_control",
    "get_document",
    "get_framework",
    "get_person",
    "get_policy",
    "get_risk_scenario",
    "get_test",
    "get_vendor",
    "get_vulnerable_asset",
    "list_control_documents",
    "list_control_tests",
    "list_controls",
    "list_document_uploads",
    "list_documents",
    "list_framework_controls",
    "list_frameworks",
    "list_monitored_computers",
    "list_people",
    "list_policies",
    "list_risk_scenarios",
    "list_test_entities",
    "list_tests",
    "list_vendors",
    "list_vulnerabilities",
    "list_vulnerability_remediations",
    "list_vulnerable_assets",
    "submit_document",
    "upload_document_file",
]

_TIMEOUT = 30.0

_REGION_HOSTS: dict[str, str] = {
    "us": "https://api.vanta.com",
    "gov": "https://api.vanta-gov.com",
}

# Scopes taken verbatim from Vanta's API access docs. The read scope covers
# every query operation; the upload scope is required by the documents upload
# endpoint and cannot be requested alone.
_READ_SCOPE = "vanta-api.all:read"
_DOCUMENT_UPLOAD_SCOPE = (
    "vanta-api.all:read vanta-api.all:write vanta-api.documents:upload"
)
_WRITE_SCOPE = "vanta-api.all:read vanta-api.all:write"


# --- Auth / request plumbing ---------------------------------------------


def _base_host(auth_data: dict[str, Any]) -> str:
    """Return the region-specific Vanta API host (no trailing slash)."""
    region = (auth_data.get("region") or "us").strip().lower()
    return _REGION_HOSTS.get(region, _REGION_HOSTS["us"])


def _base_url(auth_data: dict[str, Any]) -> str:
    """Return the region-specific Vanta v1 REST base URL."""
    return f"{_base_host(auth_data)}/v1"


def _missing_credentials(auth_data: dict[str, Any]) -> bool:
    """True when either OAuth client credential is absent."""
    return not (auth_data.get("client_id") and auth_data.get("client_secret"))


async def _get_access_token(
    auth_data: dict[str, Any], client: httpx.AsyncClient, scope: str
) -> str:
    """Exchange client credentials for a bearer access token.

    Raises ``RuntimeError`` with a human-readable message on failure so the
    calling tool can surface it as ``success=False``.
    """
    token_url = f"{_base_host(auth_data)}/oauth/token"
    # Vanta's /oauth/token expects a JSON body (it does not accept
    # form-encoded bodies).
    payload: dict[str, Any] = {
        "grant_type": "client_credentials",
        "client_id": auth_data.get("client_id"),
        "client_secret": auth_data.get("client_secret"),
        "scope": scope,
    }
    response = await client.post(
        token_url,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        json=payload,
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Vanta authentication failed ({response.status_code}): {response.text}"
        )
    data = response.json()
    token = data.get("access_token")
    if not token or not isinstance(token, str):
        raise RuntimeError("Vanta authentication did not return an access token.")
    return token


def _query(**kwargs: Any) -> dict[str, Any]:
    """Drop ``None``/empty values; split comma lists into repeated params."""
    params: dict[str, Any] = {}
    for key, value in kwargs.items():
        if value is None or value == "":
            continue
        if isinstance(value, bool):
            params[key] = str(value).lower()
        elif isinstance(value, str) and key.endswith("MatchesAny"):
            entries = [entry.strip() for entry in value.split(",") if entry.strip()]
            if entries:
                params[key] = entries
        else:
            params[key] = value
    return params


def _page_info(results: dict[str, Any]) -> PageInfo | None:
    raw = results.get("pageInfo")
    if not isinstance(raw, dict):
        return None
    return PageInfo(
        start_cursor=raw.get("startCursor"),
        end_cursor=raw.get("endCursor"),
        has_next_page=raw.get("hasNextPage"),
        has_previous_page=raw.get("hasPreviousPage"),
    )


async def _fetch_list(
    auth_data: dict[str, Any],
    path: str,
    query: dict[str, Any],
    page_size: int | None,
    page_cursor: str | None,
    max_pages: int,
    scope: str = _READ_SCOPE,
) -> tuple[list[dict[str, Any]], PageInfo | None]:
    """Run a cursor-paginated GET, bounded by ``max_pages``.

    Returns ``(rows, page_info_of_last_page)``. Raises ``RuntimeError`` on a
    non-2xx response so the caller can map it to ``success=False``.
    """
    rows: list[dict[str, Any]] = []
    last_page_info: PageInfo | None = None
    cursor = page_cursor
    pages = max(1, max_pages)

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        token = await _get_access_token(auth_data, client, scope)
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        for _ in range(pages):
            params: dict[str, Any] = dict(query)
            if page_size is not None:
                params["pageSize"] = page_size
            if cursor:
                params["pageCursor"] = cursor
            response = await client.get(
                f"{_base_url(auth_data)}{path}", headers=headers, params=params
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Vanta API error ({response.status_code}): {response.text}"
                )
            results = response.json().get("results", {})
            data = results.get("data")
            if isinstance(data, list):
                rows.extend(item for item in data if isinstance(item, dict))
            last_page_info = _page_info(results)
            if last_page_info is None or not last_page_info.has_next_page:
                break
            cursor = last_page_info.end_cursor
            if not cursor:
                break
    return rows, last_page_info


async def _fetch_one(
    auth_data: dict[str, Any], path: str, scope: str = _READ_SCOPE
) -> dict[str, Any]:
    """Run a single-resource GET. Raises ``RuntimeError`` on non-2xx."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        token = await _get_access_token(auth_data, client, scope)
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        response = await client.get(f"{_base_url(auth_data)}{path}", headers=headers)
        if response.status_code != 200:
            raise RuntimeError(
                f"Vanta API error ({response.status_code}): {response.text}"
            )
        body = response.json()
    return body if isinstance(body, dict) else {}


# --- Resource normalizers (camelCase JSON -> snake_case models) ----------


def _str_list(value: Any) -> list[str]:
    """Coerce an unknown value into a list of strings (drops non-strings)."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _owner(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    return {
        "id": raw.get("id"),
        "display_name": raw.get("displayName"),
        "email_address": raw.get("emailAddress"),
    }


def _framework(raw: dict[str, Any]) -> Framework:
    return Framework(
        id=raw.get("id"),
        display_name=raw.get("displayName"),
        shorthand_name=raw.get("shorthandName"),
        description=raw.get("description"),
        num_controls_completed=raw.get("numControlsCompleted"),
        num_controls_total=raw.get("numControlsTotal"),
        num_documents_passing=raw.get("numDocumentsPassing"),
        num_documents_total=raw.get("numDocumentsTotal"),
        num_tests_passing=raw.get("numTestsPassing"),
        num_tests_total=raw.get("numTestsTotal"),
    )


def _framework_detail(raw: dict[str, Any]) -> FrameworkDetail:
    base = _framework(raw).model_dump()
    cats = raw.get("requirementCategories")
    base["requirement_categories"] = cats if isinstance(cats, list) else []
    return FrameworkDetail(**base)


def _control(raw: dict[str, Any]) -> Control:
    domains = raw.get("domains")
    custom = raw.get("customFields")
    return Control(
        id=raw.get("id"),
        external_id=raw.get("externalId"),
        name=raw.get("name"),
        description=raw.get("description"),
        source=raw.get("source"),
        domains=domains if isinstance(domains, list) else [],
        owner=_owner(raw.get("owner")),  # type: ignore[arg-type]
        role=raw.get("role"),
        custom_fields=custom if isinstance(custom, list) else [],
        creation_date=raw.get("creationDate"),
        modification_date=raw.get("modificationDate"),
    )


def _control_detail(raw: dict[str, Any]) -> ControlDetail:
    base = _control(raw).model_dump()
    base.update(
        note=raw.get("note"),
        status=raw.get("status"),
        num_documents_passing=raw.get("numDocumentsPassing"),
        num_documents_total=raw.get("numDocumentsTotal"),
        num_tests_passing=raw.get("numTestsPassing"),
        num_tests_total=raw.get("numTestsTotal"),
    )
    return ControlDetail(**base)


def _test(raw: dict[str, Any]) -> Test:
    integrations = raw.get("integrations")
    return Test(
        id=raw.get("id"),
        name=raw.get("name"),
        description=raw.get("description"),
        failure_description=raw.get("failureDescription"),
        remediation_description=raw.get("remediationDescription"),
        category=raw.get("category"),
        status=raw.get("status"),
        integrations=integrations if isinstance(integrations, list) else [],
        last_test_run_date=raw.get("lastTestRunDate"),
        latest_flip_date=raw.get("latestFlipDate"),
        version=raw.get("version") if isinstance(raw.get("version"), dict) else None,
        deactivated_status_info=raw.get("deactivatedStatusInfo")
        if isinstance(raw.get("deactivatedStatusInfo"), dict)
        else None,
        remediation_status_info=raw.get("remediationStatusInfo")
        if isinstance(raw.get("remediationStatusInfo"), dict)
        else None,
        owner=_owner(raw.get("owner")),  # type: ignore[arg-type]
    )


def _test_entity(raw: dict[str, Any]) -> TestEntity:
    return TestEntity(
        id=raw.get("id"),
        entity_status=raw.get("entityStatus"),
        display_name=raw.get("displayName"),
        response_type=raw.get("responseType"),
        deactivated_reason=raw.get("deactivatedReason"),
        created_date=raw.get("createdDate"),
        last_updated_date=raw.get("lastUpdatedDate"),
    )


def _document(raw: dict[str, Any]) -> Document:
    return Document(
        id=raw.get("id"),
        title=raw.get("title"),
        description=raw.get("description"),
        category=raw.get("category"),
        owner_id=raw.get("ownerId"),
        is_sensitive=raw.get("isSensitive"),
        upload_status=raw.get("uploadStatus"),
        upload_status_date=raw.get("uploadStatusDate"),
        url=raw.get("url"),
    )


def _document_detail(raw: dict[str, Any]) -> DocumentDetail:
    base = _document(raw).model_dump()
    subs = raw.get("subscribers")
    base.update(
        note=raw.get("note"),
        next_renewal_date=raw.get("nextRenewalDate"),
        renewal_cadence=raw.get("renewalCadence"),
        reminder_window=raw.get("reminderWindow"),
        subscribers=subs if isinstance(subs, list) else [],
        deactivated_status=raw.get("deactivatedStatus")
        if isinstance(raw.get("deactivatedStatus"), dict)
        else None,
    )
    return DocumentDetail(**base)


def _uploaded_file(raw: dict[str, Any]) -> UploadedFile:
    return UploadedFile(
        id=raw.get("id"),
        file_name=raw.get("fileName"),
        title=raw.get("title"),
        description=raw.get("description"),
        mime_type=raw.get("mimeType"),
        uploaded_by=raw.get("uploadedBy")
        if isinstance(raw.get("uploadedBy"), dict)
        else None,
        creation_date=raw.get("creationDate"),
        updated_date=raw.get("updatedDate"),
        deletion_date=raw.get("deletionDate"),
        effective_date=raw.get("effectiveDate"),
        url=raw.get("url"),
    )


def _person(raw: dict[str, Any]) -> Person:
    groups = raw.get("groupIds")
    return Person(
        id=raw.get("id"),
        user_id=raw.get("userId"),
        email_address=raw.get("emailAddress"),
        name=raw.get("name") if isinstance(raw.get("name"), dict) else None,
        employment=raw.get("employment")
        if isinstance(raw.get("employment"), dict)
        else None,
        leave_info=raw.get("leaveInfo")
        if isinstance(raw.get("leaveInfo"), dict)
        else None,
        group_ids=groups if isinstance(groups, list) else [],
        tasks_summary=raw.get("tasksSummary")
        if isinstance(raw.get("tasksSummary"), dict)
        else None,
    )


def _policy(raw: dict[str, Any]) -> Policy:
    latest_version = raw.get("latestVersion")
    return Policy(
        id=raw.get("id"),
        name=raw.get("name"),
        description=raw.get("description"),
        status=raw.get("status"),
        approved_at_date=raw.get("approvedAtDate"),
        latest_version_status=latest_version.get("status")
        if isinstance(latest_version, dict)
        else None,
        latest_approved_version=raw.get("latestApprovedVersion")
        if isinstance(raw.get("latestApprovedVersion"), dict)
        else None,
    )


def _vendor(raw: dict[str, Any]) -> Vendor:
    category = raw.get("category")
    risk_ids = raw.get("riskAttributeIds")
    custom = raw.get("customFields")
    return Vendor(
        id=raw.get("id"),
        name=raw.get("name"),
        status=raw.get("status"),
        website_url=raw.get("websiteUrl"),
        category=category.get("displayName") if isinstance(category, dict) else None,
        services_provided=raw.get("servicesProvided"),
        additional_notes=raw.get("additionalNotes"),
        account_manager_name=raw.get("accountManagerName"),
        account_manager_email=raw.get("accountManagerEmail"),
        security_owner_user_id=raw.get("securityOwnerUserId"),
        business_owner_user_id=raw.get("businessOwnerUserId"),
        inherent_risk_level=raw.get("inherentRiskLevel"),
        residual_risk_level=raw.get("residualRiskLevel"),
        is_risk_auto_scored=raw.get("isRiskAutoScored"),
        is_visible_to_auditors=raw.get("isVisibleToAuditors"),
        risk_attribute_ids=risk_ids if isinstance(risk_ids, list) else [],
        vendor_headquarters=raw.get("vendorHeadquarters"),
        contract_start_date=raw.get("contractStartDate"),
        contract_renewal_date=raw.get("contractRenewalDate"),
        contract_termination_date=raw.get("contractTerminationDate"),
        contract_amount=raw.get("contractAmount")
        if isinstance(raw.get("contractAmount"), dict)
        else None,
        next_security_review_due_date=raw.get("nextSecurityReviewDueDate"),
        last_security_review_completion_date=raw.get("lastSecurityReviewCompletionDate"),
        auth_details=raw.get("authDetails")
        if isinstance(raw.get("authDetails"), dict)
        else None,
        custom_fields=custom if isinstance(custom, list) else [],
        latest_decision=raw.get("latestDecision")
        if isinstance(raw.get("latestDecision"), dict)
        else None,
        linked_task_tracker_task_procurement_request=raw.get(
            "linkedTaskTrackerTaskProcurementRequest"
        )
        if isinstance(raw.get("linkedTaskTrackerTaskProcurementRequest"), dict)
        else None,
    )


def _monitored_computer(raw: dict[str, Any]) -> MonitoredComputer:
    def _outcome(value: Any) -> str | None:
        return value.get("outcome") if isinstance(value, dict) else None

    return MonitoredComputer(
        id=raw.get("id"),
        integration_id=raw.get("integrationId"),
        last_check_date=raw.get("lastCheckDate"),
        screenlock=_outcome(raw.get("screenlock")),
        disk_encryption=_outcome(raw.get("diskEncryption")),
        password_manager=_outcome(raw.get("passwordManager")),
        antivirus_installation=_outcome(raw.get("antivirusInstallation")),
        operating_system=raw.get("operatingSystem")
        if isinstance(raw.get("operatingSystem"), dict)
        else None,
        owner=_owner(raw.get("owner")),  # type: ignore[arg-type]
        serial_number=raw.get("serialNumber"),
        udid=raw.get("udid"),
    )


def _risk_scenario(raw: dict[str, Any]) -> RiskScenario:
    custom = raw.get("customFields")
    return RiskScenario(
        risk_id=raw.get("riskId"),
        description=raw.get("description"),
        likelihood=raw.get("likelihood"),
        impact=raw.get("impact"),
        residual_likelihood=raw.get("residualLikelihood"),
        residual_impact=raw.get("residualImpact"),
        categories=_str_list(raw.get("categories")),
        cia_categories=_str_list(raw.get("ciaCategories")),
        treatment=raw.get("treatment"),
        owner=raw.get("owner") if isinstance(raw.get("owner"), str) else None,
        note=raw.get("note"),
        risk_register=raw.get("riskRegister"),
        custom_fields=custom if isinstance(custom, list) else [],
        is_archived=raw.get("isArchived"),
        review_status=raw.get("reviewStatus"),
        required_approvers=_str_list(raw.get("requiredApprovers")),
        type=raw.get("type"),
        identification_date=raw.get("identificationDate"),
    )


def _vulnerability(raw: dict[str, Any]) -> Vulnerability:
    return Vulnerability(
        id=raw.get("id"),
        name=raw.get("name"),
        description=raw.get("description"),
        severity=raw.get("severity"),
        vulnerability_type=raw.get("vulnerabilityType"),
        integration_id=raw.get("integrationId"),
        target_id=raw.get("targetId"),
        package_identifier=raw.get("packageIdentifier"),
        cvss_severity_score=raw.get("cvssSeverityScore"),
        scanner_score=raw.get("scannerScore"),
        is_fixable=raw.get("isFixable"),
        fixed_version=raw.get("fixedVersion"),
        remediate_by_date=raw.get("remediateByDate"),
        first_detected_date=raw.get("firstDetectedDate"),
        source_detected_date=raw.get("sourceDetectedDate"),
        last_detected_date=raw.get("lastDetectedDate"),
        scan_source=raw.get("scanSource"),
        external_url=raw.get("externalURL"),
        related_vulns=_str_list(raw.get("relatedVulns")),
        related_urls=_str_list(raw.get("relatedUrls")),
        deactivate_metadata=raw.get("deactivateMetadata")
        if isinstance(raw.get("deactivateMetadata"), dict)
        else None,
    )


def _vulnerability_remediation(raw: dict[str, Any]) -> VulnerabilityRemediation:
    return VulnerabilityRemediation(
        id=raw.get("id"),
        vulnerability_id=raw.get("vulnerabilityId"),
        vulnerable_asset_id=raw.get("vulnerableAssetId"),
        severity=raw.get("severity"),
        detected_date=raw.get("detectedDate"),
        sla_deadline_date=raw.get("slaDeadlineDate"),
        remediation_date=raw.get("remediationDate"),
    )


def _vulnerable_asset(raw: dict[str, Any]) -> VulnerableAsset:
    scanners = raw.get("scanners")
    return VulnerableAsset(
        id=raw.get("id"),
        name=raw.get("name"),
        asset_type=raw.get("assetType"),
        has_been_scanned=raw.get("hasBeenScanned"),
        image_scan_tag=raw.get("imageScanTag"),
        scanners=scanners if isinstance(scanners, list) else [],
    )


# --- Input schemas --------------------------------------------------------


class _PaginatedInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    page_size: int | None = Field(
        default=None,
        description="Maximum number of items per page (1-100)",
    )
    page_cursor: str | None = Field(
        default=None,
        description="Pagination cursor from a previous response",
    )
    max_pages: int = Field(
        default=1,
        description="Maximum number of pages to fetch when auto-paginating",
    )


class ListFrameworksInput(_PaginatedInput):
    pass


class GetFrameworkInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    framework_id: str = Field(description="Unique ID of the framework (e.g., soc2)")


class ListFrameworkControlsInput(_PaginatedInput):
    framework_id: str = Field(description="Unique ID of the framework (e.g., soc2)")


class ListControlsInput(_PaginatedInput):
    framework_matches_any: str | None = Field(
        default=None,
        description="Comma-separated framework IDs to filter by",
    )


class GetControlInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    control_id: str = Field(description="Unique ID of the control")


class ListControlTestsInput(_PaginatedInput):
    control_id: str = Field(description="Unique ID of the control")


class ListControlDocumentsInput(_PaginatedInput):
    control_id: str = Field(description="Unique ID of the control")


class ListTestsInput(_PaginatedInput):
    status_filter: str | None = Field(default=None, description="Filter by test status")
    framework_filter: str | None = Field(default=None, description="Filter by framework ID")
    integration_filter: str | None = Field(default=None, description="Filter by integration ID")
    control_filter: str | None = Field(default=None, description="Filter by control ID")
    owner_filter: str | None = Field(default=None, description="Filter by owner user ID")
    category_filter: str | None = Field(default=None, description="Filter by test category")
    is_in_rollout: bool | None = Field(
        default=None,
        description="Filter by whether the test is in rollout",
    )


class GetTestInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    test_id: str = Field(description="Unique ID of the test")


class ListTestEntitiesInput(_PaginatedInput):
    test_id: str = Field(description="Unique ID of the test")
    entity_status: str | None = Field(
        default=None,
        description="Filter entities by status: FAILING or DEACTIVATED",
    )


class ListDocumentsInput(_PaginatedInput):
    framework_matches_any: str | None = Field(
        default=None,
        description="Comma-separated framework IDs to filter by",
    )
    status_matches_any: str | None = Field(
        default=None,
        description="Comma-separated document statuses to filter by",
    )


class GetDocumentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    document_id: str = Field(description="Unique ID of the document")


class ListDocumentUploadsInput(_PaginatedInput):
    document_id: str = Field(description="Unique ID of the document")


class UploadDocumentFileInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    document_id: str = Field(description="Unique ID of the document to attach the file to")
    file_content: str = Field(description="Base64-encoded content of the evidence file")
    file_name: str = Field(description="File name for the upload")
    mime_type: str | None = Field(
        default=None,
        description="MIME type of the file (e.g., application/pdf)",
    )
    description: str | None = Field(
        default=None,
        description="Description of the uploaded evidence",
    )
    effective_at_date: str | None = Field(default=None, description="ISO 8601 effective date")


class DownloadDocumentFileInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    document_id: str = Field(description="Unique ID of the document")
    uploaded_file_id: str = Field(
        description="Unique ID of the uploaded file (from list_document_uploads)",
    )


class SubmitDocumentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    document_id: str = Field(description="Unique ID of the document to submit")


class ListPeopleInput(_PaginatedInput):
    email_and_name_filter: str | None = Field(
        default=None,
        description="Filter people by email address or name",
    )
    employment_status: str | None = Field(default=None, description="Filter by employment status")
    group_ids_matches_any: str | None = Field(default=None, description="Comma-separated group IDs")
    tasks_summary_status_matches_any: str | None = Field(
        default=None,
        description="Comma-separated task summary statuses",
    )
    task_type_matches_any: str | None = Field(
        default=None,
        description="Comma-separated task types",
    )
    task_status_matches_any: str | None = Field(
        default=None,
        description="Comma-separated task statuses",
    )


class GetPersonInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    person_id: str = Field(description="Unique ID of the person")


class ListPoliciesInput(_PaginatedInput):
    pass


class GetPolicyInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    policy_id: str = Field(description="Unique ID of the policy")


class ListVendorsInput(_PaginatedInput):
    name: str | None = Field(default=None, description="Filter vendors by name")
    status_matches_any: str | None = Field(
        default=None,
        description="Comma-separated vendor statuses",
    )


class GetVendorInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    vendor_id: str = Field(description="Unique ID of the vendor")


class ListMonitoredComputersInput(_PaginatedInput):
    compliance_status_filter_matches_any: str | None = Field(
        default=None, description="Comma-separated compliance issues to filter by"
    )


class ListVulnerabilitiesInput(_PaginatedInput):
    q: str | None = Field(default=None, description="Search query for vulnerabilities")
    severity: str | None = Field(default=None, description="Filter by severity")
    is_fix_available: bool | None = Field(
        default=None,
        description="Filter by whether a fix is available",
    )
    is_deactivated: bool | None = Field(
        default=None,
        description="Filter by whether monitoring is deactivated",
    )
    include_vulnerabilities_without_slas: bool | None = Field(
        default=None, description="Include vulnerabilities without an SLA deadline"
    )
    package_identifier: str | None = Field(
        default=None,
        description="Filter by affected package identifier",
    )
    external_vulnerability_id: str | None = Field(
        default=None,
        description="Filter by external vulnerability ID",
    )
    integration_id: str | None = Field(
        default=None,
        description="Filter by integration that detected it",
    )
    vulnerable_asset_id: str | None = Field(
        default=None,
        description="Filter by vulnerable asset ID",
    )
    sla_deadline_after_date: str | None = Field(
        default=None,
        description="SLA deadline after this ISO 8601 date",
    )
    sla_deadline_before_date: str | None = Field(
        default=None,
        description="SLA deadline before this ISO 8601 date",
    )


class ListVulnerabilityRemediationsInput(_PaginatedInput):
    integration_id: str | None = Field(
        default=None,
        description="Filter by integration that detected it",
    )
    severity: str | None = Field(default=None, description="Filter by severity")
    is_remediated_on_time: bool | None = Field(
        default=None,
        description="Filter by on-time remediation",
    )
    remediated_after_date: str | None = Field(
        default=None,
        description="Remediated after this ISO 8601 date",
    )
    remediated_before_date: str | None = Field(
        default=None,
        description="Remediated before this ISO 8601 date",
    )


class ListVulnerableAssetsInput(_PaginatedInput):
    q: str | None = Field(default=None, description="Search query for vulnerable assets")
    integration_id: str | None = Field(
        default=None,
        description="Filter by integration scanning the asset",
    )
    asset_type: str | None = Field(default=None, description="Filter by asset type")
    asset_external_account_id: str | None = Field(
        default=None,
        description="Filter by external account ID",
    )


class GetVulnerableAssetInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    vulnerable_asset_id: str = Field(description="Unique ID of the vulnerable asset")


class ListRiskScenariosInput(_PaginatedInput):
    search_string: str | None = Field(
        default=None,
        description="Search string to filter risk scenarios",
    )
    include_ignored: bool | None = Field(default=None, description="Include ignored risk scenarios")
    type: str | None = Field(default=None, description="Filter by scenario type")
    owner_matches_any: str | None = Field(default=None, description="Comma-separated owner emails")
    category_matches_any: str | None = Field(
        default=None,
        description="Comma-separated risk categories",
    )
    cia_category_matches_any: str | None = Field(
        default=None,
        description="Comma-separated CIA categories",
    )
    treatment_type_matches_any: str | None = Field(
        default=None,
        description="Comma-separated treatments",
    )
    inherent_score_group_matches_any: str | None = Field(
        default=None,
        description="Comma-separated inherent score groups",
    )
    residual_score_group_matches_any: str | None = Field(
        default=None,
        description="Comma-separated residual score groups",
    )
    review_status_matches_any: str | None = Field(
        default=None,
        description="Comma-separated review statuses",
    )
    order_by: str | None = Field(
        default=None,
        description="Field to order by: description or createdAt",
    )


class GetRiskScenarioInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    risk_scenario_id: str = Field(description="Unique ID of the risk scenario")


# --- @tool functions ------------------------------------------------------

_MISSING = "Missing Vanta credentials (client_id, client_secret) in auth_data."


@tool(args_schema=ListFrameworksInput)
@serialize_pydantic_return
async def list_frameworks(
    auth_type: str,
    auth_data: dict[str, Any],
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListFrameworksOutput:
    """List the compliance frameworks available in a Vanta account with completion counts."""
    if _missing_credentials(auth_data):
        return ListFrameworksOutput(success=False, error=_MISSING)
    try:
        rows, page = await _fetch_list(
            auth_data, "/frameworks", {}, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListFrameworksOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFrameworksOutput(success=False, error=str(exc))
    return ListFrameworksOutput(
        success=True, frameworks=[_framework(r) for r in rows], page_info=page
    )


@tool(args_schema=GetFrameworkInput)
@serialize_pydantic_return
async def get_framework(
    auth_type: str, auth_data: dict[str, Any], framework_id: str
) -> GetFrameworkOutput:
    """Get a Vanta compliance framework by ID, including its requirement categories and mapped
    controls.
    """
    if _missing_credentials(auth_data):
        return GetFrameworkOutput(success=False, error=_MISSING)
    try:
        body = await _fetch_one(auth_data, f"/frameworks/{framework_id}")
    except httpx.TimeoutException:
        return GetFrameworkOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetFrameworkOutput(success=False, error=str(exc))
    return GetFrameworkOutput(success=True, framework=_framework_detail(body))


@tool(args_schema=ListFrameworkControlsInput)
@serialize_pydantic_return
async def list_framework_controls(
    auth_type: str,
    auth_data: dict[str, Any],
    framework_id: str,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListFrameworkControlsOutput:
    """List the controls that belong to a specific Vanta compliance framework."""
    if _missing_credentials(auth_data):
        return ListFrameworkControlsOutput(success=False, error=_MISSING)
    try:
        rows, page = await _fetch_list(
            auth_data,
            f"/frameworks/{framework_id}/controls",
            {},
            page_size,
            page_cursor,
            max_pages,
        )
    except httpx.TimeoutException:
        return ListFrameworkControlsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFrameworkControlsOutput(success=False, error=str(exc))
    return ListFrameworkControlsOutput(
        success=True, controls=[_control(r) for r in rows], page_info=page
    )


@tool(args_schema=ListControlsInput)
@serialize_pydantic_return
async def list_controls(
    auth_type: str,
    auth_data: dict[str, Any],
    framework_matches_any: str | None = None,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListControlsOutput:
    """List the security controls in a Vanta account, optionally filtered by framework."""
    if _missing_credentials(auth_data):
        return ListControlsOutput(success=False, error=_MISSING)
    query = _query(frameworkMatchesAny=framework_matches_any)
    try:
        rows, page = await _fetch_list(
            auth_data, "/controls", query, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListControlsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListControlsOutput(success=False, error=str(exc))
    return ListControlsOutput(
        success=True, controls=[_control(r) for r in rows], page_info=page
    )


@tool(args_schema=GetControlInput)
@serialize_pydantic_return
async def get_control(
    auth_type: str, auth_data: dict[str, Any], control_id: str
) -> GetControlOutput:
    """Get a Vanta security control by ID, including its status and evidence pass/fail counts."""
    if _missing_credentials(auth_data):
        return GetControlOutput(success=False, error=_MISSING)
    try:
        body = await _fetch_one(auth_data, f"/controls/{control_id}")
    except httpx.TimeoutException:
        return GetControlOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetControlOutput(success=False, error=str(exc))
    return GetControlOutput(success=True, control=_control_detail(body))


@tool(args_schema=ListControlTestsInput)
@serialize_pydantic_return
async def list_control_tests(
    auth_type: str,
    auth_data: dict[str, Any],
    control_id: str,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListControlTestsOutput:
    """List the automated tests mapped to a specific Vanta control."""
    if _missing_credentials(auth_data):
        return ListControlTestsOutput(success=False, error=_MISSING)
    try:
        rows, page = await _fetch_list(
            auth_data, f"/controls/{control_id}/tests", {}, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListControlTestsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListControlTestsOutput(success=False, error=str(exc))
    return ListControlTestsOutput(
        success=True, tests=[_test(r) for r in rows], page_info=page
    )


@tool(args_schema=ListControlDocumentsInput)
@serialize_pydantic_return
async def list_control_documents(
    auth_type: str,
    auth_data: dict[str, Any],
    control_id: str,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListControlDocumentsOutput:
    """List the evidence documents mapped to a specific Vanta control."""
    if _missing_credentials(auth_data):
        return ListControlDocumentsOutput(success=False, error=_MISSING)
    try:
        rows, page = await _fetch_list(
            auth_data,
            f"/controls/{control_id}/documents",
            {},
            page_size,
            page_cursor,
            max_pages,
        )
    except httpx.TimeoutException:
        return ListControlDocumentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListControlDocumentsOutput(success=False, error=str(exc))
    return ListControlDocumentsOutput(
        success=True, documents=[_document(r) for r in rows], page_info=page
    )


@tool(args_schema=ListTestsInput)
@serialize_pydantic_return
async def list_tests(
    auth_type: str,
    auth_data: dict[str, Any],
    status_filter: str | None = None,
    framework_filter: str | None = None,
    integration_filter: str | None = None,
    control_filter: str | None = None,
    owner_filter: str | None = None,
    category_filter: str | None = None,
    is_in_rollout: bool | None = None,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListTestsOutput:
    """List the automated compliance tests in a Vanta account, with filters."""
    if _missing_credentials(auth_data):
        return ListTestsOutput(success=False, error=_MISSING)
    query = _query(
        statusFilter=status_filter,
        frameworkFilter=framework_filter,
        integrationFilter=integration_filter,
        controlFilter=control_filter,
        ownerFilter=owner_filter,
        categoryFilter=category_filter,
        isInRollout=is_in_rollout,
    )
    try:
        rows, page = await _fetch_list(
            auth_data, "/tests", query, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListTestsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTestsOutput(success=False, error=str(exc))
    return ListTestsOutput(success=True, tests=[_test(r) for r in rows], page_info=page)


@tool(args_schema=GetTestInput)
@serialize_pydantic_return
async def get_test(
    auth_type: str, auth_data: dict[str, Any], test_id: str
) -> GetTestOutput:
    """Get a Vanta automated compliance test by ID, including its status and remediation info."""
    if _missing_credentials(auth_data):
        return GetTestOutput(success=False, error=_MISSING)
    try:
        body = await _fetch_one(auth_data, f"/tests/{test_id}")
    except httpx.TimeoutException:
        return GetTestOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetTestOutput(success=False, error=str(exc))
    return GetTestOutput(success=True, test=_test(body))


@tool(args_schema=ListTestEntitiesInput)
@serialize_pydantic_return
async def list_test_entities(
    auth_type: str,
    auth_data: dict[str, Any],
    test_id: str,
    entity_status: str | None = None,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListTestEntitiesOutput:
    """List the failing or deactivated resource entities for a specific Vanta test."""
    if _missing_credentials(auth_data):
        return ListTestEntitiesOutput(success=False, error=_MISSING)
    query = _query(entityStatus=entity_status)
    try:
        rows, page = await _fetch_list(
            auth_data, f"/tests/{test_id}/entities", query, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListTestEntitiesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTestEntitiesOutput(success=False, error=str(exc))
    return ListTestEntitiesOutput(
        success=True, entities=[_test_entity(r) for r in rows], page_info=page
    )


@tool(args_schema=ListDocumentsInput)
@serialize_pydantic_return
async def list_documents(
    auth_type: str,
    auth_data: dict[str, Any],
    framework_matches_any: str | None = None,
    status_matches_any: str | None = None,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListDocumentsOutput:
    """List the evidence documents in a Vanta account, optionally filtered by framework or status.
    """
    if _missing_credentials(auth_data):
        return ListDocumentsOutput(success=False, error=_MISSING)
    query = _query(
        frameworkMatchesAny=framework_matches_any,
        statusMatchesAny=status_matches_any,
    )
    try:
        rows, page = await _fetch_list(
            auth_data, "/documents", query, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListDocumentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDocumentsOutput(success=False, error=str(exc))
    return ListDocumentsOutput(
        success=True, documents=[_document(r) for r in rows], page_info=page
    )


@tool(args_schema=GetDocumentInput)
@serialize_pydantic_return
async def get_document(
    auth_type: str, auth_data: dict[str, Any], document_id: str
) -> GetDocumentOutput:
    """Get a Vanta evidence document by ID, including its renewal schedule and deactivation status.
    """
    if _missing_credentials(auth_data):
        return GetDocumentOutput(success=False, error=_MISSING)
    try:
        body = await _fetch_one(auth_data, f"/documents/{document_id}")
    except httpx.TimeoutException:
        return GetDocumentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetDocumentOutput(success=False, error=str(exc))
    return GetDocumentOutput(success=True, document=_document_detail(body))


@tool(args_schema=ListDocumentUploadsInput)
@serialize_pydantic_return
async def list_document_uploads(
    auth_type: str,
    auth_data: dict[str, Any],
    document_id: str,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListDocumentUploadsOutput:
    """List the files uploaded to a specific Vanta evidence document."""
    if _missing_credentials(auth_data):
        return ListDocumentUploadsOutput(success=False, error=_MISSING)
    try:
        rows, page = await _fetch_list(
            auth_data,
            f"/documents/{document_id}/uploads",
            {},
            page_size,
            page_cursor,
            max_pages,
        )
    except httpx.TimeoutException:
        return ListDocumentUploadsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDocumentUploadsOutput(success=False, error=str(exc))
    return ListDocumentUploadsOutput(
        success=True, uploads=[_uploaded_file(r) for r in rows], page_info=page
    )


@tool(args_schema=UploadDocumentFileInput)
@serialize_pydantic_return
async def upload_document_file(
    auth_type: str,
    auth_data: dict[str, Any],
    document_id: str,
    file_content: str,
    file_name: str,
    mime_type: str | None = None,
    description: str | None = None,
    effective_at_date: str | None = None,
) -> UploadDocumentFileOutput:
    """Upload an evidence file (base64) to a Vanta document. Requires the documents:upload scope."""
    if _missing_credentials(auth_data):
        return UploadDocumentFileOutput(success=False, error=_MISSING)
    try:
        raw_bytes = base64.b64decode(file_content, validate=True)
    except Exception as exc:
        return UploadDocumentFileOutput(
            success=False, error=f"file_content is not valid base64: {exc}"
        )
    # TODO (unverified): Vanta's POST /v1/documents/{id}/uploads is
    # multipart/form-data with a binary ``file`` part plus optional
    # ``description`` and ``effectiveAtDate`` text parts per
    # developer.vanta.com (uploadfilefordocument); the exact text-part field
    # names beyond ``file`` are not fully documented.
    files: dict[str, Any] = {
        "file": (file_name, raw_bytes, mime_type or "application/octet-stream")
    }
    form: dict[str, Any] = {}
    if description is not None:
        form["description"] = description
    if effective_at_date is not None:
        form["effectiveAtDate"] = effective_at_date
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token = await _get_access_token(auth_data, client, _DOCUMENT_UPLOAD_SCOPE)
            response = await client.post(
                f"{_base_url(auth_data)}/documents/{document_id}/uploads",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                files=files,
                data=form,
            )
        if response.status_code not in (200, 201):
            return UploadDocumentFileOutput(
                success=False,
                error=f"Vanta API error ({response.status_code}): {response.text}",
            )
        body = response.json()
    except httpx.TimeoutException:
        return UploadDocumentFileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UploadDocumentFileOutput(success=False, error=str(exc))
    return UploadDocumentFileOutput(
        success=True, upload=_uploaded_file(body if isinstance(body, dict) else {})
    )


@tool(args_schema=DownloadDocumentFileInput)
@serialize_pydantic_return
async def download_document_file(
    auth_type: str,
    auth_data: dict[str, Any],
    document_id: str,
    uploaded_file_id: str,
) -> DownloadDocumentFileOutput:
    """Download a file previously uploaded to a Vanta evidence document.

    The file body is returned as base64 content so it stays JSON-serializable.
    """
    if _missing_credentials(auth_data):
        return DownloadDocumentFileOutput(success=False, error=_MISSING)
    # TODO (unverified): GET /v1/documents/{id}/uploads/{uploadId}/download
    # per developer.vanta.com (manage-vanta endpoint index). The exact
    # response shape (raw bytes vs a redirect to a signed URL) is not publicly
    # documented; this follows redirects and returns the bytes as base64 plus
    # the response Content-Type so the body stays JSON-serializable.
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True) as client:
            token = await _get_access_token(auth_data, client, _READ_SCOPE)
            response = await client.get(
                f"{_base_url(auth_data)}/documents/{document_id}"
                f"/uploads/{uploaded_file_id}/download",
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code != 200:
            return DownloadDocumentFileOutput(
                success=False,
                error=f"Vanta API error ({response.status_code}): {response.text}",
            )
        content = response.content
    except httpx.TimeoutException:
        return DownloadDocumentFileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DownloadDocumentFileOutput(success=False, error=str(exc))
    return DownloadDocumentFileOutput(
        success=True,
        name=uploaded_file_id,
        mime_type=response.headers.get("content-type"),
        size=len(content),
        data=base64.b64encode(content).decode("ascii"),
    )


@tool(args_schema=SubmitDocumentInput)
@serialize_pydantic_return
async def submit_document(
    auth_type: str, auth_data: dict[str, Any], document_id: str
) -> SubmitDocumentOutput:
    """Submit a Vanta document collection for review.

    Once submitted, uploaded evidence becomes visible to auditors.
    """
    if _missing_credentials(auth_data):
        return SubmitDocumentOutput(success=False, error=_MISSING)
    # TODO (unverified): POST /v1/documents/submit per developer.vanta.com
    # (manage-vanta endpoint index). The request body field carrying the
    # document id is assumed to be ``documentId``; confirm against the OpenAPI
    # spec.
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token = await _get_access_token(auth_data, client, _WRITE_SCOPE)
            response = await client.post(
                f"{_base_url(auth_data)}/documents/submit",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                json={"documentId": document_id},
            )
        if response.status_code not in (200, 201, 204):
            return SubmitDocumentOutput(
                success=False,
                error=f"Vanta API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return SubmitDocumentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SubmitDocumentOutput(success=False, error=str(exc))
    return SubmitDocumentOutput(success=True, document_id=document_id, submitted=True)


@tool(args_schema=ListPeopleInput)
@serialize_pydantic_return
async def list_people(
    auth_type: str,
    auth_data: dict[str, Any],
    email_and_name_filter: str | None = None,
    employment_status: str | None = None,
    group_ids_matches_any: str | None = None,
    tasks_summary_status_matches_any: str | None = None,
    task_type_matches_any: str | None = None,
    task_status_matches_any: str | None = None,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListPeopleOutput:
    """List the people tracked in a Vanta account with employment status, groups, and tasks."""
    if _missing_credentials(auth_data):
        return ListPeopleOutput(success=False, error=_MISSING)
    query = _query(
        emailAndNameFilter=email_and_name_filter,
        employmentStatus=employment_status,
        groupIdsMatchesAny=group_ids_matches_any,
        tasksSummaryStatusMatchesAny=tasks_summary_status_matches_any,
        taskTypeMatchesAny=task_type_matches_any,
        taskStatusMatchesAny=task_status_matches_any,
    )
    try:
        rows, page = await _fetch_list(
            auth_data, "/people", query, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListPeopleOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListPeopleOutput(success=False, error=str(exc))
    return ListPeopleOutput(
        success=True, people=[_person(r) for r in rows], page_info=page
    )


@tool(args_schema=GetPersonInput)
@serialize_pydantic_return
async def get_person(
    auth_type: str, auth_data: dict[str, Any], person_id: str
) -> GetPersonOutput:
    """Get a person tracked in Vanta by ID, including employment, leave, and security task status.
    """
    if _missing_credentials(auth_data):
        return GetPersonOutput(success=False, error=_MISSING)
    try:
        body = await _fetch_one(auth_data, f"/people/{person_id}")
    except httpx.TimeoutException:
        return GetPersonOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetPersonOutput(success=False, error=str(exc))
    return GetPersonOutput(success=True, person=_person(body))


@tool(args_schema=ListPoliciesInput)
@serialize_pydantic_return
async def list_policies(
    auth_type: str,
    auth_data: dict[str, Any],
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListPoliciesOutput:
    """List the security policies in a Vanta account with approval status and version info."""
    if _missing_credentials(auth_data):
        return ListPoliciesOutput(success=False, error=_MISSING)
    try:
        rows, page = await _fetch_list(
            auth_data, "/policies", {}, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListPoliciesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListPoliciesOutput(success=False, error=str(exc))
    return ListPoliciesOutput(
        success=True, policies=[_policy(r) for r in rows], page_info=page
    )


@tool(args_schema=GetPolicyInput)
@serialize_pydantic_return
async def get_policy(
    auth_type: str, auth_data: dict[str, Any], policy_id: str
) -> GetPolicyOutput:
    """Get a Vanta security policy by ID, including approval status and latest approved version
    documents.
    """
    if _missing_credentials(auth_data):
        return GetPolicyOutput(success=False, error=_MISSING)
    try:
        body = await _fetch_one(auth_data, f"/policies/{policy_id}")
    except httpx.TimeoutException:
        return GetPolicyOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetPolicyOutput(success=False, error=str(exc))
    return GetPolicyOutput(success=True, policy=_policy(body))


@tool(args_schema=ListVendorsInput)
@serialize_pydantic_return
async def list_vendors(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str | None = None,
    status_matches_any: str | None = None,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListVendorsOutput:
    """List the vendors tracked in a Vanta account with risk levels, contract dates, and review
    schedules.
    """
    if _missing_credentials(auth_data):
        return ListVendorsOutput(success=False, error=_MISSING)
    query = _query(name=name, statusMatchesAny=status_matches_any)
    try:
        rows, page = await _fetch_list(
            auth_data, "/vendors", query, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListVendorsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListVendorsOutput(success=False, error=str(exc))
    return ListVendorsOutput(
        success=True, vendors=[_vendor(r) for r in rows], page_info=page
    )


@tool(args_schema=GetVendorInput)
@serialize_pydantic_return
async def get_vendor(
    auth_type: str, auth_data: dict[str, Any], vendor_id: str
) -> GetVendorOutput:
    """Get a Vanta vendor by ID, including risk levels, contract details, and authentication info.
    """
    if _missing_credentials(auth_data):
        return GetVendorOutput(success=False, error=_MISSING)
    try:
        body = await _fetch_one(auth_data, f"/vendors/{vendor_id}")
    except httpx.TimeoutException:
        return GetVendorOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetVendorOutput(success=False, error=str(exc))
    return GetVendorOutput(success=True, vendor=_vendor(body))


@tool(args_schema=ListMonitoredComputersInput)
@serialize_pydantic_return
async def list_monitored_computers(
    auth_type: str,
    auth_data: dict[str, Any],
    compliance_status_filter_matches_any: str | None = None,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListMonitoredComputersOutput:
    """List the monitored computers in a Vanta account with device compliance check outcomes."""
    if _missing_credentials(auth_data):
        return ListMonitoredComputersOutput(success=False, error=_MISSING)
    query = _query(
        complianceStatusFilterMatchesAny=compliance_status_filter_matches_any
    )
    try:
        rows, page = await _fetch_list(
            auth_data, "/monitored-computers", query, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListMonitoredComputersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListMonitoredComputersOutput(success=False, error=str(exc))
    return ListMonitoredComputersOutput(
        success=True, computers=[_monitored_computer(r) for r in rows], page_info=page
    )


@tool(args_schema=ListVulnerabilitiesInput)
@serialize_pydantic_return
async def list_vulnerabilities(
    auth_type: str,
    auth_data: dict[str, Any],
    q: str | None = None,
    severity: str | None = None,
    is_fix_available: bool | None = None,
    is_deactivated: bool | None = None,
    include_vulnerabilities_without_slas: bool | None = None,
    package_identifier: str | None = None,
    external_vulnerability_id: str | None = None,
    integration_id: str | None = None,
    vulnerable_asset_id: str | None = None,
    sla_deadline_after_date: str | None = None,
    sla_deadline_before_date: str | None = None,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListVulnerabilitiesOutput:
    """List the vulnerabilities detected across a Vanta account with filters."""
    if _missing_credentials(auth_data):
        return ListVulnerabilitiesOutput(success=False, error=_MISSING)
    query = _query(
        q=q,
        severity=severity,
        isFixAvailable=is_fix_available,
        isDeactivated=is_deactivated,
        includeVulnerabilitiesWithoutSlas=include_vulnerabilities_without_slas,
        packageIdentifier=package_identifier,
        externalVulnerabilityId=external_vulnerability_id,
        integrationId=integration_id,
        vulnerableAssetId=vulnerable_asset_id,
        slaDeadlineAfterDate=sla_deadline_after_date,
        slaDeadlineBeforeDate=sla_deadline_before_date,
    )
    try:
        rows, page = await _fetch_list(
            auth_data, "/vulnerabilities", query, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListVulnerabilitiesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListVulnerabilitiesOutput(success=False, error=str(exc))
    return ListVulnerabilitiesOutput(
        success=True, vulnerabilities=[_vulnerability(r) for r in rows], page_info=page
    )


@tool(args_schema=ListVulnerabilityRemediationsInput)
@serialize_pydantic_return
async def list_vulnerability_remediations(
    auth_type: str,
    auth_data: dict[str, Any],
    integration_id: str | None = None,
    severity: str | None = None,
    is_remediated_on_time: bool | None = None,
    remediated_after_date: str | None = None,
    remediated_before_date: str | None = None,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListVulnerabilityRemediationsOutput:
    """List remediated vulnerabilities with detection, SLA, and remediation dates."""
    if _missing_credentials(auth_data):
        return ListVulnerabilityRemediationsOutput(success=False, error=_MISSING)
    query = _query(
        integrationId=integration_id,
        severity=severity,
        isRemediatedOnTime=is_remediated_on_time,
        remediatedAfterDate=remediated_after_date,
        remediatedBeforeDate=remediated_before_date,
    )
    try:
        rows, page = await _fetch_list(
            auth_data,
            "/vulnerability-remediations",
            query,
            page_size,
            page_cursor,
            max_pages,
        )
    except httpx.TimeoutException:
        return ListVulnerabilityRemediationsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListVulnerabilityRemediationsOutput(success=False, error=str(exc))
    return ListVulnerabilityRemediationsOutput(
        success=True,
        remediations=[_vulnerability_remediation(r) for r in rows],
        page_info=page,
    )


@tool(args_schema=ListVulnerableAssetsInput)
@serialize_pydantic_return
async def list_vulnerable_assets(
    auth_type: str,
    auth_data: dict[str, Any],
    q: str | None = None,
    integration_id: str | None = None,
    asset_type: str | None = None,
    asset_external_account_id: str | None = None,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListVulnerableAssetsOutput:
    """List the assets associated with vulnerabilities in a Vanta account."""
    if _missing_credentials(auth_data):
        return ListVulnerableAssetsOutput(success=False, error=_MISSING)
    query = _query(
        q=q,
        integrationId=integration_id,
        assetType=asset_type,
        assetExternalAccountId=asset_external_account_id,
    )
    try:
        rows, page = await _fetch_list(
            auth_data, "/vulnerable-assets", query, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListVulnerableAssetsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListVulnerableAssetsOutput(success=False, error=str(exc))
    return ListVulnerableAssetsOutput(
        success=True, assets=[_vulnerable_asset(r) for r in rows], page_info=page
    )


@tool(args_schema=GetVulnerableAssetInput)
@serialize_pydantic_return
async def get_vulnerable_asset(
    auth_type: str, auth_data: dict[str, Any], vulnerable_asset_id: str
) -> GetVulnerableAssetOutput:
    """Get a vulnerable asset in Vanta by ID, including its scanners and per-scanner asset details.
    """
    if _missing_credentials(auth_data):
        return GetVulnerableAssetOutput(success=False, error=_MISSING)
    try:
        body = await _fetch_one(auth_data, f"/vulnerable-assets/{vulnerable_asset_id}")
    except httpx.TimeoutException:
        return GetVulnerableAssetOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetVulnerableAssetOutput(success=False, error=str(exc))
    return GetVulnerableAssetOutput(success=True, asset=_vulnerable_asset(body))


@tool(args_schema=ListRiskScenariosInput)
@serialize_pydantic_return
async def list_risk_scenarios(
    auth_type: str,
    auth_data: dict[str, Any],
    search_string: str | None = None,
    include_ignored: bool | None = None,
    type: str | None = None,
    owner_matches_any: str | None = None,
    category_matches_any: str | None = None,
    cia_category_matches_any: str | None = None,
    treatment_type_matches_any: str | None = None,
    inherent_score_group_matches_any: str | None = None,
    residual_score_group_matches_any: str | None = None,
    review_status_matches_any: str | None = None,
    order_by: str | None = None,
    page_size: int | None = None,
    page_cursor: str | None = None,
    max_pages: int = 1,
) -> ListRiskScenariosOutput:
    """List the risk scenarios in a Vanta risk register with scores, treatment decisions, and review
    status.
    """
    if _missing_credentials(auth_data):
        return ListRiskScenariosOutput(success=False, error=_MISSING)
    query = _query(
        searchString=search_string,
        includeIgnored=include_ignored,
        type=type,
        ownerMatchesAny=owner_matches_any,
        categoryMatchesAny=category_matches_any,
        ciaCategoryMatchesAny=cia_category_matches_any,
        treatmentTypeMatchesAny=treatment_type_matches_any,
        inherentScoreGroupMatchesAny=inherent_score_group_matches_any,
        residualScoreGroupMatchesAny=residual_score_group_matches_any,
        reviewStatusMatchesAny=review_status_matches_any,
        orderBy=order_by,
    )
    try:
        rows, page = await _fetch_list(
            auth_data, "/risk-scenarios", query, page_size, page_cursor, max_pages
        )
    except httpx.TimeoutException:
        return ListRiskScenariosOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListRiskScenariosOutput(success=False, error=str(exc))
    return ListRiskScenariosOutput(
        success=True, risk_scenarios=[_risk_scenario(r) for r in rows], page_info=page
    )


@tool(args_schema=GetRiskScenarioInput)
@serialize_pydantic_return
async def get_risk_scenario(
    auth_type: str, auth_data: dict[str, Any], risk_scenario_id: str
) -> GetRiskScenarioOutput:
    """Get a Vanta risk scenario by ID, including its scores, treatment decision, and review status.
    """
    if _missing_credentials(auth_data):
        return GetRiskScenarioOutput(success=False, error=_MISSING)
    try:
        body = await _fetch_one(auth_data, f"/risk-scenarios/{risk_scenario_id}")
    except httpx.TimeoutException:
        return GetRiskScenarioOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetRiskScenarioOutput(success=False, error=str(exc))
    return GetRiskScenarioOutput(success=True, risk_scenario=_risk_scenario(body))
