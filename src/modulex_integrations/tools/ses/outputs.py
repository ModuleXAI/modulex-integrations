"""Pydantic response models for the ses integration's @tool functions.

Every model mirrors the documented Amazon SES API v2 response shape,
with camelCase JSON keys mapped to snake_case attributes at parse time.
Fields stay permissive (``| None`` scalars, ``default_factory=list``
collections) because SES omits optional members entirely.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BulkEmailResult",
    "CreateConfigurationSetOutput",
    "CreateEmailIdentityOutput",
    "CreateTemplateOutput",
    "DeleteEmailIdentityOutput",
    "DeleteSuppressedDestinationOutput",
    "DeleteTemplateOutput",
    "DkimAttributes",
    "GetAccountOutput",
    "GetEmailIdentityOutput",
    "GetSuppressedDestinationOutput",
    "GetTemplateOutput",
    "IdentitySummary",
    "IdentityTag",
    "ListIdentitiesOutput",
    "ListSuppressedDestinationsOutput",
    "ListTemplatesOutput",
    "MailFromAttributes",
    "PutSuppressedDestinationOutput",
    "SendBulkEmailOutput",
    "SendCustomVerificationEmailOutput",
    "SendEmailOutput",
    "SendTemplatedEmailOutput",
    "SuppressedDestinationSummary",
    "TemplateSummary",
    "UpdateTemplateOutput",
    "VerificationInfo",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models --------------------------------------------------


class BulkEmailResult(_Base):
    """One entry of ``BulkEmailEntryResults``."""

    message_id: str | None = None
    status: str | None = None
    error: str | None = None


class IdentitySummary(_Base):
    """One entry of ``EmailIdentities``."""

    identity_name: str | None = None
    identity_type: str | None = None
    sending_enabled: bool | None = None
    verification_status: str | None = None


class TemplateSummary(_Base):
    """One entry of ``TemplatesMetadata``."""

    template_name: str | None = None
    created_timestamp: float | str | None = None


class SuppressedDestinationSummary(_Base):
    """One entry of ``SuppressedDestinationSummaries``."""

    email_address: str | None = None
    reason: str | None = None
    last_update_time: float | str | None = None


class DkimAttributes(_Base):
    """DKIM signing configuration and status for an identity."""

    signing_enabled: bool | None = None
    status: str | None = None
    tokens: list[str] = Field(default_factory=list)
    signing_attributes_origin: str | None = None
    next_signing_key_length: str | None = None
    current_signing_key_length: str | None = None
    last_key_generation_timestamp: float | str | None = None
    signing_hosted_zone: str | None = None


class MailFromAttributes(_Base):
    """Custom MAIL FROM domain configuration for an identity."""

    mail_from_domain: str | None = None
    mail_from_domain_status: str | None = None
    behavior_on_mx_failure: str | None = None


class VerificationInfo(_Base):
    """Additional diagnostics about an identity's verification state."""

    error_type: str | None = None
    last_checked_timestamp: float | str | None = None
    last_success_timestamp: float | str | None = None
    soa_record: dict[str, Any] | None = None


class IdentityTag(_Base):
    """A key/value tag attached to an identity."""

    key: str | None = None
    value: str | None = None


# --- Per-action output models ------------------------------------------------


class SendEmailOutput(_Base):
    success: bool
    error: str | None = None
    message_id: str | None = None


class SendTemplatedEmailOutput(_Base):
    success: bool
    error: str | None = None
    message_id: str | None = None


class SendBulkEmailOutput(_Base):
    success: bool
    error: str | None = None
    results: list[BulkEmailResult] = Field(default_factory=list)
    success_count: int | None = None
    failure_count: int | None = None


class ListIdentitiesOutput(_Base):
    success: bool
    error: str | None = None
    identities: list[IdentitySummary] = Field(default_factory=list)
    next_token: str | None = None
    count: int | None = None


class GetAccountOutput(_Base):
    success: bool
    error: str | None = None
    sending_enabled: bool | None = None
    max_24_hour_send: float | None = None
    max_send_rate: float | None = None
    sent_last_24_hours: float | None = None
    production_access_enabled: bool | None = None
    enforcement_status: str | None = None
    dedicated_ip_auto_warmup_enabled: bool | None = None
    suppressed_reasons: list[str] = Field(default_factory=list)


class CreateTemplateOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
    template_name: str | None = None


class GetTemplateOutput(_Base):
    success: bool
    error: str | None = None
    template_name: str | None = None
    subject_part: str | None = None
    text_part: str | None = None
    html_part: str | None = None


class ListTemplatesOutput(_Base):
    success: bool
    error: str | None = None
    templates: list[TemplateSummary] = Field(default_factory=list)
    next_token: str | None = None
    count: int | None = None


class DeleteTemplateOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
    template_name: str | None = None


class UpdateTemplateOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
    template_name: str | None = None


class SendCustomVerificationEmailOutput(_Base):
    success: bool
    error: str | None = None
    message_id: str | None = None


class CreateEmailIdentityOutput(_Base):
    success: bool
    error: str | None = None
    identity_type: str | None = None
    verified_for_sending_status: bool | None = None
    dkim_attributes: DkimAttributes | None = None


class GetEmailIdentityOutput(_Base):
    success: bool
    error: str | None = None
    identity_type: str | None = None
    verified_for_sending_status: bool | None = None
    verification_status: str | None = None
    feedback_forwarding_status: bool | None = None
    configuration_set_name: str | None = None
    dkim_attributes: DkimAttributes | None = None
    mail_from_attributes: MailFromAttributes | None = None
    policies: dict[str, str] | None = None
    tags: list[IdentityTag] = Field(default_factory=list)
    verification_info: VerificationInfo | None = None


class DeleteEmailIdentityOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
    email_identity: str | None = None


class PutSuppressedDestinationOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
    email_address: str | None = None
    reason: str | None = None


class GetSuppressedDestinationOutput(_Base):
    success: bool
    error: str | None = None
    email_address: str | None = None
    reason: str | None = None
    last_update_time: float | str | None = None
    message_id: str | None = None
    feedback_id: str | None = None


class ListSuppressedDestinationsOutput(_Base):
    success: bool
    error: str | None = None
    destinations: list[SuppressedDestinationSummary] = Field(default_factory=list)
    next_token: str | None = None
    count: int | None = None


class DeleteSuppressedDestinationOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
    email_address: str | None = None


class CreateConfigurationSetOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
    configuration_set_name: str | None = None
