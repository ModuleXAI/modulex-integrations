"""DocuSign LangChain @tool functions."""
from __future__ import annotations

import base64
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.docusign.outputs import (
    CreateDraftOutput,
    CreateEnvelopeFromFileOutput,
    CreateEnvelopeOutput,
    CreateRecipientViewOutput,
    CreateSignatureRequestOutput,
    DocumentSummary,
    DownloadDocumentsOutput,
    EnvelopeSummary,
    GetEnvelopeOutput,
    ListDocumentsOutput,
    ListEnvelopesOutput,
    ListRecipientsOutput,
    RecipientSummary,
    SendEnvelopeOutput,
    VoidEnvelopeOutput,
)

__all__ = [
    "create_draft",
    "create_envelope",
    "create_envelope_from_file",
    "create_recipient_view",
    "create_signature_request",
    "download_documents",
    "get_envelope",
    "list_documents",
    "list_envelopes",
    "list_recipients",
    "send_envelope",
    "void_envelope",
]

_USERINFO_URL = "https://account.docusign.com/oauth/userinfo"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        token = auth_data.get("access_token")
    else:
        token = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def _resolve_base_uri(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    account_id: str,
) -> str:
    resp = await client.get(_USERINFO_URL, headers=headers)
    resp.raise_for_status()
    info = resp.json()
    for acct in info.get("accounts", []):
        if acct.get("account_id") == account_id:
            return f"{acct['base_uri']}/restapi/v2.1/accounts/{account_id}"
    if info.get("accounts"):
        acct = info["accounts"][0]
        return f"{acct['base_uri']}/restapi/v2.1/accounts/{account_id}"
    raise ValueError(f"No accounts found in DocuSign userinfo for account {account_id}")


def _parse_json_safe(value: str | None) -> Any:
    if not value:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _build_envelope_summary(data: dict[str, Any]) -> EnvelopeSummary:
    return EnvelopeSummary(
        envelope_id=data.get("envelopeId"),
        status=data.get("status"),
        email_subject=data.get("emailSubject"),
        status_date_time=data.get("statusDateTime"),
        uri=data.get("uri"),
        sender_user_name=(data.get("sender") or {}).get("userName"),
        sender_email=(data.get("sender") or {}).get("email"),
        created_date_time=data.get("createdDateTime"),
        sent_date_time=data.get("sentDateTime"),
        completed_date_time=data.get("completedDateTime"),
        voided_date_time=data.get("voidedDateTime"),
        voided_reason=data.get("voidedReason"),
    )


def _build_recipient(r: dict[str, Any]) -> RecipientSummary:
    return RecipientSummary(
        recipient_id=r.get("recipientId"),
        name=r.get("name"),
        email=r.get("email"),
        status=r.get("status"),
        routing_order=r.get("routingOrder"),
        client_user_id=r.get("clientUserId"),
        signed_date_time=r.get("signedDateTime"),
        delivered_date_time=r.get("deliveredDateTime"),
    )


# --- Input schemas --------------------------------------------------------


class CreateSignatureRequestInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="DocuSign Account ID")
    template: str = Field(description="Document Template ID")
    email_subject: str = Field(description="Subject line of the signature request email")
    email_blurb: str | None = Field(default=None, description="Email message body to the recipient")
    template_roles_json: str | None = Field(default=None, description="JSON array of template role objects")


class CreateDraftInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="DocuSign Account ID")
    template: str = Field(description="Document Template ID")
    email_subject: str = Field(description="Subject line of the email")
    email_blurb: str | None = Field(default=None, description="Email message body to the recipient")
    template_roles_json: str | None = Field(default=None, description="JSON array of template role objects")


class CreateEnvelopeInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="DocuSign Account ID")
    envelope_definition_json: str = Field(description="Full DocuSign envelope definition as a JSON string")
    status: str | None = Field(default=None, description="Envelope status override: sent or created")
    merge_roles_on_draft: bool | None = Field(default=None, description="Merge template roles on draft")


class CreateEnvelopeFromFileInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="DocuSign Account ID")
    file_url: str = Field(description="URL of the document to send")
    email_subject: str = Field(description="Subject line of the email")
    signer_name: str = Field(description="Full name of the signer")
    signer_email: str = Field(description="Email address of the signer")
    status: str = Field(default="sent", description="Envelope status: sent or created")
    document_name: str | None = Field(default=None, description="Document name shown in DocuSign")
    file_extension: str | None = Field(default=None, description="File extension")
    signer_recipient_id: str = Field(default="1", description="Recipient ID for the signer")
    routing_order: str = Field(default="1", description="Routing order for the signer")
    client_user_id: str | None = Field(default=None, description="Client user ID for embedded signing")
    sign_here_anchor_string: str = Field(default="/sn1/", description="Anchor text for signature tab placement")
    anchor_x_offset: str = Field(default="20", description="Horizontal offset in pixels for the signature tab")
    anchor_y_offset: str = Field(default="10", description="Vertical offset in pixels for the signature tab")


class CreateRecipientViewInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="DocuSign Account ID")
    envelope_id: str = Field(description="DocuSign envelope ID")
    return_url: str = Field(description="Redirect URL after signing session")
    recipient_id: str = Field(description="Recipient ID on the envelope")
    authentication_method: str = Field(default="none", description="How the signer was authenticated")
    ping_url: str | None = Field(default=None, description="URL DocuSign pings during signing")
    ping_frequency: str | None = Field(default=None, description="Ping interval in seconds (60-1200)")


class GetEnvelopeInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="DocuSign Account ID")
    envelope_id: str = Field(description="DocuSign envelope ID")
    include: str | None = Field(default=None, description="Comma-separated additional info: custom_fields, documents, extensions, folders, recipients, tabs")


class ListEnvelopesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="DocuSign Account ID")
    from_date: str | None = Field(default=None, description="ISO 8601 datetime filter start")
    to_date: str | None = Field(default=None, description="ISO 8601 datetime filter end")
    status: str | None = Field(default=None, description="Comma-separated envelope statuses")
    email: str | None = Field(default=None, description="Filter by email address")
    search_text: str | None = Field(default=None, description="Search text against envelope metadata")
    folder_ids: str | None = Field(default=None, description="Comma-separated folder IDs")
    count: int = Field(default=100, description="Envelopes per page")
    start_position: int = Field(default=0, description="Zero-based result offset")
    order: str | None = Field(default=None, description="Sort order: asc or desc")
    order_by: str | None = Field(default=None, description="Sort field")
    fetch_all: bool = Field(default=False, description="Follow pagination until no pages remain")
    max_pages: int = Field(default=10, description="Maximum pages when fetch_all is true")


class ListDocumentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="DocuSign Account ID")
    envelope_id: str = Field(description="DocuSign envelope ID")
    include_tabs: bool = Field(default=False, description="Include tab information")
    include_metadata: bool = Field(default=False, description="Include document metadata")


class ListRecipientsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="DocuSign Account ID")
    envelope_id: str = Field(description="DocuSign envelope ID")
    include_tabs: bool = Field(default=False, description="Include recipient tabs")
    include_extended: bool = Field(default=False, description="Include extended recipient info")
    include_metadata: bool = Field(default=False, description="Include metadata")


class SendEnvelopeInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="DocuSign Account ID")
    envelope_id: str = Field(description="DocuSign envelope ID")


class DownloadDocumentsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="DocuSign Account ID")
    envelope_id: str = Field(description="DocuSign envelope ID")
    download_type: str = Field(description="Download type: combined, archive, certificate, or portfolio")
    filename: str = Field(description="Filename including extension")


class VoidEnvelopeInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account: str = Field(description="DocuSign Account ID")
    envelope_id: str = Field(description="DocuSign envelope ID")
    voided_reason: str = Field(description="Reason for voiding the envelope")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateSignatureRequestInput)
