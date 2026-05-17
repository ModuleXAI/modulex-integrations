"""Microsoft Outlook LangChain @tool functions.

API Documentation: https://learn.microsoft.com/en-us/graph/api/resources/mail-api-overview
"""
from __future__ import annotations

import base64
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.microsoft_outlook.outputs import (
    AddLabelToEmailOutput,
    ApproveWorkflowOutput,
    ContactSummary,
    CreateContactOutput,
    CreateDraftEmailOutput,
    CreateDraftReplyOutput,
    DownloadAttachmentOutput,
    FindContactsOutput,
    FindEmailOutput,
    FindSharedFolderEmailOutput,
    GetCurrentUserOutput,
    GetMessageOutput,
    ImportantMailItem,
    ListContactsOutput,
    ListFoldersOutput,
    ListImportantMailOutput,
    ListLabelsOutput,
    MoveEmailToFolderOutput,
    RemoveLabelFromEmailOutput,
    ReplyToEmailOutput,
    SendEmailOutput,
    UpdateContactOutput,
)

__all__ = [
    "add_label_to_email",
    "approve_workflow",
    "create_contact",
    "create_draft_email",
    "create_draft_reply",
    "download_attachment",
    "find_contacts",
    "find_email",
    "find_shared_folder_email",
    "get_current_user",
    "get_message",
    "list_contacts",
    "list_folders",
    "list_important_mail",
    "list_labels",
    "move_email_to_folder",
    "remove_label_from_email",
    "reply_to_email",
    "send_email",
    "update_contact",
]

_BASE_URL = "https://graph.microsoft.com/v1.0"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for Microsoft Graph based on auth_type/auth_data."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _check_auth(auth_type: str, auth_data: dict[str, Any]) -> str | None:
    """Return an error message if credentials are missing/empty, else None."""
    if auth_type == "oauth2":
        token = auth_data.get("access_token")
        if not token or not str(token).strip():
            return "Missing or empty access_token in auth_data."
    return None


def _user_path(user_id: str | None) -> str:
    """Mirror the pipedream `_userPath(userId)` helper."""
    return f"/users/{user_id}" if user_id else "/me"


def _build_recipients(addresses: list[str] | None) -> list[dict[str, Any]]:
    """Convert a list of plain email strings into Microsoft Graph recipient objects."""
    if not addresses:
        return []
    return [
        {"emailAddress": {"address": a}}
        for a in addresses
        if isinstance(a, str) and a.strip()
    ]


async def _build_attachments_from_urls(file_urls: list[str] | None) -> list[dict[str, Any]]:
    """Fetch each URL and produce a Microsoft Graph fileAttachment payload (base64)."""
    attachments: list[dict[str, Any]] = []
    if not file_urls:
        return attachments
    async with httpx.AsyncClient(timeout=60.0) as client:
        for url in file_urls:
            if not url or not isinstance(url, str):
                continue
            resp = await client.get(url)
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Failed to fetch attachment {url}: {resp.status_code} - {resp.text[:200]}"
                )
            content_type = resp.headers.get("Content-Type", "application/octet-stream")
            name = url.rsplit("/", 1)[-1].split("?", 1)[0] or f"attachment-{len(attachments) + 1}"
            attachments.append(
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": name,
                    "contentType": content_type,
                    "contentBytes": base64.b64encode(resp.content).decode("ascii"),
                }
            )
    return attachments


async def _build_message_body(
    recipients: list[str] | None,
    cc_recipients: list[str] | None,
    bcc_recipients: list[str] | None,
    subject: str | None,
    content: str | None,
    content_type: str | None,
    file_urls: list[str] | None,
) -> dict[str, Any]:
    """Translate of `microsoftOutlook.prepareMessageBody`."""
    attachments = await _build_attachments_from_urls(file_urls)
    message: dict[str, Any] = {"subject": subject, "attachments": attachments}
    if content:
        message["body"] = {"content": content, "contentType": content_type or "text"}
    to_list = _build_recipients(recipients)
    cc_list = _build_recipients(cc_recipients)
    bcc_list = _build_recipients(bcc_recipients)
    if to_list:
        message["toRecipients"] = to_list
    if cc_list:
        message["ccRecipients"] = cc_list
    if bcc_list:
        message["bccRecipients"] = bcc_list
    return message


