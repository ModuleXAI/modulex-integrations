"""Zoho Desk LangChain ``@tool`` functions.

Pure HTTP integration against the Zoho Desk REST API (``/api/v1``).
Credentials arrive as ``auth_type, auth_data`` (first args); ``auth_data``
carries the Self Client pair (``client_id`` / ``client_secret``), the Zoho
Desk organization ID and the data center.

Each invocation first exchanges the credential pair for a short-lived access
token (``POST {accounts server}/oauth/v2/token`` with
``grant_type=client_credentials``), then calls the Desk API with
``Authorization: Zoho-oauthtoken <access_token>`` plus an ``orgId`` header
identifying the organization (portal). ``list_organizations`` is the one
endpoint that takes no ``orgId`` header.

Zoho Desk is a multi-data-center product: the REST host is
``desk.zoho.<tld>`` in the data center the account lives in. It is resolved
from the ``api_domain`` the token response carries (falling back to the
configured ``data_center``) and validated against Zoho's own apex domains
before it is allowed to receive the access token. The accounts server that
receives the client secret is picked from a closed map of literal hosts.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Any, NamedTuple
from urllib.parse import quote, urlparse

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.zoho_desk.outputs import (
    AddCommentOutput,
    GetContactOutput,
    GetThreadOutput,
    GetTicketOutput,
    ListCommentsOutput,
    ListOrganizationsOutput,
    ListThreadsOutput,
    ListTicketsOutput,
    UpdateTicketOutput,
    ZohoAttachment,
    ZohoComment,
    ZohoContact,
    ZohoOrganization,
    ZohoThread,
    ZohoTicket,
    ZohoUserRef,
)

__all__ = [
    "add_comment",
    "get_contact",
    "get_thread",
    "get_ticket",
    "list_comments",
    "list_organizations",
    "list_threads",
    "list_tickets",
    "update_ticket",
]

_TIMEOUT = 30.0

# REST host for the US data center, used whenever no data center is known.
_DEFAULT_DESK_BASE = "https://desk.zoho.com"

# Zoho-owned apex domains across data centers. The REST host is derived from
# the `api_domain` of a token response, so it is anchored to this list with a
# strict suffix match before it receives the access token: a loose
# "contains zoho." check would accept a look-alike such as
# ``desk.zoho.com.example.org``.
_ZOHO_APEX_DOMAINS = (
    "zoho.com",
    "zoho.eu",
    "zoho.in",
    "zoho.com.au",
    "zoho.jp",
    "zoho.ca",
    "zoho.sa",
    "zoho.com.cn",
    "zoho.uk",
    "zohocloud.ca",
    "zohoapis.com",
    "zohoapis.eu",
    "zohoapis.in",
    "zohoapis.com.au",
    "zohoapis.jp",
    "zohoapis.ca",
    "zohoapis.sa",
    "zohoapis.com.cn",
    "zohoapis.uk",
)

# Accepted shorthand data-center values (the key into the host maps below).
_DATA_CENTER_TLDS = frozenset(
    {"com", "eu", "in", "com.au", "jp", "ca", "sa", "com.cn", "uk"}
)

# Desk REST hosts, one literal per data center — the same closed-map discipline
# as _ACCOUNTS_URLS below, since the access token is sent here. Canada is
# ``desk.zohocloud.ca``; ``desk.zoho.ca`` does not resolve at all, so deriving
# the host as ``desk.zoho.<tld>`` silently routed Canadian tenants to a dead
# name. All nine were confirmed live (HTTP 401 on /api/v1/organizations).
_DESK_HOSTS: dict[str, str] = {
    "com": "https://desk.zoho.com",
    "eu": "https://desk.zoho.eu",
    "in": "https://desk.zoho.in",
    "com.au": "https://desk.zoho.com.au",
    "jp": "https://desk.zoho.jp",
    "ca": "https://desk.zohocloud.ca",
    "sa": "https://desk.zoho.sa",
    "uk": "https://desk.zoho.uk",
    "com.cn": "https://desk.zoho.com.cn",
}

# Accounts servers that mint the access token, one literal per data center.
# Deliberately a closed map of constants rather than a derived pattern: the
# client secret is posted here, so the only hosts it can ever reach are these.
# Canada is ``zohocloud.ca``, NOT ``zoho.ca``. All nine were confirmed live
# (HTTP 200 on /oauth/serverinfo).
_ACCOUNTS_URLS: dict[str, str] = {
    "com": "https://accounts.zoho.com",
    "eu": "https://accounts.zoho.eu",
    "in": "https://accounts.zoho.in",
    "com.au": "https://accounts.zoho.com.au",
    "jp": "https://accounts.zoho.jp",
    "ca": "https://accounts.zohocloud.ca",
    "sa": "https://accounts.zoho.sa",
    "uk": "https://accounts.zoho.uk",
    "com.cn": "https://accounts.zoho.com.cn",
}

_DEFAULT_ACCOUNTS_URL = _ACCOUNTS_URLS["com"]

# Scopes the minted token asks for — exactly what the nine actions exercise.
# The Self Client must have been created with (at least) these granted.
_TOKEN_SCOPES = "Desk.tickets.READ,Desk.tickets.UPDATE,Desk.contacts.READ,Desk.basic.READ"

_ZOHO_TLD_RE = re.compile(r"zoho(?:apis|cloud)?\.([a-z.]+)$")


# --- Host / base URL resolution -------------------------------------------


def _is_zoho_host(hostname: str) -> bool:
    """True only when the hostname is exactly a Zoho apex or a subdomain of one."""
    host = hostname.lower()
    return any(host == apex or host.endswith(f".{apex}") for apex in _ZOHO_APEX_DOMAINS)


def _desk_base(api_domain: str) -> str:
    """Resolve the data-center-scoped Zoho Desk host.

    ``api_domain`` is what the token response carries (e.g.
    ``https://www.zohoapis.eu``); the Desk REST API lives on ``desk.zoho.eu``
    in the same data center. The shorthand TLD (``eu``, ``in``, ``com.au``,
    ...) is also accepted so a configured data center can stand in. Anything
    absent, unparseable or not a Zoho host falls back to the US host.
    """
    raw = api_domain.strip()
    if not raw:
        return _DEFAULT_DESK_BASE
    if "://" not in raw:
        tld = raw.lstrip(".").lower()
        return _DESK_HOSTS.get(tld, _DEFAULT_DESK_BASE)
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not _is_zoho_host(host):
        return _DEFAULT_DESK_BASE
    match = _ZOHO_TLD_RE.search(host)
    tld = match.group(1) if match else ""
    return _DESK_HOSTS.get(tld, _DEFAULT_DESK_BASE)


def _api_base(api_domain: str) -> str:
    """Return the Zoho Desk REST base (``{desk host}/api/v1``)."""
    return f"{_desk_base(api_domain)}/api/v1"


def _data_center(auth_data: dict[str, Any]) -> str:
    """Normalized data-center suffix from the credential (US when unset)."""
    raw = str(auth_data.get("data_center") or "").strip().lstrip(".").lower()
    return raw if raw in _DATA_CENTER_TLDS else "com"


def _accounts_url(auth_data: dict[str, Any]) -> str:
    """The accounts server that mints tokens for this credential."""
    return _ACCOUNTS_URLS.get(_data_center(auth_data), _DEFAULT_ACCOUNTS_URL)


# --- Auth helpers ----------------------------------------------------------


class _Token(NamedTuple):
    """A minted access token plus the data-center base it is valid against."""

    access_token: str
    api_domain: str


def _credentials(auth_data: dict[str, Any]) -> tuple[str, str]:
    """The Self Client credential pair from ``auth_data``."""
    return (
        str(auth_data.get("client_id") or "").strip(),
        str(auth_data.get("client_secret") or "").strip(),
    )


def _credential_error(auth_data: dict[str, Any]) -> str | None:
    """Short-circuit message when the credential pair is missing or blank."""
    client_id, client_secret = _credentials(auth_data)
    return None if client_id and client_secret else _MISSING_CREDENTIALS


def _desk_headers(access_token: str, org_id: str | None = None) -> dict[str, str]:
    """Headers for a Zoho Desk API call; ``orgId`` is added when supplied."""
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Zoho-oauthtoken {access_token}",
    }
    if org_id:
        headers["orgId"] = org_id
    return headers


def _resolve_org_id(org_id: str | None, auth_data: dict[str, Any]) -> str:
    """Prefer the explicit organization ID, else the one on the credential."""
    explicit = (org_id or "").strip()
    if explicit:
        return explicit
    return str(auth_data.get("org_id") or "").strip()


_MISSING_CREDENTIALS = (
    "Zoho Desk client ID and client secret are required. Add them to the"
    " credential from the Self Client you created in the Zoho API console."
)
_MISSING_ORG = (
    "Zoho Desk organization ID is required. Provide org_id, or configure it on"
    " the credential — it also forms the `soid` of the token request."
)
_TIMED_OUT = "Request to Zoho Desk timed out."


async def _mint_access_token(
    client: httpx.AsyncClient,
    auth_data: dict[str, Any],
    org_id: str,
) -> tuple[_Token | None, str | None]:
    """Exchange the Self Client credential pair for a short-lived token.

    Returns ``(token, None)`` on success or ``(None, error)`` on failure, so
    callers can short-circuit before touching the Desk API. Tokens are valid
    for one hour and are minted per invocation — nothing is cached between
    calls, keeping every action stateless.
    """
    client_id, client_secret = _credentials(auth_data)
    form: dict[str, Any] = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": _TOKEN_SCOPES,
        # `soid` follows Zoho's `{servicename}.{zsoid}` syntax, where zsoid is
        # the portal/organization ID and the service name for this API is
        # documented as `ZohoDesk`, per
        # https://www.zoho.com/accounts/protocol/oauth/self-client/client-credentials-flow.html
        "soid": f"ZohoDesk.{org_id}",
    }
    try:
        response = await client.post(f"{_accounts_url(auth_data)}/oauth/v2/token", data=form)
    except httpx.TimeoutException:
        return None, _TIMED_OUT
    except Exception as exc:
        return None, f"Failed to obtain a Zoho Desk access token: {exc}"

    payload = _json_body(response)
    if not _is_ok(response):
        return None, _error_message(
            payload,
            f"Failed to obtain a Zoho Desk access token (HTTP {response.status_code})",
        )
    # The accounts server answers a rejected credential with HTTP 200 and an
    # `error` key rather than a non-2xx status.
    if isinstance(payload, dict):
        failure = payload.get("error")
        if isinstance(failure, str) and failure.strip():
            return None, f"Zoho Desk rejected the client credentials: {failure}"
        access_token = payload.get("access_token")
        if isinstance(access_token, str) and access_token:
            api_domain = payload.get("api_domain")
            return _Token(access_token, str(api_domain or "")), None
    return None, "Zoho Desk token response did not contain an access_token."


# --- Response helpers ------------------------------------------------------


def _json_body(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:
        return {}


def _is_ok(response: httpx.Response) -> bool:
    return 200 <= response.status_code < 300


def _error_message(payload: Any, fallback: str) -> str:
    """Extract a human-readable message from a Zoho Desk error body."""
    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message
        code = payload.get("errorCode")
        if isinstance(code, str) and code.strip():
            return code
    return fallback


def _records(payload: Any) -> list[dict[str, Any]]:
    """Zoho Desk wraps list results in a top-level ``data`` array."""
    if isinstance(payload, dict):
        rows = payload.get("data")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def _as_dict(payload: Any) -> dict[str, Any]:
    return payload if isinstance(payload, dict) else {}


# --- Rich-text helpers -----------------------------------------------------

_HTML_SKIP_TAGS = frozenset({"script", "style", "img", "head", "noscript"})
_HTML_BLOCK_TAGS = frozenset(
    {
        "address",
        "article",
        "blockquote",
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "li",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tr",
        "ul",
    }
)

# A real element is required before a body is treated as markup: a paired
# <tag>...</tag>, a self-closing <tag/>, a comment/doctype, or a character
# entity. A bare "<"..">" pair is not enough, so plain support text such as
# "if x<y then z>0" is never run through the stripper and silently gutted.
_HTML_PAIRED_RE = re.compile(r"<([a-z][a-z0-9]*)\b[^>]*>[\s\S]*</\1\s*>", re.IGNORECASE)
_HTML_SELF_CLOSING_RE = re.compile(r"<[a-z][a-z0-9]*\b[^>]*/>", re.IGNORECASE)
_HTML_DOCTYPE_RE = re.compile(r"<!(?:--|doctype)", re.IGNORECASE)
_HTML_ENTITY_RE = re.compile(r"&(?:[a-z]+|#\d+|#x[0-9a-f]+);", re.IGNORECASE)
_BLANK_LINES_RE = re.compile(r"\n{3,}")


class _TextExtractor(HTMLParser):
    """Collapse Zoho Desk rich-text HTML into readable plain text.

    Anchors collapse to their text; ``img``/``script``/``style`` subtrees are
    dropped; block-level elements become line breaks.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _HTML_SKIP_TAGS:
            self._skip_depth += 1
        elif tag in _HTML_BLOCK_TAGS:
            self._parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _HTML_BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _HTML_SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in _HTML_BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._parts.append(data)

    def text(self) -> str:
        joined = "".join(self._parts)
        lines = [line.rstrip() for line in joined.replace("\r\n", "\n").split("\n")]
        return _BLANK_LINES_RE.sub("\n\n", "\n".join(lines)).strip()


def _html_to_text(html: str) -> str:
    if not html:
        return ""
    parser = _TextExtractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        return html
    return parser.text()


def _looks_like_html(value: str) -> bool:
    """True when a string carries markup worth stripping."""
    return bool(
        _HTML_PAIRED_RE.search(value)
        or _HTML_SELF_CLOSING_RE.search(value)
        or _HTML_DOCTYPE_RE.search(value)
        or _HTML_ENTITY_RE.search(value)
    )


def _derive_content_text(content: Any, content_type: Any) -> str | None:
    """Derive a plain-text rendering of a Zoho Desk content value.

    Zoho is not consistent about the HTML discriminator: comment bodies come
    back as ``contentType: "html"`` while thread bodies use the MIME form
    ``"text/html"``. Both spellings (and ``text/html;charset=...``) are matched
    case-insensitively; a plain-text or unrecognized value is returned
    unchanged so callers can mirror it into a parallel text field.
    """
    if not isinstance(content, str):
        return None
    if not isinstance(content_type, str):
        return content
    normalized = content_type.strip().lower()
    is_html = normalized == "html" or normalized.startswith("text/html")
    return _html_to_text(content) if is_html else content


def _derive_description_text(record: dict[str, Any]) -> str | None:
    """Derive plain text for a ticket ``description``.

    Zoho ships no content-type discriminator for ticket descriptions and the
    shape is not consistently HTML — its own samples show both markup and
    plain sentences. Sniff for markup instead of converting unconditionally,
    so a plain description is never mangled. An explicit
    ``descriptionContentType`` still wins if Zoho ever starts sending one.
    """
    description = record.get("description")
    if not isinstance(description, str):
        return None
    declared = record.get("descriptionContentType")
    if isinstance(declared, str):
        return _derive_content_text(description, declared)
    return _html_to_text(description) if _looks_like_html(description) else description


# --- Resource parsers ------------------------------------------------------


def _opt_dict(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _parse_attachments(value: Any) -> list[ZohoAttachment]:
    if not isinstance(value, list):
        return []
    return [
        ZohoAttachment(
            id=item.get("id"),
            name=item.get("name"),
            size=item.get("size"),
            href=item.get("href"),
        )
        for item in value
        if isinstance(item, dict)
    ]


def _parse_user_ref(value: Any) -> ZohoUserRef | None:
    if not isinstance(value, dict):
        return None
    return ZohoUserRef(
        name=value.get("name"),
        first_name=value.get("firstName"),
        last_name=value.get("lastName"),
        email=value.get("email"),
        type=value.get("type"),
        role_name=value.get("roleName"),
        photo_url=value.get("photoURL"),
    )


def _parse_ticket(item: dict[str, Any]) -> ZohoTicket:
    return ZohoTicket(
        id=item.get("id"),
        ticket_number=item.get("ticketNumber"),
        subject=item.get("subject"),
        description=item.get("description"),
        description_text=_derive_description_text(item),
        status=item.get("status"),
        status_type=item.get("statusType"),
        priority=item.get("priority"),
        category=item.get("category"),
        sub_category=item.get("subCategory"),
        classification=item.get("classification"),
        channel=item.get("channel"),
        department_id=item.get("departmentId"),
        contact_id=item.get("contactId"),
        account_id=item.get("accountId"),
        assignee_id=item.get("assigneeId"),
        email=item.get("email"),
        phone=item.get("phone"),
        due_date=item.get("dueDate"),
        response_due_date=item.get("responseDueDate"),
        created_time=item.get("createdTime"),
        modified_time=item.get("modifiedTime"),
        closed_time=item.get("closedTime"),
        resolution=item.get("resolution"),
        thread_count=item.get("threadCount"),
        comment_count=item.get("commentCount"),
        web_url=item.get("webUrl"),
        is_escalated=item.get("isEscalated"),
        is_over_due=item.get("isOverDue"),
        is_spam=item.get("isSpam"),
        cf=_opt_dict(item.get("cf")),
        contact=_opt_dict(item.get("contact")),
        assignee=_opt_dict(item.get("assignee")),
    )


def _parse_comment(item: dict[str, Any]) -> ZohoComment:
    return ZohoComment(
        id=item.get("id"),
        content=item.get("content"),
        content_type=item.get("contentType"),
        content_text=_derive_content_text(item.get("content"), item.get("contentType")),
        is_public=item.get("isPublic"),
        commenter_id=item.get("commenterId"),
        commenter=_parse_user_ref(item.get("commenter")),
        commented_time=item.get("commentedTime"),
        modified_time=item.get("modifiedTime"),
        attachments=_parse_attachments(item.get("attachments")),
    )


def _parse_thread(item: dict[str, Any]) -> ZohoThread:
    return ZohoThread(
        id=item.get("id"),
        channel=item.get("channel"),
        direction=item.get("direction"),
        content=item.get("content"),
        content_type=item.get("contentType"),
        content_text=_derive_content_text(item.get("content"), item.get("contentType")),
        summary=item.get("summary"),
        responder_id=item.get("responderId"),
        created_time=item.get("createdTime"),
        has_attach=item.get("hasAttach"),
        attachment_count=item.get("attachmentCount"),
        from_email_address=item.get("fromEmailAddress"),
        to=item.get("to"),
        cc=item.get("cc"),
        bcc=item.get("bcc"),
        reply_to=item.get("replyTo"),
        is_forward=item.get("isForward"),
        is_content_truncated=item.get("isContentTruncated"),
        full_content_url=item.get("fullContentURL"),
        plain_text=item.get("plainText"),
        status=item.get("status"),
        is_description_thread=item.get("isDescriptionThread"),
        visibility=item.get("visibility"),
        can_reply=item.get("canReply"),
        author=_parse_user_ref(item.get("author")),
        attachments=_parse_attachments(item.get("attachments")),
    )


def _parse_contact(item: dict[str, Any]) -> ZohoContact:
    return ZohoContact(
        id=item.get("id"),
        first_name=item.get("firstName"),
        last_name=item.get("lastName"),
        email=item.get("email"),
        secondary_email=item.get("secondaryEmail"),
        phone=item.get("phone"),
        mobile=item.get("mobile"),
        account_id=item.get("accountId"),
        owner_id=item.get("ownerId"),
        type=item.get("type"),
        title=item.get("title"),
        street=item.get("street"),
        city=item.get("city"),
        state=item.get("state"),
        country=item.get("country"),
        zip=item.get("zip"),
        description=item.get("description"),
        cf=_opt_dict(item.get("cf")),
    )


def _parse_organization(item: dict[str, Any]) -> ZohoOrganization:
    return ZohoOrganization(
        id=item.get("id"),
        company_name=item.get("companyName"),
        portal_name=item.get("portalName"),
    )


# --- Input schemas ---------------------------------------------------------

_ORG_ID_DESCRIPTION = (
    "Zoho Desk organization (portal) ID. Optional — defaults to the"
    " organization configured on the credential; override it to work in"
    " another portal the same credential can reach (list_organizations"
    " enumerates them)."
)


class ListTicketsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    org_id: str | None = Field(default=None, description=_ORG_ID_DESCRIPTION)
    from_index: int | None = Field(
        default=None,
        description=(
            "Pagination start index, sent as the `from` query parameter"
            " (0-based, max 4999)"
        ),
    )
    limit: int | None = Field(
        default=None,
        description="Number of tickets to return (1-100, default 10)",
    )
    department_ids: str | None = Field(
        default=None,
        description="Filter by department ID (comma-separated for multiple)",
    )
    status: str | None = Field(
        default=None,
        description=(
            "Filter by status, including custom statuses. Comma-separate to"
            ' match multiple (e.g. "Open,On Hold")'
        ),
    )
    priority: str | None = Field(
        default=None,
        description='Filter by priority. Comma-separate to match multiple (e.g. "High,Urgent")',
    )
    sort_by: str | None = Field(
        default=None,
        description=(
            "Sort field: createdTime, customerResponseTime, or responseDueDate."
            " Prefix with - for descending."
        ),
    )
    include: str | None = Field(
        default=None,
        description=(
            "Comma-separated related data to embed. Allowed: contacts,"
            " products, departments, team, isRead, assignee"
        ),
    )


class GetTicketInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    ticket_id: str = Field(description="Ticket ID to retrieve")
    org_id: str | None = Field(default=None, description=_ORG_ID_DESCRIPTION)
    include: str | None = Field(
        default=None,
        description=(
            "Comma-separated related data to embed. Allowed: contacts,"
            " products, assignee, departments, contract, isRead, team, skills"
        ),
    )


class UpdateTicketInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    ticket_id: str = Field(description="Ticket ID to update")
    org_id: str | None = Field(default=None, description=_ORG_ID_DESCRIPTION)
    subject: str | None = Field(default=None, description="Ticket subject")
    status: str | None = Field(default=None, description="Ticket status (e.g. Open, Closed)")
    priority: str | None = Field(default=None, description="Ticket priority (e.g. High)")
    assignee_id: str | None = Field(default=None, description="Assignee (agent) ID")
    department_id: str | None = Field(default=None, description="Department ID")
    category: str | None = Field(default=None, description="Ticket category")
    sub_category: str | None = Field(default=None, description="Ticket sub-category")
    due_date: str | None = Field(default=None, description="Due date (ISO 8601)")
    description: str | None = Field(default=None, description="Ticket description")
    resolution: str | None = Field(
        default=None, description="Resolution notes recorded on the ticket"
    )
    classification: str | None = Field(
        default=None,
        description="Ticket classification: Problem, Request, Question, or Others",
    )
    custom_fields: dict[str, Any] | None = Field(
        default=None,
        description="Custom field values as a JSON object, keyed by custom field API name",
    )


class ListCommentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    ticket_id: str = Field(description="Ticket ID")
    org_id: str | None = Field(default=None, description=_ORG_ID_DESCRIPTION)
    from_index: int | None = Field(
        default=None,
        description="Pagination start index, sent as the `from` query parameter (0-based)",
    )
    limit: int | None = Field(
        default=None,
        description="Number of comments to return (1-100, default 50)",
    )


class AddCommentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    ticket_id: str = Field(description="Ticket ID")
    content: str = Field(description="Comment content")
    org_id: str | None = Field(default=None, description=_ORG_ID_DESCRIPTION)
    content_type: str | None = Field(
        default=None,
        description=(
            "Content type: plainText or html. Defaults to plainText so"
            " agent-written text posts literally; pass 'html' to send markup"
            " (the Zoho Desk API's own default is html)."
        ),
    )
    is_public: bool | None = Field(
        default=None, description="Whether the comment is public (default false)"
    )


class ListThreadsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    ticket_id: str = Field(description="Ticket ID")
    org_id: str | None = Field(default=None, description=_ORG_ID_DESCRIPTION)
    from_index: int | None = Field(
        default=None,
        description="Pagination start index, sent as the `from` query parameter (0-based)",
    )
    limit: int | None = Field(
        default=None,
        description="Number of threads to return (1-200, default 100)",
    )


class GetThreadInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    ticket_id: str = Field(description="Ticket ID")
    thread_id: str = Field(description="Thread ID")
    org_id: str | None = Field(default=None, description=_ORG_ID_DESCRIPTION)


class GetContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="Contact ID to retrieve")
    org_id: str | None = Field(default=None, description=_ORG_ID_DESCRIPTION)


class ListOrganizationsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=ListTicketsInput)
@serialize_pydantic_return
async def list_tickets(
    auth_type: str,
    auth_data: dict[str, Any],
    org_id: str | None = None,
    from_index: int | None = None,
    limit: int | None = None,
    department_ids: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    sort_by: str | None = None,
    include: str | None = None,
) -> ListTicketsOutput:
    """List tickets from a Zoho Desk organization with optional filters.

    Returns a list projection: description, resolution, statusType and
    classification are only available from get_ticket.
    """
    credential_error = _credential_error(auth_data)
    if credential_error:
        return ListTicketsOutput(success=False, error=credential_error)
    resolved_org = _resolve_org_id(org_id, auth_data)
    if not resolved_org:
        return ListTicketsOutput(success=False, error=_MISSING_ORG)

    params: dict[str, Any] = {}
    if from_index is not None:
        params["from"] = from_index
    if limit is not None:
        params["limit"] = limit
    # Zoho names this query param `departmentIds` (plural); a singular
    # `departmentId` is silently ignored and every department's tickets return.
    if department_ids:
        params["departmentIds"] = department_ids
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    if sort_by:
        params["sortBy"] = sort_by
    if include:
        params["include"] = include

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, token_error = await _mint_access_token(
                client, auth_data, resolved_org
            )
            if token is None:
                return ListTicketsOutput(success=False, error=token_error)
            response = await client.get(
                f"{_api_base(token.api_domain)}/tickets",
                headers=_desk_headers(token.access_token, resolved_org),
                params=params,
            )
    except httpx.TimeoutException:
        return ListTicketsOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return ListTicketsOutput(success=False, error=f"Failed to list tickets: {exc}")

    data = _json_body(response)
    if not _is_ok(response):
        return ListTicketsOutput(
            success=False,
            error=_error_message(data, f"Failed to list tickets (HTTP {response.status_code})"),
        )
    tickets = [_parse_ticket(item) for item in _records(data)]
    return ListTicketsOutput(success=True, tickets=tickets, count=len(tickets))