@serialize_pydantic_return
async def create_signature_request(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    template: str,
    email_subject: str,
    email_blurb: str | None = None,
    template_roles_json: str | None = None,
) -> CreateSignatureRequestOutput:
    """Create and send a signature request from a DocuSign template."""
    if not auth_data.get("access_token"):
        return CreateSignatureRequestOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            base_uri = await _resolve_base_uri(client, headers, account)
            body: dict[str, Any] = {
                "templateId": template,
                "emailSubject": email_subject,
                "status": "sent",
            }
            if email_blurb:
                body["emailBlurb"] = email_blurb
            roles = _parse_json_safe(template_roles_json)
            if roles and isinstance(roles, list):
                body["templateRoles"] = roles
            headers["Content-Type"] = "application/json"
            resp = await client.post(f"{base_uri}/envelopes", headers=headers, json=body)
        if resp.status_code not in (200, 201):
            return CreateSignatureRequestOutput(
                success=False,
                error=f"API error ({resp.status_code}): {resp.text}",
            )
        data = resp.json()
    except httpx.TimeoutException:
        return CreateSignatureRequestOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateSignatureRequestOutput(success=False, error=f"Call failed: {exc}")
    return CreateSignatureRequestOutput(
        success=True,
        envelope_id=data.get("envelopeId"),
        status=data.get("status"),
        status_date_time=data.get("statusDateTime"),
        uri=data.get("uri"),
    )


@tool(args_schema=CreateDraftInput)
@serialize_pydantic_return
async def create_draft(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    template: str,
    email_subject: str,
    email_blurb: str | None = None,
    template_roles_json: str | None = None,
) -> CreateDraftOutput:
    """Create a draft envelope from a DocuSign template without sending it."""
    if not auth_data.get("access_token"):
        return CreateDraftOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            base_uri = await _resolve_base_uri(client, headers, account)
            body: dict[str, Any] = {
                "templateId": template,
                "emailSubject": email_subject,
                "status": "created",
            }
            if email_blurb:
                body["emailBlurb"] = email_blurb
            roles = _parse_json_safe(template_roles_json)
            if roles and isinstance(roles, list):
                body["templateRoles"] = roles
            headers["Content-Type"] = "application/json"
            resp = await client.post(f"{base_uri}/envelopes", headers=headers, json=body)
        if resp.status_code not in (200, 201):
            return CreateDraftOutput(
                success=False,
                error=f"API error ({resp.status_code}): {resp.text}",
            )
        data = resp.json()
    except httpx.TimeoutException:
        return CreateDraftOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDraftOutput(success=False, error=f"Call failed: {exc}")
    return CreateDraftOutput(
        success=True,
        envelope_id=data.get("envelopeId"),
        status=data.get("status"),
        status_date_time=data.get("statusDateTime"),
        uri=data.get("uri"),
    )


@tool(args_schema=CreateEnvelopeInput)
@serialize_pydantic_return
async def create_envelope(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    envelope_definition_json: str,
    status: str | None = None,
    merge_roles_on_draft: bool | None = None,
) -> CreateEnvelopeOutput:
    """Create a DocuSign envelope from a full envelope definition JSON payload for advanced multi-document or multi-recipient scenarios."""
    if not auth_data.get("access_token"):
        return CreateEnvelopeOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        body = _parse_json_safe(envelope_definition_json)
        if not body or not isinstance(body, dict):
            return CreateEnvelopeOutput(
                success=False,
                error="Invalid envelope_definition_json: must be a valid JSON object.",
            )
        if status:
            body["status"] = status
        if merge_roles_on_draft:
            body["mergeRolesOnDraft"] = "true"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            base_uri = await _resolve_base_uri(client, headers, account)
            headers["Content-Type"] = "application/json"
            resp = await client.post(f"{base_uri}/envelopes", headers=headers, json=body)
        if resp.status_code not in (200, 201):
            return CreateEnvelopeOutput(
                success=False,
                error=f"API error ({resp.status_code}): {resp.text}",
            )
        data = resp.json()
    except httpx.TimeoutException:
        return CreateEnvelopeOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateEnvelopeOutput(success=False, error=f"Call failed: {exc}")
    return CreateEnvelopeOutput(
        success=True,
        envelope_id=data.get("envelopeId"),
        status=data.get("status"),
        status_date_time=data.get("statusDateTime"),
        uri=data.get("uri"),
    )