async def _paginated_get(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    params: dict[str, Any],
    max_results: int,
    max_pages: int = 50,
) -> list[dict[str, Any]]:
    """Walk Graph's `@odata.nextLink` pagination, capping at `max_results`."""
    items: list[dict[str, Any]] = []
    next_url: str | None = url
    next_params: dict[str, Any] | None = {k: v for k, v in params.items() if v is not None}
    pages_seen = 0
    while next_url and pages_seen < max_pages:
        resp = await client.get(next_url, headers=headers, params=next_params)
        if resp.status_code >= 400:
            raise RuntimeError(f"{resp.status_code} - {resp.text}")
        payload = resp.json()
        for item in payload.get("value", []) or []:
            items.append(item)
            if max_results and len(items) >= max_results:
                return items
        next_url = payload.get("@odata.nextLink")
        next_params = None
        pages_seen += 1
    return items


async def _list_all_folders(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    parent_folder_id: str | None,
    include_hidden: bool,
    _depth: int = 0,
) -> list[dict[str, Any]]:
    """Recursive translate of `listAllFolders`."""
    if _depth > 10:
        return []
    path = (
        f"/me/mailFolders/{parent_folder_id}/childFolders"
        if parent_folder_id
        else "/me/mailFolders"
    )
    params: dict[str, Any] = {"$top": 50}
    if include_hidden:
        params["includeHiddenFolders"] = "true"
    resp = await client.get(f"{_BASE_URL}{path}", headers=headers, params=params)
    if resp.status_code >= 400:
        raise RuntimeError(f"{resp.status_code} - {resp.text}")
    folders: list[dict[str, Any]] = []
    for f in resp.json().get("value", []) or []:
        folders.append(f)
        folders.extend(await _list_all_folders(client, headers, f.get("id"), include_hidden, _depth + 1))
    return folders


# ==================== Pydantic Input Schemas ====================


class AddLabelToEmailInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="The identifier of the message to update.")
    label: str = Field(description="The name of the label/category to add.")
    user_id: str | None = Field(default=None, description="User ID of a shared mailbox. Defaults to /me.")


class ApproveWorkflowInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    recipients: list[str] = Field(description="Recipient email addresses.")
    subject: str = Field(description="Subject of the approval email.")
    resume_url: str = Field(description="URL the recipient clicks to approve / resume the workflow.")
    cancel_url: str = Field(description="URL the recipient clicks to cancel the workflow.")
    user_id: str | None = Field(default=None, description="User ID of a shared mailbox.")


class CreateContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    given_name: str | None = Field(default=None, description="Given name of the contact.")
    surname: str | None = Field(default=None, description="Surname of the contact.")
    email_addresses: list[str] | None = Field(default=None, description="Email addresses for the contact.")
    business_phones: list[str] | None = Field(default=None, description="Phone numbers.")
    expand: dict[str, Any] | None = Field(default=None, description="Additional contact fields.")


class CreateDraftEmailInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    recipients: list[str] | None = Field(default=None, description="TO recipients.")
    cc_recipients: list[str] | None = Field(default=None, description="CC recipients.")
    bcc_recipients: list[str] | None = Field(default=None, description="BCC recipients.")
    subject: str | None = Field(default=None, description="Subject of the email.")
    content_type: str | None = Field(default="text", description="Content type (text or html).")
    content: str | None = Field(default=None, description="Body content.")
    file_urls: list[str] | None = Field(default=None, description="File URLs to attach.")
    expand: dict[str, Any] | None = Field(default=None, description="Extra Message fields.")
    user_id: str | None = Field(default=None, description="Shared mailbox User ID.")


class CreateDraftReplyInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="The identifier of the message to reply to.")
    comment: str | None = Field(default=None, description="Plain-text reply content.")
    recipients: list[str] | None = Field(default=None, description="Override TO recipients.")
    cc_recipients: list[str] | None = Field(default=None, description="CC recipients.")
    bcc_recipients: list[str] | None = Field(default=None, description="BCC recipients.")
    subject: str | None = Field(default=None, description="Subject override.")
    file_urls: list[str] | None = Field(default=None, description="File URLs to attach.")
    expand: dict[str, Any] | None = Field(default=None, description="Extra Message fields.")
    user_id: str | None = Field(default=None, description="Shared mailbox User ID.")


class DownloadAttachmentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="ID of the message containing the attachment.")
    attachment_id: str = Field(description="ID of the attachment to download.")
    user_id: str | None = Field(default=None, description="Shared mailbox User ID.")


class FindContactsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    search_string: str = Field(description="Email address, given name, surname, or display name (case sensitive).")
    max_results: int = Field(default=100, description="Maximum number of results to return.")


class FindEmailInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    search: str | None = Field(default=None, description="Search query.")
    filter: str | None = Field(default=None, description="OData $filter expression.")
    order_by: str | None = Field(default=None, description="OData $orderby expression.")
    max_results: int = Field(default=100, description="Maximum number of messages.")
    include_attachments: bool = Field(default=False, description="If true, expand attachments.")
    select: str | None = Field(default=None, description="Comma-separated property names.")
    user_id: str | None = Field(default=None, description="Shared mailbox User ID.")


class FindSharedFolderEmailInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str = Field(description="User ID owning the shared folder.")
    shared_folder_id: str = Field(description="ID of the shared folder.")
    search: str | None = Field(default=None, description="Search query.")
    filter: str | None = Field(default=None, description="OData $filter expression.")
    order_by: str | None = Field(default=None, description="OData $orderby expression.")
    max_results: int = Field(default=100, description="Maximum number of messages.")


class GetCurrentUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class GetMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="The Microsoft Graph message ID.")
    include_attachments: bool = Field(default=False, description="If true, expand attachments.")
    user_id: str | None = Field(default=None, description="Shared mailbox User ID.")


class ListContactsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    filter_address: str | None = Field(default=None, description="Filter contacts by email address.")
    max_results: int = Field(default=100, description="Maximum number of contacts.")


class ListFoldersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    max_results: int = Field(default=100, description="Maximum number of folders.")
    include_subfolders: bool = Field(default=False, description="Recursively include subfolders.")
    include_hidden_folders: bool = Field(default=False, description="Include hidden folders.")


class ListImportantMailInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    max_results: int = Field(default=100, description="Maximum number of messages.")
    user_id: str | None = Field(default=None, description="Shared mailbox User ID.")


class ListLabelsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str | None = Field(default=None, description="Shared mailbox User ID.")


class MoveEmailToFolderInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="Message to move.")
    folder_id: str = Field(description="Destination folder ID.")
    user_id: str | None = Field(default=None, description="Shared mailbox User ID.")


class RemoveLabelFromEmailInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="The identifier of the message to update.")
    label: str = Field(description="The name of the label/category to remove.")
    user_id: str | None = Field(default=None, description="Shared mailbox User ID.")


class ReplyToEmailInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message_id: str = Field(description="The identifier of the message to reply to.")
    comment: str | None = Field(default=None, description="Plain-text reply content.")
    recipients: list[str] | None = Field(default=None, description="Override TO recipients.")
    cc_recipients: list[str] | None = Field(default=None, description="CC recipients.")
    bcc_recipients: list[str] | None = Field(default=None, description="BCC recipients.")
    subject: str | None = Field(default=None, description="Subject override.")
    file_urls: list[str] | None = Field(default=None, description="File URLs to attach.")
    expand: dict[str, Any] | None = Field(default=None, description="Extra Message fields.")
    user_id: str | None = Field(default=None, description="Shared mailbox User ID.")


class SendEmailInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    recipients: list[str] | None = Field(default=None, description="TO recipients.")
    cc_recipients: list[str] | None = Field(default=None, description="CC recipients.")
    bcc_recipients: list[str] | None = Field(default=None, description="BCC recipients.")
    subject: str | None = Field(default=None, description="Subject of the email.")
    content_type: str | None = Field(default="text", description="Content type (text or html).")
    content: str | None = Field(default=None, description="Body content.")
    file_urls: list[str] | None = Field(default=None, description="File URLs to attach.")
    expand: dict[str, Any] | None = Field(default=None, description="Extra Message fields.")
    user_id: str | None = Field(default=None, description="Shared mailbox User ID.")


class UpdateContactInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    contact_id: str = Field(description="The ID of the contact to update.")
    given_name: str | None = Field(default=None, description="Given name.")
    surname: str | None = Field(default=None, description="Surname.")
    email_addresses: list[str] | None = Field(default=None, description="Replacement email addresses.")
    business_phones: list[str] | None = Field(default=None, description="Replacement phone numbers.")
    expand: dict[str, Any] | None = Field(default=None, description="Additional contact fields.")


# ==================== Tool Functions ====================


