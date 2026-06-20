"""Pydantic response models for the vanta integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "Control",
    "ControlDetail",
    "Document",
    "DocumentDetail",
    "DownloadDocumentFileOutput",
    "Framework",
    "FrameworkDetail",
    "GetControlOutput",
    "GetDocumentOutput",
    "GetFrameworkOutput",
    "GetPersonOutput",
    "GetPolicyOutput",
    "GetRiskScenarioOutput",
    "GetTestOutput",
    "GetVendorOutput",
    "GetVulnerableAssetOutput",
    "ListControlDocumentsOutput",
    "ListControlTestsOutput",
    "ListControlsOutput",
    "ListDocumentUploadsOutput",
    "ListDocumentsOutput",
    "ListFrameworkControlsOutput",
    "ListFrameworksOutput",
    "ListMonitoredComputersOutput",
    "ListPeopleOutput",
    "ListPoliciesOutput",
    "ListRiskScenariosOutput",
    "ListTestEntitiesOutput",
    "ListTestsOutput",
    "ListVendorsOutput",
    "ListVulnerabilitiesOutput",
    "ListVulnerabilityRemediationsOutput",
    "ListVulnerableAssetsOutput",
    "MonitoredComputer",
    "PageInfo",
    "Person",
    "Policy",
    "RiskScenario",
    "SubmitDocumentOutput",
    "Test",
    "TestEntity",
    "UploadDocumentFileOutput",
    "UploadedFile",
    "Vendor",
    "Vulnerability",
    "VulnerabilityRemediation",
    "VulnerableAsset",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Shared nested resource models ---------------------------------------


class PageInfo(_Base):
    """Cursor pagination info returned by every list endpoint."""

    start_cursor: str | None = None
    end_cursor: str | None = None
    has_next_page: bool | None = None
    has_previous_page: bool | None = None


class Owner(_Base):
    id: str | None = None
    display_name: str | None = None
    email_address: str | None = None


class Framework(_Base):
    id: str | None = None
    display_name: str | None = None
    shorthand_name: str | None = None
    description: str | None = None
    num_controls_completed: int | None = None
    num_controls_total: int | None = None
    num_documents_passing: int | None = None
    num_documents_total: int | None = None
    num_tests_passing: int | None = None
    num_tests_total: int | None = None


class FrameworkDetail(Framework):
    requirement_categories: list[dict[str, Any]] = Field(default_factory=list)


class Control(_Base):
    id: str | None = None
    external_id: str | None = None
    name: str | None = None
    description: str | None = None
    source: str | None = None
    domains: list[str] = Field(default_factory=list)
    owner: Owner | None = None
    role: str | None = None
    custom_fields: list[dict[str, Any]] = Field(default_factory=list)
    creation_date: str | None = None
    modification_date: str | None = None


class ControlDetail(Control):
    note: str | None = None
    status: str | None = None
    num_documents_passing: int | None = None
    num_documents_total: int | None = None
    num_tests_passing: int | None = None
    num_tests_total: int | None = None


class Test(_Base):
    id: str | None = None
    name: str | None = None
    description: str | None = None
    failure_description: str | None = None
    remediation_description: str | None = None
    category: str | None = None
    status: str | None = None
    integrations: list[str] = Field(default_factory=list)
    last_test_run_date: str | None = None
    latest_flip_date: str | None = None
    version: dict[str, Any] | None = None
    deactivated_status_info: dict[str, Any] | None = None
    remediation_status_info: dict[str, Any] | None = None
    owner: Owner | None = None


class TestEntity(_Base):
    id: str | None = None
    entity_status: str | None = None
    display_name: str | None = None
    response_type: str | None = None
    deactivated_reason: str | None = None
    created_date: str | None = None
    last_updated_date: str | None = None


class Document(_Base):
    id: str | None = None
    title: str | None = None
    description: str | None = None
    category: str | None = None
    owner_id: str | None = None
    is_sensitive: bool | None = None
    upload_status: str | None = None
    upload_status_date: str | None = None
    url: str | None = None


class DocumentDetail(Document):
    note: str | None = None
    next_renewal_date: str | None = None
    renewal_cadence: str | None = None
    reminder_window: str | None = None
    subscribers: list[str] = Field(default_factory=list)
    deactivated_status: dict[str, Any] | None = None


class UploadedFile(_Base):
    id: str | None = None
    file_name: str | None = None
    title: str | None = None
    description: str | None = None
    mime_type: str | None = None
    uploaded_by: dict[str, Any] | None = None
    creation_date: str | None = None
    updated_date: str | None = None
    deletion_date: str | None = None
    effective_date: str | None = None
    url: str | None = None


class Person(_Base):
    id: str | None = None
    user_id: str | None = None
    email_address: str | None = None
    name: dict[str, Any] | None = None
    employment: dict[str, Any] | None = None
    leave_info: dict[str, Any] | None = None
    group_ids: list[str] = Field(default_factory=list)
    tasks_summary: dict[str, Any] | None = None


class Policy(_Base):
    id: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None
    approved_at_date: str | None = None
    latest_version_status: str | None = None
    latest_approved_version: dict[str, Any] | None = None


class Vendor(_Base):
    id: str | None = None
    name: str | None = None
    status: str | None = None
    website_url: str | None = None
    category: str | None = None
    services_provided: str | None = None
    additional_notes: str | None = None
    account_manager_name: str | None = None
    account_manager_email: str | None = None
    security_owner_user_id: str | None = None
    business_owner_user_id: str | None = None
    inherent_risk_level: str | None = None
    residual_risk_level: str | None = None
    is_risk_auto_scored: bool | None = None
    is_visible_to_auditors: bool | None = None
    risk_attribute_ids: list[str] = Field(default_factory=list)
    vendor_headquarters: str | None = None
    contract_start_date: str | None = None
    contract_renewal_date: str | None = None
    contract_termination_date: str | None = None
    contract_amount: dict[str, Any] | None = None
    next_security_review_due_date: str | None = None
    last_security_review_completion_date: str | None = None
    auth_details: dict[str, Any] | None = None
    custom_fields: list[dict[str, Any]] = Field(default_factory=list)
    latest_decision: dict[str, Any] | None = None
    linked_task_tracker_task_procurement_request: dict[str, Any] | None = None


class MonitoredComputer(_Base):
    id: str | None = None
    integration_id: str | None = None
    last_check_date: str | None = None
    screenlock: str | None = None
    disk_encryption: str | None = None
    password_manager: str | None = None
    antivirus_installation: str | None = None
    operating_system: dict[str, Any] | None = None
    owner: Owner | None = None
    serial_number: str | None = None
    udid: str | None = None


class RiskScenario(_Base):
    risk_id: str | None = None
    description: str | None = None
    likelihood: float | None = None
    impact: float | None = None
    residual_likelihood: float | None = None
    residual_impact: float | None = None
    categories: list[str] = Field(default_factory=list)
    cia_categories: list[str] = Field(default_factory=list)
    treatment: str | None = None
    owner: str | None = None
    note: str | None = None
    risk_register: str | None = None
    custom_fields: list[dict[str, Any]] = Field(default_factory=list)
    is_archived: bool | None = None
    review_status: str | None = None
    required_approvers: list[str] = Field(default_factory=list)
    type: str | None = None
    identification_date: str | None = None


class VulnerabilityRemediation(_Base):
    id: str | None = None
    vulnerability_id: str | None = None
    vulnerable_asset_id: str | None = None
    severity: str | None = None
    detected_date: str | None = None
    sla_deadline_date: str | None = None
    remediation_date: str | None = None


class VulnerableAsset(_Base):
    id: str | None = None
    name: str | None = None
    asset_type: str | None = None
    has_been_scanned: bool | None = None
    image_scan_tag: str | None = None
    scanners: list[dict[str, Any]] = Field(default_factory=list)


class Vulnerability(_Base):
    id: str | None = None
    name: str | None = None
    description: str | None = None
    severity: str | None = None
    vulnerability_type: str | None = None
    integration_id: str | None = None
    target_id: str | None = None
    package_identifier: str | None = None
    cvss_severity_score: float | None = None
    scanner_score: float | None = None
    is_fixable: bool | None = None
    fixed_version: str | None = None
    remediate_by_date: str | None = None
    first_detected_date: str | None = None
    source_detected_date: str | None = None
    last_detected_date: str | None = None
    scan_source: str | None = None
    external_url: str | None = None
    related_vulns: list[str] = Field(default_factory=list)
    related_urls: list[str] = Field(default_factory=list)
    deactivate_metadata: dict[str, Any] | None = None


# --- Per-action output models --------------------------------------------


class ListFrameworksOutput(_Base):
    success: bool
    error: str | None = None
    frameworks: list[Framework] = Field(default_factory=list)
    page_info: PageInfo | None = None


class GetFrameworkOutput(_Base):
    success: bool
    error: str | None = None
    framework: FrameworkDetail | None = None


class ListFrameworkControlsOutput(_Base):
    success: bool
    error: str | None = None
    controls: list[Control] = Field(default_factory=list)
    page_info: PageInfo | None = None


class ListControlsOutput(_Base):
    success: bool
    error: str | None = None
    controls: list[Control] = Field(default_factory=list)
    page_info: PageInfo | None = None


class GetControlOutput(_Base):
    success: bool
    error: str | None = None
    control: ControlDetail | None = None


class ListControlTestsOutput(_Base):
    success: bool
    error: str | None = None
    tests: list[Test] = Field(default_factory=list)
    page_info: PageInfo | None = None


class ListControlDocumentsOutput(_Base):
    success: bool
    error: str | None = None
    documents: list[Document] = Field(default_factory=list)
    page_info: PageInfo | None = None


class ListTestsOutput(_Base):
    success: bool
    error: str | None = None
    tests: list[Test] = Field(default_factory=list)
    page_info: PageInfo | None = None


class GetTestOutput(_Base):
    success: bool
    error: str | None = None
    test: Test | None = None


class ListTestEntitiesOutput(_Base):
    success: bool
    error: str | None = None
    entities: list[TestEntity] = Field(default_factory=list)
    page_info: PageInfo | None = None


class ListDocumentsOutput(_Base):
    success: bool
    error: str | None = None
    documents: list[Document] = Field(default_factory=list)
    page_info: PageInfo | None = None


class GetDocumentOutput(_Base):
    success: bool
    error: str | None = None
    document: DocumentDetail | None = None


class ListDocumentUploadsOutput(_Base):
    success: bool
    error: str | None = None
    uploads: list[UploadedFile] = Field(default_factory=list)
    page_info: PageInfo | None = None


class UploadDocumentFileOutput(_Base):
    success: bool
    error: str | None = None
    upload: UploadedFile | None = None


class DownloadDocumentFileOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    mime_type: str | None = None
    size: int | None = None
    # Base64-encoded file content, so the binary body remains
    # JSON-serializable in the tool result.
    data: str | None = None


class SubmitDocumentOutput(_Base):
    success: bool
    error: str | None = None
    document_id: str | None = None
    submitted: bool | None = None


class ListPeopleOutput(_Base):
    success: bool
    error: str | None = None
    people: list[Person] = Field(default_factory=list)
    page_info: PageInfo | None = None


class GetPersonOutput(_Base):
    success: bool
    error: str | None = None
    person: Person | None = None


class ListPoliciesOutput(_Base):
    success: bool
    error: str | None = None
    policies: list[Policy] = Field(default_factory=list)
    page_info: PageInfo | None = None


class GetPolicyOutput(_Base):
    success: bool
    error: str | None = None
    policy: Policy | None = None


class ListVendorsOutput(_Base):
    success: bool
    error: str | None = None
    vendors: list[Vendor] = Field(default_factory=list)
    page_info: PageInfo | None = None


class GetVendorOutput(_Base):
    success: bool
    error: str | None = None
    vendor: Vendor | None = None


class ListMonitoredComputersOutput(_Base):
    success: bool
    error: str | None = None
    computers: list[MonitoredComputer] = Field(default_factory=list)
    page_info: PageInfo | None = None


class ListVulnerabilitiesOutput(_Base):
    success: bool
    error: str | None = None
    vulnerabilities: list[Vulnerability] = Field(default_factory=list)
    page_info: PageInfo | None = None


class ListVulnerabilityRemediationsOutput(_Base):
    success: bool
    error: str | None = None
    remediations: list[VulnerabilityRemediation] = Field(default_factory=list)
    page_info: PageInfo | None = None


class ListVulnerableAssetsOutput(_Base):
    success: bool
    error: str | None = None
    assets: list[VulnerableAsset] = Field(default_factory=list)
    page_info: PageInfo | None = None


class GetVulnerableAssetOutput(_Base):
    success: bool
    error: str | None = None
    asset: VulnerableAsset | None = None


class ListRiskScenariosOutput(_Base):
    success: bool
    error: str | None = None
    risk_scenarios: list[RiskScenario] = Field(default_factory=list)
    page_info: PageInfo | None = None


class GetRiskScenarioOutput(_Base):
    success: bool
    error: str | None = None
    risk_scenario: RiskScenario | None = None
