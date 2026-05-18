"""Pydantic response models for the docusign integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateDraftOutput",
    "CreateEnvelopeFromFileOutput",
    "CreateEnvelopeOutput",
    "CreateRecipientViewOutput",
    "CreateSignatureRequestOutput",
    "DocumentSummary",
    "DownloadDocumentsOutput",
    "EnvelopeSummary",
    "GetEnvelopeOutput",
    "ListDocumentsOutput",
    "ListEnvelopesOutput",
    "ListRecipientsOutput",
    "RecipientSummary",
    "SendEnvelopeOutput",
    "VoidEnvelopeOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class EnvelopeSummary(_Base):
    envelope_id: str | None = None
    status: str | None = None
    email_subject: str | None = None
    status_date_time: str | None = None
    uri: str | None = None
    sender_user_name: str | None = None
    sender_email: str | None = None
    created_date_time: str | None = None
    sent_date_time: str | None = None
    completed_date_time: str | None = None
    voided_date_time: str | None = None
    voided_reason: str | None = None


class DocumentSummary(_Base):
    document_id: str | None = None
    name: str | None = None
    type: str | None = None
    uri: str | None = None
    order: str | None = None
    pages: str | None = None


class RecipientSummary(_Base):
    recipient_id: str | None = None
    name: str | None = None
    email: str | None = None
    status: str | None = None
    routing_order: str | None = None
    client_user_id: str | None = None
    signed_date_time: str | None = None
    delivered_date_time: str | None = None


# --- Per-action output models ---------------------------------------------


class CreateSignatureRequestOutput(_Base):
    success: bool
    error: str | None = None
    envelope_id: str | None = None
    status: str | None = None
    status_date_time: str | None = None
    uri: str | None = None


class CreateDraftOutput(_Base):
    success: bool
    error: str | None = None
    envelope_id: str | None = None
    status: str | None = None
    status_date_time: str | None = None
    uri: str | None = None


class CreateEnvelopeOutput(_Base):
    success: bool
    error: str | None = None
    envelope_id: str | None = None
    status: str | None = None
    status_date_time: str | None = None
    uri: str | None = None


class CreateEnvelopeFromFileOutput(_Base):
    success: bool
    error: str | None = None
    envelope_id: str | None = None
    status: str | None = None
    status_date_time: str | None = None
    uri: str | None = None


class CreateRecipientViewOutput(_Base):
    success: bool
    error: str | None = None
    url: str | None = None


class GetEnvelopeOutput(_Base):
    success: bool
    error: str | None = None
    envelope: EnvelopeSummary | None = None


class ListEnvelopesOutput(_Base):
    success: bool
    error: str | None = None
    envelopes: list[EnvelopeSummary] = Field(default_factory=list)
    result_set_size: int | None = None
    total_set_size: int | None = None


class ListDocumentsOutput(_Base):
    success: bool
    error: str | None = None
    documents: list[DocumentSummary] = Field(default_factory=list)


class ListRecipientsOutput(_Base):
    success: bool
    error: str | None = None
    signers: list[RecipientSummary] = Field(default_factory=list)
    carbon_copies: list[RecipientSummary] = Field(default_factory=list)
    agents: list[RecipientSummary] = Field(default_factory=list)


class SendEnvelopeOutput(_Base):
    success: bool
    error: str | None = None
    envelope_id: str | None = None
    status: str | None = None


class DownloadDocumentsOutput(_Base):
    success: bool
    error: str | None = None
    content_base64: str | None = None
    filename: str | None = None
    content_type: str | None = None


class VoidEnvelopeOutput(_Base):
    success: bool
    error: str | None = None
    envelope_id: str | None = None
    status: str | None = None