@tool(args_schema=AddLabelToEmailInput)
@serialize_pydantic_return
async def add_label_to_email(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    label: str,
    user_id: str | None = None,
) -> AddLabelToEmailOutput:
    """Adds a label/category to an email in Microsoft Outlook."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return AddLabelToEmailOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    base = f"{_BASE_URL}{_user_path(user_id)}/messages/{message_id}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        get_resp = await client.get(base, headers=headers)
        if get_resp.status_code >= 400:
            return AddLabelToEmailOutput(
                success=False,
                error=f"API error fetching message: {get_resp.status_code} - {get_resp.text}",
            )
        categories = get_resp.json().get("categories", []) or []
        if label in categories:
            return AddLabelToEmailOutput(
                success=False,
                error=f'Message already contains label "{label}".',
            )
        new_categories = [*categories, label]
        patch_resp = await client.patch(
            base, headers=headers, json={"categories": new_categories}
        )
        if patch_resp.status_code >= 400:
            return AddLabelToEmailOutput(
                success=False,
                error=f"API error: {patch_resp.status_code} - {patch_resp.text}",
            )
        data = patch_resp.json()
    return AddLabelToEmailOutput(
        success=True,
        id=data.get("id"),
        subject=data.get("subject"),
        categories=data.get("categories", []) or [],
    )


@tool(args_schema=ApproveWorkflowInput)
@serialize_pydantic_return
async def approve_workflow(
    auth_type: str,
    auth_data: dict[str, Any],
    recipients: list[str],
    subject: str,
    resume_url: str,
    cancel_url: str,
    user_id: str | None = None,
) -> ApproveWorkflowOutput:
    """Send an email containing approve/cancel URLs to a recipient so they can resume or cancel a workflow externally."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return ApproveWorkflowOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    content = (
        f"Click here to approve the workflow: {resume_url}\n"
        f"Cancel here: {cancel_url}"
    )
    try:
        message = await _build_message_body(
            recipients=recipients,
            cc_recipients=None,
            bcc_recipients=None,
            subject=subject,
            content=content,
            content_type="text",
            file_urls=None,
        )
    except RuntimeError as exc:
        return ApproveWorkflowOutput(success=False, error=str(exc))
    url = f"{_BASE_URL}{_user_path(user_id)}/sendMail"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json={"message": message})
        if resp.status_code >= 400:
            return ApproveWorkflowOutput(
                success=False,
                error=f"API error: {resp.status_code} - {resp.text}",
            )
    return ApproveWorkflowOutput(success=True, sent=True)


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    given_name: str | None = None,
    surname: str | None = None,
    email_addresses: list[str] | None = None,
    business_phones: list[str] | None = None,
    expand: dict[str, Any] | None = None,
) -> CreateContactOutput:
    """Add a contact to the root Contacts folder."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return CreateContactOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {}
    if given_name is not None:
        body["givenName"] = given_name
    if surname is not None:
        body["surname"] = surname
    if email_addresses:
        body["emailAddresses"] = [
            {"address": a, "name": f"Email #{i + 1}"}
            for i, a in enumerate(email_addresses)
        ]
    if business_phones is not None:
        body["businessPhones"] = business_phones
    if expand:
        body.update(expand)
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(f"{_BASE_URL}/me/contacts", headers=headers, json=body)
        if resp.status_code >= 400:
            return CreateContactOutput(
                success=False,
                error=f"API error: {resp.status_code} - {resp.text}",
            )
        data = resp.json()
    return CreateContactOutput(
        success=True,
        contact=ContactSummary(
            id=data.get("id"),
            displayName=data.get("displayName"),
            givenName=data.get("givenName"),
            surname=data.get("surname"),
            emailAddresses=data.get("emailAddresses", []) or [],
            businessPhones=data.get("businessPhones", []) or [],
        ),
    )


@tool(args_schema=CreateDraftEmailInput)
@serialize_pydantic_return
async def create_draft_email(
    auth_type: str,
    auth_data: dict[str, Any],
    recipients: list[str] | None = None,
    cc_recipients: list[str] | None = None,
    bcc_recipients: list[str] | None = None,
    subject: str | None = None,
    content_type: str | None = "text",
    content: str | None = None,
    file_urls: list[str] | None = None,
    expand: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> CreateDraftEmailOutput:
    """Create a draft email."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return CreateDraftEmailOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        body = await _build_message_body(
            recipients, cc_recipients, bcc_recipients, subject, content, content_type, file_urls
        )
    except RuntimeError as exc:
        return CreateDraftEmailOutput(success=False, error=str(exc))
    if expand:
        body.update(expand)
    url = f"{_BASE_URL}{_user_path(user_id)}/messages"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=body)
        if resp.status_code >= 400:
            return CreateDraftEmailOutput(
                success=False,
                error=f"API error: {resp.status_code} - {resp.text}",
            )
        data = resp.json()
    return CreateDraftEmailOutput(
        success=True,
        id=data.get("id"),
        subject=data.get("subject"),
        isDraft=data.get("isDraft"),
        webLink=data.get("webLink"),
    )


