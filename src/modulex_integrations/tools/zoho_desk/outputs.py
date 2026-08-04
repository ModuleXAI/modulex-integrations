"""Pydantic response models for the Zoho Desk integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddCommentOutput",
    "GetContactOutput",
    "GetThreadOutput",
    "GetTicketOutput",
    "ListCommentsOutput",
    "ListOrganizationsOutput",
    "ListThreadsOutput",
    "ListTicketsOutput",
    "UpdateTicketOutput",
    "ZohoAttachment",
    "ZohoComment",
    "ZohoContact",
    "ZohoOrganization",
    "ZohoThread",
    "ZohoTicket",
    "ZohoUserRef",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class ZohoAttachment(_Base):
    """Attachment metadata surfaced on a comment or thread (never the bytes)."""

    id: str | None = None
    name: str | None = None
    # Zoho serializes the size as a string and its samples are not
    # self-consistent about the unit, so it is reported verbatim.
    size: str | None = None
    href: str | None = None


class ZohoUserRef(_Base):
    """A person referenced from a comment (``commenter``) or thread (``author``)."""

    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    type: str | None = None
    role_name: str | None = None
    photo_url: str | None = None


class ZohoTicket(_Base):
    """A Zoho Desk ticket.

    List endpoints return a projection: ``description``, ``description_text``,
    ``resolution``, ``status_type`` and ``classification`` are only populated by
    the single-ticket endpoints.
    """

    id: str | None = None
    ticket_number: str | None = None
    subject: str | None = None
    description: str | None = None
    # Plain-text rendering of the description: HTML stripped when the body
    # contains markup, otherwise the description verbatim.
    description_text: str | None = None
    status: str | None = None
    status_type: str | None = None
    priority: str | None = None
    category: str | None = None
    sub_category: str | None = None
    classification: str | None = None
    channel: str | None = None
    department_id: str | None = None
    contact_id: str | None = None
    account_id: str | None = None
    assignee_id: str | None = None
    email: str | None = None
    phone: str | None = None
    due_date: str | None = None
    response_due_date: str | None = None
    created_time: str | None = None
    modified_time: str | None = None
    closed_time: str | None = None
    resolution: str | None = None
    thread_count: str | None = None
    comment_count: str | None = None
    web_url: str | None = None
    is_escalated: bool | None = None
    is_over_due: bool | None = None
    is_spam: bool | None = None
    # Custom field values, keyed by custom field API name.
    cf: dict[str, Any] | None = None
    # Populated only when the request asks for the related record via
    # ``include`` (``contacts`` -> ``contact``, ``assignee`` -> ``assignee``).
    # TODO (unverified): only the ``contact`` and ``assignee`` expansion keys
    # are confirmed from published Zoho Desk response samples; the remaining
    # ``include`` targets (products, departments, team, contract, isRead,
    # skills) surface through the ``raw`` payload of the single-ticket tools
    # until their exact key names are confirmed per the Zoho Desk API docs.
    contact: dict[str, Any] | None = None
    assignee: dict[str, Any] | None = None


class ZohoComment(_Base):
    """A comment (agent note) on a Zoho Desk ticket."""

    id: str | None = None
    content: str | None = None
    content_type: str | None = None
    # Plain-text rendering of ``content`` (HTML stripped when the content type
    # marks the body as HTML).
    content_text: str | None = None
    is_public: bool | None = None
    commenter_id: str | None = None
    commenter: ZohoUserRef | None = None
    commented_time: str | None = None
    modified_time: str | None = None
    attachments: list[ZohoAttachment] = Field(default_factory=list)


class ZohoThread(_Base):
    """A conversation thread (customer-facing message) on a Zoho Desk ticket.

    List endpoints return a projection: message bodies (``content``,
    ``summary``, ``to``/``cc``/``bcc``) come back only from the single-thread
    endpoint.
    """

    id: str | None = None
    channel: str | None = None
    direction: str | None = None
    content: str | None = None
    content_type: str | None = None
    content_text: str | None = None
    summary: str | None = None
    responder_id: str | None = None
    created_time: str | None = None
    has_attach: bool | None = None
    attachment_count: str | None = None
    from_email_address: str | None = None
    to: str | None = None
    cc: str | None = None
    bcc: str | None = None
    reply_to: str | None = None
    is_forward: bool | None = None
    is_content_truncated: bool | None = None
    full_content_url: str | None = None
    plain_text: str | None = None
    status: str | None = None
    is_description_thread: bool | None = None
    visibility: str | None = None
    can_reply: bool | None = None
    author: ZohoUserRef | None = None
    attachments: list[ZohoAttachment] = Field(default_factory=list)


class ZohoContact(_Base):
    """A Zoho Desk contact (the end user behind a ticket)."""

    id: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    secondary_email: str | None = None
    phone: str | None = None
    mobile: str | None = None
    account_id: str | None = None
    owner_id: str | None = None
    type: str | None = None
    title: str | None = None
    street: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    zip: str | None = None
    description: str | None = None
    cf: dict[str, Any] | None = None


class ZohoOrganization(_Base):
    """A Zoho Desk organization (portal)."""

    id: str | None = None
    company_name: str | None = None
    portal_name: str | None = None


# --- Per-action output models ---------------------------------------------


class ListTicketsOutput(_Base):
    success: bool
    error: str | None = None
    tickets: list[ZohoTicket] = Field(default_factory=list)
    count: int = 0


class GetTicketOutput(_Base):
    success: bool
    error: str | None = None
    ticket: ZohoTicket | None = None
    # The complete ticket object exactly as returned, so related records asked
    # for via ``include`` and any custom keys are never dropped.
    raw: dict[str, Any] | None = None


class UpdateTicketOutput(_Base):
    success: bool
    error: str | None = None
    ticket: ZohoTicket | None = None
    raw: dict[str, Any] | None = None


class ListCommentsOutput(_Base):
    success: bool
    error: str | None = None
    comments: list[ZohoComment] = Field(default_factory=list)
    count: int = 0


class AddCommentOutput(_Base):
    success: bool
    error: str | None = None
    comment: ZohoComment | None = None
    raw: dict[str, Any] | None = None


class ListThreadsOutput(_Base):
    success: bool
    error: str | None = None
    threads: list[ZohoThread] = Field(default_factory=list)
    count: int = 0


class GetThreadOutput(_Base):
    success: bool
    error: str | None = None
    thread: ZohoThread | None = None
    raw: dict[str, Any] | None = None


class GetContactOutput(_Base):
    success: bool
    error: str | None = None
    contact: ZohoContact | None = None
    raw: dict[str, Any] | None = None


class ListOrganizationsOutput(_Base):
    success: bool
    error: str | None = None
    organizations: list[ZohoOrganization] = Field(default_factory=list)
    count: int = 0