@tool(args_schema=GetTicketInput)
@serialize_pydantic_return
async def get_ticket(
    auth_type: str,
    auth_data: dict[str, Any],
    ticket_id: str,
    org_id: str | None = None,
    include: str | None = None,
) -> GetTicketOutput:
    """Retrieve a single Zoho Desk ticket by ID."""
    credential_error = _credential_error(auth_data)
    if credential_error:
        return GetTicketOutput(success=False, error=credential_error)
    resolved_org = _resolve_org_id(org_id, auth_data)
    if not resolved_org:
        return GetTicketOutput(success=False, error=_MISSING_ORG)
    clean_ticket_id = ticket_id.strip()
    if not clean_ticket_id:
        return GetTicketOutput(success=False, error="Ticket ID is required.")

    params: dict[str, Any] = {}
    if include:
        params["include"] = include

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, token_error = await _mint_access_token(
                client, auth_data, resolved_org
            )
            if token is None:
                return GetTicketOutput(success=False, error=token_error)
            response = await client.get(
                f"{_api_base(token.api_domain)}/tickets/{quote(clean_ticket_id, safe='')}",
                headers=_desk_headers(token.access_token, resolved_org),
                params=params,
            )
    except httpx.TimeoutException:
        return GetTicketOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return GetTicketOutput(success=False, error=f"Failed to get ticket: {exc}")

    data = _json_body(response)
    if not _is_ok(response):
        return GetTicketOutput(
            success=False,
            error=_error_message(data, f"Failed to get ticket (HTTP {response.status_code})"),
        )
    record = _as_dict(data)
    return GetTicketOutput(success=True, ticket=_parse_ticket(record), raw=record)