@tool(args_schema=CreateDraftReplyInput)
@serialize_pydantic_return
async def create_draft_reply(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    comment: str | None = None,
    recipients: list[str] | None = None,
    cc_recipients: list[str] | None = None,
    bcc_recipients: list[str] | None = None,
    subject: str | None = None,
    file_urls: list[str] | None = None,
    expand: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> CreateDraftReplyOutput:
    """Create a draft reply to an email."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return CreateDraftReplyOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        message = await _build_message_body(
            recipients, cc_recipients, bcc_recipients, subject, comment, "text", file_urls
        )
    except RuntimeError as exc:
        return CreateDraftReplyOutput(success=False, error=str(exc))
    if expand:
        message.update(expand)
    payload: dict[str, Any] = {"comment": comment or "", "message": message}
    url = f"{_BASE_URL}{_user_path(user_id)}/messages/{message_id}/createReply"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            return CreateDraftReplyOutput(
                success=False,
                error=f"API error: {resp.status_code} - {resp.text}",
            )
        data = resp.json()
    return CreateDraftReplyOutput(
        success=True,
        id=data.get("id"),
        subject=data.get("subject"),
        isDraft=data.get("isDraft"),
    )


@tool(args_schema=DownloadAttachmentInput)
@serialize_pydantic_return
async def download_attachment(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    attachment_id: str,
    user_id: str | None = None,
) -> DownloadAttachmentOutput:
    """Download a Microsoft Outlook attachment and return it base64-encoded with metadata."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return DownloadAttachmentOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    info_url = (
        f"{_BASE_URL}{_user_path(user_id)}/messages/{message_id}/attachments/{attachment_id}"
    )
    async with httpx.AsyncClient(timeout=120.0) as client:
        info_resp = await client.get(info_url, headers=headers)
        if info_resp.status_code >= 400:
            return DownloadAttachmentOutput(
                success=False,
                error=f"API error: {info_resp.status_code} - {info_resp.text}",
            )
        info = info_resp.json()
        content_bytes_b64 = info.get("contentBytes")
        if not content_bytes_b64:
            value_resp = await client.get(f"{info_url}/$value", headers=headers)
            if value_resp.status_code >= 400:
                return DownloadAttachmentOutput(
                    success=False,
                    error=f"API error: {value_resp.status_code} - {value_resp.text}",
                )
            content_bytes_b64 = base64.b64encode(value_resp.content).decode("ascii")
    return DownloadAttachmentOutput(
        success=True,
        name=info.get("name"),
        content_type=info.get("contentType"),
        size=info.get("size"),
        content_bytes_base64=content_bytes_b64,
    )


@tool(args_schema=FindContactsInput)
@serialize_pydantic_return
async def find_contacts(
    auth_type: str,
    auth_data: dict[str, Any],
    search_string: str,
    max_results: int = 100,
) -> FindContactsOutput:
    """Finds contacts with the given search string."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return FindContactsOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            all_contacts = await _paginated_get(
                client,
                f"{_BASE_URL}/me/contacts",
                headers,
                {"$top": 50},
                max_results=0,
            )
        except RuntimeError as exc:
            return FindContactsOutput(success=False, error=f"API error: {exc}")
    matched: list[dict[str, Any]] = []
    for c in all_contacts:
        emails = c.get("emailAddresses") or []
        if (
            (c.get("displayName") and search_string in c["displayName"])
            or (c.get("givenName") and search_string in c["givenName"])
            or (c.get("surname") and search_string in c["surname"])
            or any(
                (e.get("address") == search_string)
                or (e.get("name") and search_string in e["name"])
                for e in emails
            )
        ):
            matched.append(c)
            if max_results and len(matched) >= max_results:
                break
    return FindContactsOutput(
        success=True,
        count=len(matched),
        contacts=matched,
    )


@tool(args_schema=FindEmailInput)
@serialize_pydantic_return
async def find_email(
    auth_type: str,
    auth_data: dict[str, Any],
    search: str | None = None,
    filter: str | None = None,
    order_by: str | None = None,
    max_results: int = 100,
    include_attachments: bool = False,
    select: str | None = None,
    user_id: str | None = None,
) -> FindEmailOutput:
    """Search for an email in Microsoft Outlook."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return FindEmailOutput(success=False, error=auth_err)
    if search and (filter or order_by):
        return FindEmailOutput(
            success=False,
            error="`search` is not supported when using `filter` or `order_by`.",
        )
    headers = _get_auth_headers(auth_type, auth_data)
    if search:
        headers = {**headers, "ConsistencyLevel": "eventual"}
    normalized_select = None
    if select and select.strip():
        normalized_select = ",".join(
            p.strip() for p in select.split(",") if p.strip()
        )
    params: dict[str, Any] = {}
    if search:
        s = search.strip().strip('"').strip("'")
        params["$search"] = f'"{s}"'
        params["$top"] = max_results
    else:
        if filter:
            params["$filter"] = filter
        if order_by:
            params["$orderby"] = order_by
    if normalized_select:
        params["$select"] = normalized_select
    if include_attachments:
        params["$expand"] = "attachments"
    url = f"{_BASE_URL}{_user_path(user_id)}/messages"
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            if search:
                resp = await client.get(url, headers=headers, params=params)
                if resp.status_code >= 400:
                    return FindEmailOutput(
                        success=False,
                        error=f"API error: {resp.status_code} - {resp.text}",
                    )
                messages = resp.json().get("value", []) or []
            else:
                messages = await _paginated_get(client, url, headers, params, max_results)
        except RuntimeError as exc:
            return FindEmailOutput(success=False, error=f"API error: {exc}")
    return FindEmailOutput(
        success=True,
        count=len(messages),
        messages=messages,
    )