@tool(args_schema=CreateEnvelopeFromFileInput)
@serialize_pydantic_return
async def create_envelope_from_file(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    file_url: str,
    email_subject: str,
    signer_name: str,
    signer_email: str,
    status: str = "sent",
    document_name: str | None = None,
    file_extension: str | None = None,
    signer_recipient_id: str = "1",
    routing_order: str = "1",
    client_user_id: str | None = None,
    sign_here_anchor_string: str = "/sn1/",
    anchor_x_offset: str = "20",
    anchor_y_offset: str = "10",
) -> CreateEnvelopeFromFileOutput:
    """Create and optionally send a single-document DocuSign envelope from a file URL with anchor-based signature tab placement."""
    if not auth_data.get("access_token"):
        return CreateEnvelopeFromFileOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            file_resp = await client.get(file_url)
            if file_resp.status_code != 200:
                return CreateEnvelopeFromFileOutput(
                    success=False,
                    error=f"Failed to fetch file from URL ({file_resp.status_code})",
                )
            file_bytes = file_resp.content
            file_b64 = base64.b64encode(file_bytes).decode("ascii")

            parsed_url = urlparse(file_url)
            path = parsed_url.path
            if not document_name:
                document_name = path.rsplit("/", 1)[-1] if "/" in path else "document"
            if not file_extension:
                if "." in path:
                    file_extension = path.rsplit(".", 1)[-1]
                else:
                    file_extension = "pdf"

            signer: dict[str, Any] = {
                "name": signer_name,
                "email": signer_email,
                "recipientId": signer_recipient_id,
                "routingOrder": routing_order,
                "tabs": {
                    "signHereTabs": [
                        {
                            "anchorString": sign_here_anchor_string,
                            "anchorXOffset": anchor_x_offset,
                            "anchorYOffset": anchor_y_offset,
                        },
                    ],
                },
            }
            if client_user_id:
                signer["clientUserId"] = client_user_id

            body: dict[str, Any] = {
                "emailSubject": email_subject,
                "status": status,
                "documents": [
                    {
                        "documentBase64": file_b64,
                        "name": document_name,
                        "fileExtension": file_extension,
                        "documentId": "1",
                    },
                ],
                "recipients": {
                    "signers": [signer],
                },
            }

            base_uri = await _resolve_base_uri(client, headers, account)
            headers["Content-Type"] = "application/json"
            resp = await client.post(f"{base_uri}/envelopes", headers=headers, json=body)
        if resp.status_code not in (200, 201):
            return CreateEnvelopeFromFileOutput(
                success=False,
                error=f"API error ({resp.status_code}): {resp.text}",
            )
        data = resp.json()
    except httpx.TimeoutException:
        return CreateEnvelopeFromFileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateEnvelopeFromFileOutput(success=False, error=f"Call failed: {exc}")
    return CreateEnvelopeFromFileOutput(
        success=True,
        envelope_id=data.get("envelopeId"),
        status=data.get("status"),
        status_date_time=data.get("statusDateTime"),
        uri=data.get("uri"),
    )