@tool(args_schema=UpdateTicketInput)
@serialize_pydantic_return
async def update_ticket(
    auth_type: str,
    auth_data: dict[str, Any],
    ticket_id: str,
    org_id: str | None = None,
    subject: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    assignee_id: str | None = None,
    department_id: str | None = None,
    category: str | None = None,
    sub_category: str | None = None,
    due_date: str | None = None,
    description: str | None = None,
    resolution: str | None = None,
    classification: str | None = None,
    custom_fields: dict[str, Any] | None = None,
) -> UpdateTicketOutput:
    """Update fields on an existing Zoho Desk ticket."""
    credential_error = _credential_error(auth_data)
    if credential_error:
        return UpdateTicketOutput(success=False, error=credential_error)
    resolved_org = _resolve_org_id(org_id, auth_data)
    if not resolved_org:
        return UpdateTicketOutput(success=False, error=_MISSING_ORG)
    clean_ticket_id = ticket_id.strip()
    if not clean_ticket_id:
        return UpdateTicketOutput(success=False, error="Ticket ID is required.")

    # Only fields the caller actually set are sent, so a status-only update
    # cannot blank the subject. An empty string is NOT treated as unset —
    # Zoho documents "" as its idiom for clearing a field.
    candidates: dict[str, Any] = {
        "subject": subject,
        "status": status,
        "priority": priority,
        "assigneeId": assignee_id,
        "departmentId": department_id,
        "category": category,
        "subCategory": sub_category,
        "dueDate": due_date,
        "description": description,
        "resolution": resolution,
        "classification": classification,
        # The ticket PATCH names the custom-field object `cf`; `customFields`
        # is only a deprecated alias on other Desk resources and is silently
        # ignored here, so the update would report success without applying.
        "cf": custom_fields,
    }
    body: dict[str, Any] = {key: value for key, value in candidates.items() if value is not None}
    if not body:
        return UpdateTicketOutput(
            success=False,
            error=(
                "No fields to update. Provide at least one field to change"
                " (e.g. status, priority, or subject)."
            ),
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, token_error = await _mint_access_token(
                client, auth_data, resolved_org
            )
            if token is None:
                return UpdateTicketOutput(success=False, error=token_error)
            response = await client.patch(
                f"{_api_base(token.api_domain)}/tickets/{quote(clean_ticket_id, safe='')}",
                headers=_desk_headers(token.access_token, resolved_org),
                json=body,
            )
    except httpx.TimeoutException:
        return UpdateTicketOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return UpdateTicketOutput(success=False, error=f"Failed to update ticket: {exc}")

    data = _json_body(response)
    if not _is_ok(response):
        return UpdateTicketOutput(
            success=False,
            error=_error_message(data, f"Failed to update ticket (HTTP {response.status_code})"),
        )
    record = _as_dict(data)
    return UpdateTicketOutput(success=True, ticket=_parse_ticket(record), raw=record)


@tool(args_schema=ListCommentsInput)
@serialize_pydantic_return
async def list_comments(
    auth_type: str,
    auth_data: dict[str, Any],
    ticket_id: str,
    org_id: str | None = None,
    from_index: int | None = None,
    limit: int | None = None,
) -> ListCommentsOutput:
    """List comments on a Zoho Desk ticket."""
    credential_error = _credential_error(auth_data)
    if credential_error:
        return ListCommentsOutput(success=False, error=credential_error)
    resolved_org = _resolve_org_id(org_id, auth_data)
    if not resolved_org:
        return ListCommentsOutput(success=False, error=_MISSING_ORG)
    clean_ticket_id = ticket_id.strip()
    if not clean_ticket_id:
        return ListCommentsOutput(success=False, error="Ticket ID is required.")

    params: dict[str, Any] = {}
    if from_index is not None:
        params["from"] = from_index
    if limit is not None:
        params["limit"] = limit

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, token_error = await _mint_access_token(
                client, auth_data, resolved_org
            )
            if token is None:
                return ListCommentsOutput(success=False, error=token_error)
            response = await client.get(
                f"{_api_base(token.api_domain)}/tickets/{quote(clean_ticket_id, safe='')}/comments",
                headers=_desk_headers(token.access_token, resolved_org),
                params=params,
            )
    except httpx.TimeoutException:
        return ListCommentsOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return ListCommentsOutput(success=False, error=f"Failed to list comments: {exc}")

    data = _json_body(response)
    if not _is_ok(response):
        return ListCommentsOutput(
            success=False,
            error=_error_message(data, f"Failed to list comments (HTTP {response.status_code})"),
        )
    comments = [_parse_comment(item) for item in _records(data)]
    return ListCommentsOutput(success=True, comments=comments, count=len(comments))


@tool(args_schema=AddCommentInput)
@serialize_pydantic_return
async def add_comment(
    auth_type: str,
    auth_data: dict[str, Any],
    ticket_id: str,
    content: str,
    org_id: str | None = None,
    content_type: str | None = None,
    is_public: bool | None = None,
) -> AddCommentOutput:
    """Add a comment to a Zoho Desk ticket."""
    credential_error = _credential_error(auth_data)
    if credential_error:
        return AddCommentOutput(success=False, error=credential_error)
    resolved_org = _resolve_org_id(org_id, auth_data)
    if not resolved_org:
        return AddCommentOutput(success=False, error=_MISSING_ORG)
    clean_ticket_id = ticket_id.strip()
    if not clean_ticket_id:
        return AddCommentOutput(success=False, error="Ticket ID is required.")

    body: dict[str, Any] = {
        "content": content,
        "contentType": content_type or "plainText",
        "isPublic": False if is_public is None else is_public,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, token_error = await _mint_access_token(
                client, auth_data, resolved_org
            )
            if token is None:
                return AddCommentOutput(success=False, error=token_error)
            response = await client.post(
                f"{_api_base(token.api_domain)}/tickets/{quote(clean_ticket_id, safe='')}/comments",
                headers=_desk_headers(token.access_token, resolved_org),
                json=body,
            )
    except httpx.TimeoutException:
        return AddCommentOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return AddCommentOutput(success=False, error=f"Failed to add comment: {exc}")

    data = _json_body(response)
    if not _is_ok(response):
        return AddCommentOutput(
            success=False,
            error=_error_message(data, f"Failed to add comment (HTTP {response.status_code})"),
        )
    record = _as_dict(data)
    return AddCommentOutput(success=True, comment=_parse_comment(record), raw=record)


@tool(args_schema=ListThreadsInput)
@serialize_pydantic_return
async def list_threads(
    auth_type: str,
    auth_data: dict[str, Any],
    ticket_id: str,
    org_id: str | None = None,
    from_index: int | None = None,
    limit: int | None = None,
) -> ListThreadsOutput:
    """List conversation threads on a Zoho Desk ticket, newest first.

    Returns a list projection: message bodies (content, summary, to/cc/bcc)
    come back only from get_thread.
    """
    credential_error = _credential_error(auth_data)
    if credential_error:
        return ListThreadsOutput(success=False, error=credential_error)
    resolved_org = _resolve_org_id(org_id, auth_data)
    if not resolved_org:
        return ListThreadsOutput(success=False, error=_MISSING_ORG)
    clean_ticket_id = ticket_id.strip()
    if not clean_ticket_id:
        return ListThreadsOutput(success=False, error="Ticket ID is required.")

    params: dict[str, Any] = {}
    if from_index is not None:
        params["from"] = from_index
    if limit is not None:
        params["limit"] = limit

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, token_error = await _mint_access_token(
                client, auth_data, resolved_org
            )
            if token is None:
                return ListThreadsOutput(success=False, error=token_error)
            response = await client.get(
                f"{_api_base(token.api_domain)}/tickets/{quote(clean_ticket_id, safe='')}/threads",
                headers=_desk_headers(token.access_token, resolved_org),
                params=params,
            )
    except httpx.TimeoutException:
        return ListThreadsOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return ListThreadsOutput(success=False, error=f"Failed to list threads: {exc}")

    data = _json_body(response)
    if not _is_ok(response):
        return ListThreadsOutput(
            success=False,
            error=_error_message(data, f"Failed to list threads (HTTP {response.status_code})"),
        )
    threads = [_parse_thread(item) for item in _records(data)]
    return ListThreadsOutput(success=True, threads=threads, count=len(threads))


@tool(args_schema=GetThreadInput)
@serialize_pydantic_return
async def get_thread(
    auth_type: str,
    auth_data: dict[str, Any],
    ticket_id: str,
    thread_id: str,
    org_id: str | None = None,
) -> GetThreadOutput:
    """Retrieve the full content of a single Zoho Desk ticket thread."""
    credential_error = _credential_error(auth_data)
    if credential_error:
        return GetThreadOutput(success=False, error=credential_error)
    resolved_org = _resolve_org_id(org_id, auth_data)
    if not resolved_org:
        return GetThreadOutput(success=False, error=_MISSING_ORG)
    clean_ticket_id = ticket_id.strip()
    clean_thread_id = thread_id.strip()
    if not clean_ticket_id:
        return GetThreadOutput(success=False, error="Ticket ID is required.")
    if not clean_thread_id:
        return GetThreadOutput(success=False, error="Thread ID is required.")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, token_error = await _mint_access_token(
                client, auth_data, resolved_org
            )
            if token is None:
                return GetThreadOutput(success=False, error=token_error)
            url = (
                f"{_api_base(token.api_domain)}/tickets/{quote(clean_ticket_id, safe='')}"
                f"/threads/{quote(clean_thread_id, safe='')}"
            )
            response = await client.get(
                url,
                headers=_desk_headers(token.access_token, resolved_org),
            )
    except httpx.TimeoutException:
        return GetThreadOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return GetThreadOutput(success=False, error=f"Failed to get thread: {exc}")

    data = _json_body(response)
    if not _is_ok(response):
        return GetThreadOutput(
            success=False,
            error=_error_message(data, f"Failed to get thread (HTTP {response.status_code})"),
        )
    record = _as_dict(data)
    return GetThreadOutput(success=True, thread=_parse_thread(record), raw=record)


@tool(args_schema=GetContactInput)
@serialize_pydantic_return
async def get_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    org_id: str | None = None,
) -> GetContactOutput:
    """Retrieve a Zoho Desk contact by ID."""
    credential_error = _credential_error(auth_data)
    if credential_error:
        return GetContactOutput(success=False, error=credential_error)
    resolved_org = _resolve_org_id(org_id, auth_data)
    if not resolved_org:
        return GetContactOutput(success=False, error=_MISSING_ORG)
    clean_contact_id = contact_id.strip()
    if not clean_contact_id:
        return GetContactOutput(success=False, error="Contact ID is required.")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, token_error = await _mint_access_token(
                client, auth_data, resolved_org
            )
            if token is None:
                return GetContactOutput(success=False, error=token_error)
            response = await client.get(
                f"{_api_base(token.api_domain)}/contacts/{quote(clean_contact_id, safe='')}",
                headers=_desk_headers(token.access_token, resolved_org),
            )
    except httpx.TimeoutException:
        return GetContactOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return GetContactOutput(success=False, error=f"Failed to get contact: {exc}")

    data = _json_body(response)
    if not _is_ok(response):
        return GetContactOutput(
            success=False,
            error=_error_message(data, f"Failed to get contact (HTTP {response.status_code})"),
        )
    record = _as_dict(data)
    return GetContactOutput(success=True, contact=_parse_contact(record), raw=record)


@tool(args_schema=ListOrganizationsInput)
@serialize_pydantic_return
async def list_organizations(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListOrganizationsOutput:
    """List the Zoho Desk organizations (portals) the connected account can access."""
    credential_error = _credential_error(auth_data)
    if credential_error:
        return ListOrganizationsOutput(success=False, error=credential_error)
    # The endpoint itself needs no organization, but the token request does:
    # `soid` is what scopes the minted token to a portal.
    resolved_org = _resolve_org_id(None, auth_data)
    if not resolved_org:
        return ListOrganizationsOutput(success=False, error=_MISSING_ORG)

    # The organizations endpoint is the only Desk call that does not require
    # the orgId header. No query params: none are documented for
    # /organizations and passing an unsupported one risks a 422 on the call
    # that enumerates every other organization the credential can reach.
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, token_error = await _mint_access_token(
                client, auth_data, resolved_org
            )
            if token is None:
                return ListOrganizationsOutput(success=False, error=token_error)
            response = await client.get(
                f"{_api_base(token.api_domain)}/organizations",
                headers=_desk_headers(token.access_token),
            )
    except httpx.TimeoutException:
        return ListOrganizationsOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return ListOrganizationsOutput(
            success=False, error=f"Failed to list organizations: {exc}"
        )

    data = _json_body(response)
    if not _is_ok(response):
        return ListOrganizationsOutput(
            success=False,
            error=_error_message(
                data, f"Failed to list organizations (HTTP {response.status_code})"
            ),
        )
    organizations = [_parse_organization(item) for item in _records(data)]
    return ListOrganizationsOutput(
        success=True, organizations=organizations, count=len(organizations)
    )