@tool(args_schema=FindSharedFolderEmailInput)
@serialize_pydantic_return
async def find_shared_folder_email(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str,
    shared_folder_id: str,
    search: str | None = None,
    filter: str | None = None,
    order_by: str | None = None,
    max_results: int = 100,
) -> FindSharedFolderEmailOutput:
    """Search for an email in a shared folder."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return FindSharedFolderEmailOutput(success=False, error=auth_err)
    if search and (filter or order_by):
        return FindSharedFolderEmailOutput(
            success=False,
            error="`search` is not supported when using `filter` or `order_by`.",
        )
    headers = _get_auth_headers(auth_type, auth_data)
    if search:
        headers = {**headers, "ConsistencyLevel": "eventual"}
    params: dict[str, Any] = {}
    if search:
        s = search.strip().strip('"').strip("'")
        params["$search"] = f'"{s}"'
    if filter:
        params["$filter"] = filter
    if order_by:
        params["$orderby"] = order_by
    url = f"{_BASE_URL}/users/{user_id}/mailFolders/{shared_folder_id}/messages"
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            messages = await _paginated_get(client, url, headers, params, max_results)
        except RuntimeError as exc:
            return FindSharedFolderEmailOutput(
                success=False,
                error=f"API error: {exc}",
            )
    return FindSharedFolderEmailOutput(
        success=True,
        count=len(messages),
        messages=messages,
    )


@tool(args_schema=GetCurrentUserInput)
@serialize_pydantic_return
async def get_current_user(
    auth_type: str,
    auth_data: dict[str, Any],
) -> GetCurrentUserOutput:
    """Returns the authenticated Microsoft user's ID, display name, email, and principal name."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return GetCurrentUserOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{_BASE_URL}/me",
            headers=headers,
            params={"$select": "id,displayName,mail,userPrincipalName"},
        )
        if resp.status_code >= 400:
            return GetCurrentUserOutput(
                success=False,
                error=f"API error: {resp.status_code} - {resp.text}",
            )
        user = resp.json()
    return GetCurrentUserOutput(
        success=True,
        id=user.get("id"),
        displayName=user.get("displayName"),
        mail=user.get("mail"),
        userPrincipalName=user.get("userPrincipalName"),
    )


@tool(args_schema=GetMessageInput)
@serialize_pydantic_return
async def get_message(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    include_attachments: bool = False,
    user_id: str | None = None,
) -> GetMessageOutput:
    """Retrieve a single email message by its Microsoft Graph message ID."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return GetMessageOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if include_attachments:
        params["$expand"] = "attachments"
    url = f"{_BASE_URL}{_user_path(user_id)}/messages/{message_id}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url, headers=headers, params=params)
        if resp.status_code >= 400:
            return GetMessageOutput(
                success=False,
                error=f"API error: {resp.status_code} - {resp.text}",
            )
        data = resp.json()
    return GetMessageOutput(success=True, message=data)


@tool(args_schema=ListContactsInput)
@serialize_pydantic_return
async def list_contacts(
    auth_type: str,
    auth_data: dict[str, Any],
    filter_address: str | None = None,
    max_results: int = 100,
) -> ListContactsOutput:
    """Get a contact collection from the default contacts folder."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return ListContactsOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"$top": 50}
    if filter_address:
        params["$filter"] = f"emailAddresses/any(a:a/address eq '{filter_address}')"
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            contacts = await _paginated_get(
                client, f"{_BASE_URL}/me/contacts", headers, params, max_results
            )
        except RuntimeError as exc:
            return ListContactsOutput(success=False, error=f"API error: {exc}")
    return ListContactsOutput(
        success=True,
        count=len(contacts),
        contacts=contacts,
    )