@tool(args_schema=CreateRecipientViewInput)
@serialize_pydantic_return
async def create_recipient_view(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    envelope_id: str,
    return_url: str,
    recipient_id: str,
    authentication_method: str = "none",
    ping_url: str | None = None,
    ping_frequency: str | None = None,
) -> CreateRecipientViewOutput:
    """Create an embedded signing URL for a selected envelope recipient who was created with a clientUserId."""
    if not auth_data.get("access_token"):
        return CreateRecipientViewOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            base_uri = await _resolve_base_uri(client, headers, account)
            recip_resp = await client.get(
                f"{base_uri}/envelopes/{envelope_id}/recipients",
                headers=headers,
            )
            recip_resp.raise_for_status()
            recip_data = recip_resp.json()

            matched = None
            for group_key in ("signers", "agents", "editors", "intermediaries", "carbonCopies", "certifiedDeliveries"):
                for r in recip_data.get(group_key, []):
                    if r.get("recipientId") == recipient_id:
                        matched = r
                        break
                if matched:
                    break

            if not matched:
                return CreateRecipientViewOutput(
                    success=False,
                    error=f"Recipient with ID {recipient_id} not found on envelope {envelope_id}",
                )
            if not matched.get("clientUserId"):
                return CreateRecipientViewOutput(
                    success=False,
                    error=f"Recipient {recipient_id} does not have a clientUserId set. Embedded signing requires clientUserId.",
                )

            view_body: dict[str, Any] = {
                "returnUrl": return_url,
                "authenticationMethod": authentication_method,
                "clientUserId": matched["clientUserId"],
                "email": matched.get("email", ""),
                "userName": matched.get("name", ""),
                "recipientId": recipient_id,
            }
            if ping_url:
                view_body["pingUrl"] = ping_url
            if ping_frequency:
                view_body["pingFrequency"] = ping_frequency

            headers["Content-Type"] = "application/json"
            resp = await client.post(
                f"{base_uri}/envelopes/{envelope_id}/views/recipient",
                headers=headers,
                json=view_body,
            )
        if resp.status_code not in (200, 201):
            return CreateRecipientViewOutput(
                success=False,
                error=f"API error ({resp.status_code}): {resp.text}",
            )
        data = resp.json()
    except httpx.TimeoutException:
        return CreateRecipientViewOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateRecipientViewOutput(success=False, error=f"Call failed: {exc}")
    return CreateRecipientViewOutput(success=True, url=data.get("url"))


@tool(args_schema=GetEnvelopeInput)
@serialize_pydantic_return
async def get_envelope(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    envelope_id: str,
    include: str | None = None,
) -> GetEnvelopeOutput:
    """Get details for a DocuSign envelope by ID."""
    if not auth_data.get("access_token"):
        return GetEnvelopeOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            base_uri = await _resolve_base_uri(client, headers, account)
            params: dict[str, str] = {}
            if include:
                params["include"] = include
            resp = await client.get(
                f"{base_uri}/envelopes/{envelope_id}",
                headers=headers,
                params=params,
            )
        if resp.status_code != 200:
            return GetEnvelopeOutput(
                success=False,
                error=f"API error ({resp.status_code}): {resp.text}",
            )
        data = resp.json()
    except httpx.TimeoutException:
        return GetEnvelopeOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetEnvelopeOutput(success=False, error=f"Call failed: {exc}")
    return GetEnvelopeOutput(success=True, envelope=_build_envelope_summary(data))