@tool(args_schema=ListFoldersInput)
@serialize_pydantic_return
async def list_folders(
    auth_type: str,
    auth_data: dict[str, Any],
    max_results: int = 100,
    include_subfolders: bool = False,
    include_hidden_folders: bool = False,
) -> ListFoldersOutput:
    """Retrieves a list of mail folders in Microsoft Outlook."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return ListFoldersOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            if include_subfolders:
                folders = await _list_all_folders(client, headers, None, include_hidden_folders)
                if max_results and len(folders) > max_results:
                    folders = folders[:max_results]
            else:
                params: dict[str, Any] = {"$top": 50}
                if include_hidden_folders:
                    params["includeHiddenFolders"] = "true"
                folders = await _paginated_get(
                    client, f"{_BASE_URL}/me/mailFolders", headers, params, max_results
                )
        except RuntimeError as exc:
            return ListFoldersOutput(success=False, error=f"API error: {exc}")
    return ListFoldersOutput(
        success=True,
        count=len(folders),
        folders=folders,
    )


@tool(args_schema=ListImportantMailInput)
@serialize_pydantic_return
async def list_important_mail(
    auth_type: str,
    auth_data: dict[str, Any],
    max_results: int = 100,
    user_id: str | None = None,
) -> ListImportantMailOutput:
    """Get the most important mail from the user's Inbox (high importance or flagged)."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return ListImportantMailOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    params = {
        "$filter": "importance eq 'high' or flag/flagStatus eq 'flagged'",
        "$select": "id,subject,sender,receivedDateTime",
        "$top": 50,
    }
    url = f"{_BASE_URL}{_user_path(user_id)}/mailFolders/inbox/messages"
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            items = await _paginated_get(client, url, headers, params, max_results)
        except RuntimeError as exc:
            return ListImportantMailOutput(
                success=False,
                error=f"API error: {exc}",
            )
    data = [
        ImportantMailItem(
            id=it.get("id"),
            subject=it.get("subject"),
            sender=(it.get("sender") or {}).get("emailAddress", {}).get("name"),
            receivedDateTime=it.get("receivedDateTime"),
        )
        for it in items
    ]
    return ListImportantMailOutput(
        success=True,
        count=len(data),
        data=data,
    )


@tool(args_schema=ListLabelsInput)
@serialize_pydantic_return
async def list_labels(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str | None = None,
) -> ListLabelsOutput:
    """Get all the labels/categories that have been defined for a user."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return ListLabelsOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    url = f"{_BASE_URL}{_user_path(user_id)}/outlook/masterCategories"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code >= 400:
            return ListLabelsOutput(
                success=False,
                error=f"API error: {resp.status_code} - {resp.text}",
            )
        labels = resp.json().get("value", []) or []
    return ListLabelsOutput(
        success=True,
        count=len(labels),
        labels=labels,
    )


@tool(args_schema=MoveEmailToFolderInput)
@serialize_pydantic_return
async def move_email_to_folder(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    folder_id: str,
    user_id: str | None = None,
) -> MoveEmailToFolderOutput:
    """Moves an email to the specified folder."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return MoveEmailToFolderOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    url = f"{_BASE_URL}{_user_path(user_id)}/messages/{message_id}/move"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json={"destinationId": folder_id})
        if resp.status_code >= 400:
            return MoveEmailToFolderOutput(
                success=False,
                error=f"API error: {resp.status_code} - {resp.text}",
            )
        data = resp.json()
    return MoveEmailToFolderOutput(
        success=True,
        id=data.get("id"),
        parentFolderId=data.get("parentFolderId"),
    )


@tool(args_schema=RemoveLabelFromEmailInput)
@serialize_pydantic_return
async def remove_label_from_email(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    label: str,
    user_id: str | None = None,
) -> RemoveLabelFromEmailOutput:
    """Removes a label/category from an email."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return RemoveLabelFromEmailOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    base = f"{_BASE_URL}{_user_path(user_id)}/messages/{message_id}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        get_resp = await client.get(base, headers=headers)
        if get_resp.status_code >= 400:
            return RemoveLabelFromEmailOutput(
                success=False,
                error=f"API error fetching message: {get_resp.status_code} - {get_resp.text}",
            )
        categories = get_resp.json().get("categories", []) or []
        new_categories = [c for c in categories if c != label]
        patch_resp = await client.patch(
            base, headers=headers, json={"categories": new_categories}
        )
        if patch_resp.status_code >= 400:
            return RemoveLabelFromEmailOutput(
                success=False,
                error=f"API error: {patch_resp.status_code} - {patch_resp.text}",
            )
        data = patch_resp.json()
    return RemoveLabelFromEmailOutput(
        success=True,
        id=data.get("id"),
        categories=data.get("categories", []) or [],
    )


@tool(args_schema=ReplyToEmailInput)
@serialize_pydantic_return
async def reply_to_email(
    auth_type: str,
    auth_data: dict[str, Any],
    message_id: str,
    comment: str | None = None,
    recipients: list[str] | None = None,
    cc_recipients: list[str] | None = None,
    bcc_recipients: list[str] | None = None,
    subject: str | None = None,
    file_urls: list[str] | None = None,
    expand: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> ReplyToEmailOutput:
    """Reply to an email in Microsoft Outlook."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return ReplyToEmailOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        message = await _build_message_body(
            recipients, cc_recipients, bcc_recipients, subject, comment, "text", file_urls
        )
    except RuntimeError as exc:
        return ReplyToEmailOutput(success=False, error=str(exc))
    if expand:
        message.update(expand)
    payload: dict[str, Any] = {"comment": comment or "", "message": message}
    url = f"{_BASE_URL}{_user_path(user_id)}/messages/{message_id}/reply"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            return ReplyToEmailOutput(
                success=False,
                error=f"API error: {resp.status_code} - {resp.text}",
            )
    return ReplyToEmailOutput(success=True, sent=True)


@tool(args_schema=SendEmailInput)
@serialize_pydantic_return
async def send_email(
    auth_type: str,
    auth_data: dict[str, Any],
    recipients: list[str] | None = None,
    cc_recipients: list[str] | None = None,
    bcc_recipients: list[str] | None = None,
    subject: str | None = None,
    content_type: str | None = "text",
    content: str | None = None,
    file_urls: list[str] | None = None,
    expand: dict[str, Any] | None = None,
    user_id: str | None = None,
) -> SendEmailOutput:
    """Send an email to one or multiple recipients."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return SendEmailOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        message = await _build_message_body(
            recipients, cc_recipients, bcc_recipients, subject, content, content_type, file_urls
        )
    except RuntimeError as exc:
        return SendEmailOutput(success=False, error=str(exc))
    if expand:
        message.update(expand)
    url = f"{_BASE_URL}{_user_path(user_id)}/sendMail"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, headers=headers, json={"message": message})
        if resp.status_code >= 400:
            return SendEmailOutput(
                success=False,
                error=f"API error: {resp.status_code} - {resp.text}",
            )
    return SendEmailOutput(success=True, sent=True)


@tool(args_schema=UpdateContactInput)
@serialize_pydantic_return
async def update_contact(
    auth_type: str,
    auth_data: dict[str, Any],
    contact_id: str,
    given_name: str | None = None,
    surname: str | None = None,
    email_addresses: list[str] | None = None,
    business_phones: list[str] | None = None,
    expand: dict[str, Any] | None = None,
) -> UpdateContactOutput:
    """Update an existing contact."""
    auth_err = _check_auth(auth_type, auth_data)
    if auth_err:
        return UpdateContactOutput(success=False, error=auth_err)
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {}
    if given_name is not None:
        body["givenName"] = given_name
    if surname is not None:
        body["surname"] = surname
    if email_addresses:
        body["emailAddresses"] = [
            {"address": a, "name": f"Email #{i + 1}"}
            for i, a in enumerate(email_addresses)
        ]
    if business_phones is not None:
        body["businessPhones"] = business_phones
    if expand:
        body.update(expand)
    url = f"{_BASE_URL}/me/contacts/{contact_id}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.patch(url, headers=headers, json=body)
        if resp.status_code >= 400:
            return UpdateContactOutput(
                success=False,
                error=f"API error: {resp.status_code} - {resp.text}",
            )
        data = resp.json()
    return UpdateContactOutput(
        success=True,
        contact=ContactSummary(
            id=data.get("id"),
            displayName=data.get("displayName"),
            givenName=data.get("givenName"),
            surname=data.get("surname"),
            emailAddresses=data.get("emailAddresses", []) or [],
            businessPhones=data.get("businessPhones", []) or [],
        ),
    )