@tool(args_schema=ListEnvelopesInput)
@serialize_pydantic_return
async def list_envelopes(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    from_date: str | None = None,
    to_date: str | None = None,
    status: str | None = None,
    email: str | None = None,
    search_text: str | None = None,
    folder_ids: str | None = None,
    count: int = 100,
    start_position: int = 0,
    order: str | None = None,
    order_by: str | None = None,
    fetch_all: bool = False,
    max_pages: int = 10,
) -> ListEnvelopesOutput:
    """Search for DocuSign envelopes by date, status, email, text, or folder filters."""
    if not auth_data.get("access_token"):
        return ListEnvelopesOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        if not from_date:
            from_date = (datetime.now(tz=UTC) - timedelta(days=30)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            base_uri = await _resolve_base_uri(client, headers, account)
            all_envelopes: list[EnvelopeSummary] = []
            total_set_size: int | None = None
            current_pos = start_position
            pages_fetched = 0

            while True:
                params: dict[str, str] = {
                    "from_date": from_date,
                    "count": str(count),
                    "start_position": str(current_pos),
                }
                if to_date:
                    params["to_date"] = to_date
                if status:
                    params["status"] = status
                if email:
                    params["email"] = email
                if search_text:
                    params["search_text"] = search_text
                if folder_ids:
                    params["folder_ids"] = folder_ids
                if order:
                    params["order"] = order
                if order_by:
                    params["order_by"] = order_by

                resp = await client.get(
                    f"{base_uri}/envelopes",
                    headers=headers,
                    params=params,
                )
                if resp.status_code != 200:
                    return ListEnvelopesOutput(
                        success=False,
                        error=f"API error ({resp.status_code}): {resp.text}",
                    )
                data = resp.json()
                if total_set_size is None:
                    raw_total = data.get("totalSetSize")
                    if raw_total is not None:
                        total_set_size = int(raw_total)

                for env in data.get("envelopes", []):
                    all_envelopes.append(_build_envelope_summary(env))

                pages_fetched += 1
                next_uri = data.get("nextUri")
                if not fetch_all or not next_uri or pages_fetched >= max_pages:
                    break
                current_pos += count

    except httpx.TimeoutException:
        return ListEnvelopesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListEnvelopesOutput(success=False, error=f"Call failed: {exc}")
    return ListEnvelopesOutput(
        success=True,
        envelopes=all_envelopes,
        result_set_size=len(all_envelopes),
        total_set_size=total_set_size,
    )


@tool(args_schema=ListDocumentsInput)
@serialize_pydantic_return
async def list_documents(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    envelope_id: str,
    include_tabs: bool = False,
    include_metadata: bool = False,
) -> ListDocumentsOutput:
    """List documents in a DocuSign envelope."""
    if not auth_data.get("access_token"):
        return ListDocumentsOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            base_uri = await _resolve_base_uri(client, headers, account)
            params: dict[str, str] = {}
            if include_tabs:
                params["include_tabs"] = "true"
            if include_metadata:
                params["include_document_metadata"] = "true"
            resp = await client.get(
                f"{base_uri}/envelopes/{envelope_id}/documents",
                headers=headers,
                params=params,
            )
        if resp.status_code != 200:
            return ListDocumentsOutput(
                success=False,
                error=f"API error ({resp.status_code}): {resp.text}",
            )
        data = resp.json()
    except httpx.TimeoutException:
        return ListDocumentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDocumentsOutput(success=False, error=f"Call failed: {exc}")
    docs = [
        DocumentSummary(
            document_id=d.get("documentId"),
            name=d.get("name"),
            type=d.get("type"),
            uri=d.get("uri"),
            order=d.get("order"),
            pages=d.get("pages"),
        )
        for d in data.get("envelopeDocuments", [])
    ]
    return ListDocumentsOutput(success=True, documents=docs)


@tool(args_schema=ListRecipientsInput)
@serialize_pydantic_return
async def list_recipients(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    envelope_id: str,
    include_tabs: bool = False,
    include_extended: bool = False,
    include_metadata: bool = False,
) -> ListRecipientsOutput:
    """List recipients and their status for a DocuSign envelope."""
    if not auth_data.get("access_token"):
        return ListRecipientsOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            base_uri = await _resolve_base_uri(client, headers, account)
            params: dict[str, str] = {}
            if include_tabs:
                params["include_tabs"] = "true"
            if include_extended:
                params["include_extended"] = "true"
            if include_metadata:
                params["include_metadata"] = "true"
            resp = await client.get(
                f"{base_uri}/envelopes/{envelope_id}/recipients",
                headers=headers,
                params=params,
            )
        if resp.status_code != 200:
            return ListRecipientsOutput(
                success=False,
                error=f"API error ({resp.status_code}): {resp.text}",
            )
        data = resp.json()
    except httpx.TimeoutException:
        return ListRecipientsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListRecipientsOutput(success=False, error=f"Call failed: {exc}")
    return ListRecipientsOutput(
        success=True,
        signers=[_build_recipient(r) for r in data.get("signers", [])],
        carbon_copies=[_build_recipient(r) for r in data.get("carbonCopies", [])],
        agents=[_build_recipient(r) for r in data.get("agents", [])],
    )


@tool(args_schema=SendEnvelopeInput)
@serialize_pydantic_return
async def send_envelope(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    envelope_id: str,
) -> SendEnvelopeOutput:
    """Send an existing draft DocuSign envelope by updating its status to sent."""
    if not auth_data.get("access_token"):
        return SendEnvelopeOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            base_uri = await _resolve_base_uri(client, headers, account)
            headers["Content-Type"] = "application/json"
            resp = await client.put(
                f"{base_uri}/envelopes/{envelope_id}",
                headers=headers,
                json={"status": "sent"},
            )
        if resp.status_code != 200:
            return SendEnvelopeOutput(
                success=False,
                error=f"API error ({resp.status_code}): {resp.text}",
            )
        data = resp.json()
    except httpx.TimeoutException:
        return SendEnvelopeOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendEnvelopeOutput(success=False, error=f"Call failed: {exc}")
    return SendEnvelopeOutput(
        success=True,
        envelope_id=data.get("envelopeId"),
        status="sent",
    )


@tool(args_schema=DownloadDocumentsInput)
@serialize_pydantic_return
async def download_documents(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    envelope_id: str,
    download_type: str,
    filename: str,
) -> DownloadDocumentsOutput:
    """Download documents from a DocuSign envelope as base64-encoded content."""
    if not auth_data.get("access_token"):
        return DownloadDocumentsOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            base_uri = await _resolve_base_uri(client, headers, account)
            env_resp = await client.get(
                f"{base_uri}/envelopes/{envelope_id}",
                headers=headers,
            )
            env_resp.raise_for_status()
            env_data = env_resp.json()
            documents_uri = env_data.get("documentsUri", f"/envelopes/{envelope_id}/documents")

            download_url = f"{base_uri}{documents_uri}/{download_type}"
            resp = await client.get(download_url, headers=headers)
        if resp.status_code != 200:
            return DownloadDocumentsOutput(
                success=False,
                error=f"API error ({resp.status_code}): {resp.text}",
            )
        content_type = resp.headers.get("content-type", "application/octet-stream")
        content_b64 = base64.b64encode(resp.content).decode("ascii")
    except httpx.TimeoutException:
        return DownloadDocumentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DownloadDocumentsOutput(success=False, error=f"Call failed: {exc}")
    return DownloadDocumentsOutput(
        success=True,
        content_base64=content_b64,
        filename=filename,
        content_type=content_type,
    )


@tool(args_schema=VoidEnvelopeInput)
@serialize_pydantic_return
async def void_envelope(
    auth_type: str,
    auth_data: dict[str, Any],
    account: str,
    envelope_id: str,
    voided_reason: str,
) -> VoidEnvelopeOutput:
    """Void a DocuSign envelope that is still in process, cancelling it and preventing recipients from completing it."""
    if not auth_data.get("access_token"):
        return VoidEnvelopeOutput(success=False, error="Missing access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            base_uri = await _resolve_base_uri(client, headers, account)
            headers["Content-Type"] = "application/json"
            resp = await client.put(
                f"{base_uri}/envelopes/{envelope_id}",
                headers=headers,
                json={"status": "voided", "voidedReason": voided_reason},
            )
        if resp.status_code != 200:
            return VoidEnvelopeOutput(
                success=False,
                error=f"API error ({resp.status_code}): {resp.text}",
            )
        data = resp.json()
    except httpx.TimeoutException:
        return VoidEnvelopeOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return VoidEnvelopeOutput(success=False, error=f"Call failed: {exc}")
    return VoidEnvelopeOutput(
        success=True,
        envelope_id=data.get("envelopeId"),
        status="voided",
    )
