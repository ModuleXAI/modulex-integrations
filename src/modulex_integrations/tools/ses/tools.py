"""Amazon SES LangChain ``@tool`` functions.

Every action talks to the Amazon SES API v2 REST/JSON endpoint
(``https://email.<region>.amazonaws.com/v2/email/...``) over
``httpx.AsyncClient``. Requests are signed with AWS Signature Version 4
using the access key ID / secret access key pair resolved from the
credential (``auth_data``); no AWS SDK is required at runtime.

Error model: every call is wrapped — non-2xx responses, timeouts, and
unexpected exceptions all come back as the typed output with
``success=False`` + ``error`` instead of raising.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from datetime import UTC, datetime
from typing import Any, cast
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.ses.outputs import (
    BulkEmailResult,
    CreateConfigurationSetOutput,
    CreateEmailIdentityOutput,
    CreateTemplateOutput,
    DeleteEmailIdentityOutput,
    DeleteSuppressedDestinationOutput,
    DeleteTemplateOutput,
    DkimAttributes,
    GetAccountOutput,
    GetEmailIdentityOutput,
    GetSuppressedDestinationOutput,
    GetTemplateOutput,
    IdentitySummary,
    IdentityTag,
    ListIdentitiesOutput,
    ListSuppressedDestinationsOutput,
    ListTemplatesOutput,
    MailFromAttributes,
    PutSuppressedDestinationOutput,
    SendBulkEmailOutput,
    SendCustomVerificationEmailOutput,
    SendEmailOutput,
    SendTemplatedEmailOutput,
    SuppressedDestinationSummary,
    TemplateSummary,
    UpdateTemplateOutput,
    VerificationInfo,
)

__all__ = [
    "create_configuration_set",
    "create_email_identity",
    "create_template",
    "delete_email_identity",
    "delete_suppressed_destination",
    "delete_template",
    "get_account",
    "get_email_identity",
    "get_suppressed_destination",
    "get_template",
    "list_identities",
    "list_suppressed_destinations",
    "list_templates",
    "put_suppressed_destination",
    "send_bulk_email",
    "send_custom_verification_email",
    "send_email",
    "send_templated_email",
    "update_template",
]

_SERVICE = "ses"
_ALGORITHM = "AWS4-HMAC-SHA256"
_SIGNED_HEADERS = "content-type;host;x-amz-date"
_DEFAULT_REGION = "us-east-1"
_REGION_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,30}[a-z0-9]$")
_TIMEOUT = 30.0
_MISSING_CREDENTIALS = (
    "AWS credentials are missing. Provide an access key ID and a secret access key."
)
_INVALID_REGION = (
    "Invalid AWS region. Use a region code such as us-east-1 or eu-west-1."
)


# --- Auth + request helpers --------------------------------------------------


def _credential_value(auth_data: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = auth_data.get(key)
        if value:
            return str(value).strip()
    return ""


def _credentials(auth_data: dict[str, Any]) -> tuple[str, str]:
    """Read the AWS key pair from ``auth_data`` (raw or normalized keys)."""
    access_key = _credential_value(
        auth_data, "access_key_id", "aws_access_key_id", "AWS_ACCESS_KEY_ID"
    )
    secret_key = _credential_value(
        auth_data, "secret_access_key", "aws_secret_access_key", "AWS_SECRET_ACCESS_KEY"
    )
    return access_key, secret_key


def _hmac_sha256(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def _canonical_query(query: list[tuple[str, str]]) -> str:
    """Percent-encode and sort query pairs the way SigV4 requires."""
    encoded = sorted(
        (quote(name, safe="-_.~"), quote(value, safe="-_.~")) for name, value in query
    )
    return "&".join(f"{name}={value}" for name, value in encoded)


def _auth_headers(
    method: str,
    host: str,
    region: str,
    path: str,
    canonical_query: str,
    payload: str,
    access_key: str,
    secret_key: str,
) -> dict[str, str]:
    """Build the SigV4 ``Authorization`` header set for one request."""
    now = datetime.now(UTC)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    # Non-S3 services expect the already-encoded path to be encoded once
    # more when building the canonical request.
    canonical_uri = quote(path, safe="/~")
    canonical_headers = f"content-type:application/json\nhost:{host}\nx-amz-date:{amz_date}\n"
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = "\n".join(
        [
            method,
            canonical_uri,
            canonical_query,
            canonical_headers,
            _SIGNED_HEADERS,
            payload_hash,
        ]
    )

    scope = f"{date_stamp}/{region}/{_SERVICE}/aws4_request"
    string_to_sign = "\n".join(
        [
            _ALGORITHM,
            amz_date,
            scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )

    signing_key = _hmac_sha256(f"AWS4{secret_key}".encode(), date_stamp)
    signing_key = _hmac_sha256(signing_key, region)
    signing_key = _hmac_sha256(signing_key, _SERVICE)
    signing_key = _hmac_sha256(signing_key, "aws4_request")
    signature = hmac.new(
        signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    return {
        "Content-Type": "application/json",
        "X-Amz-Date": amz_date,
        "Authorization": (
            f"{_ALGORITHM} Credential={access_key}/{scope}, "
            f"SignedHeaders={_SIGNED_HEADERS}, Signature={signature}"
        ),
    }


async def _ses_request(
    method: str,
    path: str,
    region: str,
    auth_data: dict[str, Any],
    query: list[tuple[str, str]] | None = None,
    body: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str | None]:
    """Send one signed SES API v2 request.

    Returns ``(data, error)``; ``error`` is ``None`` on success and the
    parsed JSON body (or ``{}`` for empty 200 responses) is in ``data``.
    """
    access_key, secret_key = _credentials(auth_data)
    if not access_key or not secret_key:
        return {}, _MISSING_CREDENTIALS

    region_name = (region or _DEFAULT_REGION).strip().lower() or _DEFAULT_REGION
    if not _REGION_PATTERN.match(region_name):
        return {}, _INVALID_REGION
    host = f"email.{region_name}.amazonaws.com"
    payload = json.dumps(body, separators=(",", ":")) if body is not None else ""
    canonical_query = _canonical_query(query or [])
    url = f"https://{host}{path}"
    if canonical_query:
        url = f"{url}?{canonical_query}"

    headers = _auth_headers(
        method,
        host,
        region_name,
        path,
        canonical_query,
        payload,
        access_key,
        secret_key,
    )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.request(
                method, url, headers=headers, content=payload.encode("utf-8")
            )
    except httpx.TimeoutException:
        return {}, "Request to the Amazon SES API timed out."
    except Exception as exc:  # surfaced to the caller as success=False
        return {}, f"Request to the Amazon SES API failed: {exc}"

    if not 200 <= response.status_code < 300:
        return {}, f"Amazon SES API error ({response.status_code}): {response.text}"

    if not response.content:
        return {}, None
    try:
        parsed: Any = response.json()
    except ValueError:
        return {}, None
    if isinstance(parsed, dict):
        return cast(dict[str, Any], parsed), None
    return {}, None


# --- Payload helpers ---------------------------------------------------------


def _address_list(value: Any) -> list[str]:
    """Normalize a list (or comma-separated string) of email addresses."""
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _template_data(value: dict[str, Any] | str | None) -> str:
    """Render template variables as the JSON string SES expects."""
    if value is None:
        return "{}"
    if isinstance(value, str):
        return value.strip() or "{}"
    return json.dumps(value)


_DKIM_KEYS = {
    "domainsigningselector": "DomainSigningSelector",
    "domainsigningprivatekey": "DomainSigningPrivateKey",
    "nextsigningkeylength": "NextSigningKeyLength",
    "domainsigningattributesorigin": "DomainSigningAttributesOrigin",
}


def _dkim_payload(raw: dict[str, Any] | None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in (raw or {}).items():
        canonical = _DKIM_KEYS.get(str(key).lower())
        if canonical and value is not None:
            payload[canonical] = value
    return payload


def _tag_payload(tags: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    payload: list[dict[str, str]] = []
    for tag in tags or []:
        if not isinstance(tag, dict):
            continue
        key = tag.get("Key", tag.get("key"))
        if key is None:
            continue
        value = tag.get("Value", tag.get("value"))
        payload.append({"Key": str(key), "Value": "" if value is None else str(value)})
    return payload


def _reason_list(value: list[str] | str | None) -> list[str]:
    if isinstance(value, str):
        return [part.strip().upper() for part in value.split(",") if part.strip()]
    if isinstance(value, list):
        return [str(item).strip().upper() for item in value if str(item).strip()]
    return []


def _bulk_entries(
    destinations: list[dict[str, Any]],
    default_template_data: dict[str, Any] | str | None,
) -> list[dict[str, Any]]:
    """Turn destination dicts into SES ``BulkEmailEntries`` objects."""
    entries: list[dict[str, Any]] = []
    for item in destinations:
        if not isinstance(item, dict):
            continue
        destination: dict[str, Any] = {
            "ToAddresses": _address_list(
                item.get("to_addresses", item.get("toAddresses", item.get("ToAddresses")))
            )
        }
        cc = _address_list(
            item.get("cc_addresses", item.get("ccAddresses", item.get("CcAddresses")))
        )
        if cc:
            destination["CcAddresses"] = cc
        bcc = _address_list(
            item.get("bcc_addresses", item.get("bccAddresses", item.get("BccAddresses")))
        )
        if bcc:
            destination["BccAddresses"] = bcc

        raw_data = item.get(
            "template_data", item.get("templateData", item.get("TemplateData"))
        )
        data = raw_data if raw_data is not None else default_template_data
        entries.append(
            {
                "Destination": destination,
                "ReplacementEmailContent": {
                    "ReplacementTemplate": {"ReplacementTemplateData": _template_data(data)}
                },
            }
        )
    return entries


# --- Response parsing helpers ------------------------------------------------


def _parse_dkim(raw: Any) -> DkimAttributes | None:
    if not isinstance(raw, dict):
        return None
    tokens = raw.get("Tokens")
    return DkimAttributes(
        signing_enabled=raw.get("SigningEnabled"),
        status=raw.get("Status"),
        tokens=[str(token) for token in tokens] if isinstance(tokens, list) else [],
        signing_attributes_origin=raw.get("SigningAttributesOrigin"),
        next_signing_key_length=raw.get("NextSigningKeyLength"),
        current_signing_key_length=raw.get("CurrentSigningKeyLength"),
        last_key_generation_timestamp=raw.get("LastKeyGenerationTimestamp"),
        signing_hosted_zone=raw.get("SigningHostedZone"),
    )


def _parse_mail_from(raw: Any) -> MailFromAttributes | None:
    if not isinstance(raw, dict):
        return None
    return MailFromAttributes(
        mail_from_domain=raw.get("MailFromDomain"),
        mail_from_domain_status=raw.get("MailFromDomainStatus"),
        behavior_on_mx_failure=raw.get("BehaviorOnMxFailure"),
    )


def _parse_verification_info(raw: Any) -> VerificationInfo | None:
    if not isinstance(raw, dict):
        return None
    soa = raw.get("SOARecord")
    return VerificationInfo(
        error_type=raw.get("ErrorType"),
        last_checked_timestamp=raw.get("LastCheckedTimestamp"),
        last_success_timestamp=raw.get("LastSuccessTimestamp"),
        soa_record=soa if isinstance(soa, dict) else None,
    )


def _parse_tags(raw: Any) -> list[IdentityTag]:
    if not isinstance(raw, list):
        return []
    return [
        IdentityTag(key=item.get("Key"), value=item.get("Value"))
        for item in raw
        if isinstance(item, dict)
    ]


# --- Input schemas (args_schema for each @tool) ------------------------------


class SendEmailInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    from_address: str = Field(description="Verified sender email address")
    to_addresses: list[str] = Field(description="Recipient email addresses")
    subject: str = Field(description="Email subject line")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")
    body_html: str | None = Field(default=None, description="HTML email body")
    body_text: str | None = Field(default=None, description="Plain text email body")
    cc_addresses: list[str] | None = Field(default=None, description="CC email addresses")
    bcc_addresses: list[str] | None = Field(default=None, description="BCC email addresses")
    reply_to_addresses: list[str] | None = Field(
        default=None, description="Reply-To email addresses"
    )
    configuration_set_name: str | None = Field(
        default=None, description="Configuration set to apply to the send"
    )


class SendTemplatedEmailInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    from_address: str = Field(description="Verified sender email address")
    to_addresses: list[str] = Field(description="Recipient email addresses")
    template_name: str = Field(description="Name of the email template to render")
    template_data: dict[str, Any] | str = Field(
        description="Template variables as a JSON object (or JSON string)"
    )
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")
    cc_addresses: list[str] | None = Field(default=None, description="CC email addresses")
    bcc_addresses: list[str] | None = Field(default=None, description="BCC email addresses")
    configuration_set_name: str | None = Field(
        default=None, description="Configuration set to apply to the send"
    )


class SendBulkEmailInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    from_address: str = Field(description="Verified sender email address")
    template_name: str = Field(description="Name of the email template to render")
    destinations: list[dict[str, Any]] = Field(
        description=(
            'Destinations, e.g. [{"to_addresses": ["a@example.com"], '
            '"template_data": {"name": "A"}}]'
        )
    )
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")
    default_template_data: dict[str, Any] | str | None = Field(
        default=None, description="Fallback template variables for destinations without their own"
    )
    configuration_set_name: str | None = Field(
        default=None, description="Configuration set to apply to the send"
    )


class ListIdentitiesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")
    page_size: int | None = Field(
        default=None, description="Number of identities to return (0-1000)"
    )
    next_token: str | None = Field(
        default=None, description="Pagination token from a previous call"
    )


class GetAccountInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")


class CreateTemplateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    template_name: str = Field(description="Unique name for the email template")
    subject_part: str = Field(description="Subject line, supports {{variable}} substitution")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")
    html_part: str | None = Field(default=None, description="HTML body of the template")
    text_part: str | None = Field(default=None, description="Plain text body of the template")


class GetTemplateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    template_name: str = Field(description="Name of the template to retrieve")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")


class ListTemplatesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")
    page_size: int | None = Field(
        default=None, description="Number of templates to return (1-100)"
    )
    next_token: str | None = Field(
        default=None, description="Pagination token from a previous call"
    )


class DeleteTemplateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    template_name: str = Field(description="Name of the template to delete")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")


class UpdateTemplateInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    template_name: str = Field(description="Name of the template to update")
    subject_part: str = Field(description="Subject line of the template")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")
    html_part: str | None = Field(default=None, description="HTML body of the template")
    text_part: str | None = Field(default=None, description="Plain text body of the template")


class SendCustomVerificationEmailInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email_address: str = Field(description="Email address to verify")
    template_name: str = Field(description="Custom verification email template name")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")
    configuration_set_name: str | None = Field(
        default=None, description="Configuration set to apply to the send"
    )


class CreateEmailIdentityInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email_identity: str = Field(description="Email address or domain to verify")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")
    dkim_signing_attributes: dict[str, Any] | None = Field(
        default=None,
        description=(
            'BYODKIM settings, e.g. {"domain_signing_selector": "selector1", '
            '"domain_signing_private_key": "base64-key"}'
        ),
    )
    tags: list[dict[str, Any]] | None = Field(
        default=None, description='Tags, e.g. [{"key": "team", "value": "growth"}]'
    )
    configuration_set_name: str | None = Field(
        default=None, description="Default configuration set for this identity"
    )


class GetEmailIdentityInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email_identity: str = Field(description="Email address or domain identity")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")


class DeleteEmailIdentityInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email_identity: str = Field(description="Email address or domain identity to delete")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")


class PutSuppressedDestinationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email_address: str = Field(description="Email address to add to the suppression list")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")
    reason: str = Field(default="BOUNCE", description="Suppression reason: BOUNCE or COMPLAINT")


class GetSuppressedDestinationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email_address: str = Field(description="Suppressed email address to look up")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")


class ListSuppressedDestinationsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")
    reasons: list[str] | None = Field(
        default=None, description="Filter by reason: BOUNCE and/or COMPLAINT"
    )
    start_date: str | None = Field(default=None, description="ISO 8601 lower bound timestamp")
    end_date: str | None = Field(default=None, description="ISO 8601 upper bound timestamp")
    page_size: int | None = Field(default=None, description="Number of addresses to return")
    next_token: str | None = Field(
        default=None, description="Pagination token from a previous call"
    )


class DeleteSuppressedDestinationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    email_address: str = Field(description="Email address to remove from the suppression list")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")


class CreateConfigurationSetInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    configuration_set_name: str = Field(description="Name for the new configuration set")
    region: str = Field(default=_DEFAULT_REGION, description="AWS region, e.g. us-east-1")
    custom_redirect_domain: str | None = Field(
        default=None, description="Custom domain for open/click tracking links"
    )
    https_policy: str | None = Field(
        default=None, description="Tracking link policy: REQUIRE, REQUIRE_OPEN_ONLY, or OPTIONAL"
    )
    tls_policy: str | None = Field(
        default=None, description="Delivery TLS policy: REQUIRE or OPTIONAL"
    )
    sending_pool_name: str | None = Field(default=None, description="Dedicated IP pool name")
    reputation_metrics_enabled: bool | None = Field(
        default=None, description="Whether to collect reputation metrics"
    )
    sending_enabled: bool | None = Field(
        default=None, description="Whether sending is enabled for this configuration set"
    )
    suppressed_reasons: list[str] | None = Field(
        default=None, description="Auto-suppression reasons: BOUNCE and/or COMPLAINT"
    )
    tags: list[dict[str, Any]] | None = Field(
        default=None, description='Tags, e.g. [{"key": "team", "value": "growth"}]'
    )


# --- @tool functions ---------------------------------------------------------


@tool(args_schema=SendEmailInput)
@serialize_pydantic_return
async def send_email(
    auth_type: str,
    auth_data: dict[str, Any],
    from_address: str,
    to_addresses: list[str],
    subject: str,
    region: str = _DEFAULT_REGION,
    body_html: str | None = None,
    body_text: str | None = None,
    cc_addresses: list[str] | None = None,
    bcc_addresses: list[str] | None = None,
    reply_to_addresses: list[str] | None = None,
    configuration_set_name: str | None = None,
) -> SendEmailOutput:
    """Send an email through Amazon SES using simple text or HTML content."""
    body_content: dict[str, Any] = {}
    if body_html:
        body_content["Html"] = {"Data": body_html, "Charset": "UTF-8"}
    if body_text:
        body_content["Text"] = {"Data": body_text, "Charset": "UTF-8"}
    if not body_content:
        body_content["Text"] = {"Data": "", "Charset": "UTF-8"}

    destination: dict[str, Any] = {"ToAddresses": _address_list(to_addresses)}
    cc = _address_list(cc_addresses)
    if cc:
        destination["CcAddresses"] = cc
    bcc = _address_list(bcc_addresses)
    if bcc:
        destination["BccAddresses"] = bcc

    payload: dict[str, Any] = {
        "FromEmailAddress": from_address,
        "Destination": destination,
        "Content": {
            "Simple": {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": body_content,
            }
        },
    }
    reply_to = _address_list(reply_to_addresses)
    if reply_to:
        payload["ReplyToAddresses"] = reply_to
    if configuration_set_name:
        payload["ConfigurationSetName"] = configuration_set_name

    data, error = await _ses_request(
        "POST", "/v2/email/outbound-emails", region, auth_data, body=payload
    )
    if error:
        return SendEmailOutput(success=False, error=error)
    return SendEmailOutput(success=True, message_id=data.get("MessageId"))


@tool(args_schema=SendTemplatedEmailInput)
@serialize_pydantic_return
async def send_templated_email(
    auth_type: str,
    auth_data: dict[str, Any],
    from_address: str,
    to_addresses: list[str],
    template_name: str,
    template_data: dict[str, Any] | str,
    region: str = _DEFAULT_REGION,
    cc_addresses: list[str] | None = None,
    bcc_addresses: list[str] | None = None,
    configuration_set_name: str | None = None,
) -> SendTemplatedEmailOutput:
    """Send an email rendered from an Amazon SES template with dynamic data."""
    destination: dict[str, Any] = {"ToAddresses": _address_list(to_addresses)}
    cc = _address_list(cc_addresses)
    if cc:
        destination["CcAddresses"] = cc
    bcc = _address_list(bcc_addresses)
    if bcc:
        destination["BccAddresses"] = bcc

    payload: dict[str, Any] = {
        "FromEmailAddress": from_address,
        "Destination": destination,
        "Content": {
            "Template": {
                "TemplateName": template_name,
                "TemplateData": _template_data(template_data),
            }
        },
    }
    if configuration_set_name:
        payload["ConfigurationSetName"] = configuration_set_name

    data, error = await _ses_request(
        "POST", "/v2/email/outbound-emails", region, auth_data, body=payload
    )
    if error:
        return SendTemplatedEmailOutput(success=False, error=error)
    return SendTemplatedEmailOutput(success=True, message_id=data.get("MessageId"))


@tool(args_schema=SendBulkEmailInput)
@serialize_pydantic_return
async def send_bulk_email(
    auth_type: str,
    auth_data: dict[str, Any],
    from_address: str,
    template_name: str,
    destinations: list[dict[str, Any]],
    region: str = _DEFAULT_REGION,
    default_template_data: dict[str, Any] | str | None = None,
    configuration_set_name: str | None = None,
) -> SendBulkEmailOutput:
    """Send a templated email to many recipients with per-recipient data."""
    entries = _bulk_entries(destinations, default_template_data)
    if not entries:
        return SendBulkEmailOutput(
            success=False, error="No destinations were provided for the bulk send."
        )

    payload: dict[str, Any] = {
        "FromEmailAddress": from_address,
        "DefaultContent": {
            "Template": {
                "TemplateName": template_name,
                "TemplateData": _template_data(default_template_data),
            }
        },
        "BulkEmailEntries": entries,
    }
    if configuration_set_name:
        payload["ConfigurationSetName"] = configuration_set_name

    data, error = await _ses_request(
        "POST", "/v2/email/outbound-bulk-emails", region, auth_data, body=payload
    )
    if error:
        return SendBulkEmailOutput(success=False, error=error)

    raw_results = data.get("BulkEmailEntryResults")
    results = [
        BulkEmailResult(
            message_id=item.get("MessageId"),
            status=item.get("Status"),
            error=item.get("Error"),
        )
        for item in raw_results
        if isinstance(item, dict)
    ] if isinstance(raw_results, list) else []
    success_count = sum(1 for item in results if (item.status or "").upper() == "SUCCESS")
    return SendBulkEmailOutput(
        success=True,
        results=results,
        success_count=success_count,
        failure_count=len(results) - success_count,
    )


@tool(args_schema=ListIdentitiesInput)
@serialize_pydantic_return
async def list_identities(
    auth_type: str,
    auth_data: dict[str, Any],
    region: str = _DEFAULT_REGION,
    page_size: int | None = None,
    next_token: str | None = None,
) -> ListIdentitiesOutput:
    """List the email identities (addresses and domains) in the account."""
    query: list[tuple[str, str]] = []
    if page_size is not None:
        query.append(("PageSize", str(page_size)))
    if next_token:
        query.append(("NextToken", next_token))

    data, error = await _ses_request(
        "GET", "/v2/email/identities", region, auth_data, query=query
    )
    if error:
        return ListIdentitiesOutput(success=False, error=error)

    raw_identities = data.get("EmailIdentities")
    identities = [
        IdentitySummary(
            identity_name=item.get("IdentityName"),
            identity_type=item.get("IdentityType"),
            sending_enabled=item.get("SendingEnabled"),
            verification_status=item.get("VerificationStatus"),
        )
        for item in raw_identities
        if isinstance(item, dict)
    ] if isinstance(raw_identities, list) else []
    return ListIdentitiesOutput(
        success=True,
        identities=identities,
        next_token=data.get("NextToken"),
        count=len(identities),
    )


@tool(args_schema=GetAccountInput)
@serialize_pydantic_return
async def get_account(
    auth_type: str,
    auth_data: dict[str, Any],
    region: str = _DEFAULT_REGION,
) -> GetAccountOutput:
    """Get the Amazon SES account sending quota, rate, and status."""
    data, error = await _ses_request("GET", "/v2/email/account", region, auth_data)
    if error:
        return GetAccountOutput(success=False, error=error)

    quota = data.get("SendQuota")
    quota_data: dict[str, Any] = quota if isinstance(quota, dict) else {}
    suppression = data.get("SuppressionAttributes")
    suppression_data: dict[str, Any] = suppression if isinstance(suppression, dict) else {}
    reasons = suppression_data.get("SuppressedReasons")
    return GetAccountOutput(
        success=True,
        sending_enabled=data.get("SendingEnabled"),
        max_24_hour_send=quota_data.get("Max24HourSend"),
        max_send_rate=quota_data.get("MaxSendRate"),
        sent_last_24_hours=quota_data.get("SentLast24Hours"),
        production_access_enabled=data.get("ProductionAccessEnabled"),
        enforcement_status=data.get("EnforcementStatus"),
        dedicated_ip_auto_warmup_enabled=data.get("DedicatedIpAutoWarmupEnabled"),
        suppressed_reasons=[str(item) for item in reasons] if isinstance(reasons, list) else [],
    )


@tool(args_schema=CreateTemplateInput)
@serialize_pydantic_return
async def create_template(
    auth_type: str,
    auth_data: dict[str, Any],
    template_name: str,
    subject_part: str,
    region: str = _DEFAULT_REGION,
    html_part: str | None = None,
    text_part: str | None = None,
) -> CreateTemplateOutput:
    """Create a reusable Amazon SES email template."""
    content: dict[str, Any] = {"Subject": subject_part}
    if html_part:
        content["Html"] = html_part
    if text_part:
        content["Text"] = text_part

    _, error = await _ses_request(
        "POST",
        "/v2/email/templates",
        region,
        auth_data,
        body={"TemplateName": template_name, "TemplateContent": content},
    )
    if error:
        return CreateTemplateOutput(success=False, error=error)
    return CreateTemplateOutput(
        success=True,
        message=f"Template '{template_name}' created successfully.",
        template_name=template_name,
    )


@tool(args_schema=GetTemplateInput)
@serialize_pydantic_return
async def get_template(
    auth_type: str,
    auth_data: dict[str, Any],
    template_name: str,
    region: str = _DEFAULT_REGION,
) -> GetTemplateOutput:
    """Retrieve the subject, HTML, and text content of an email template."""
    path = f"/v2/email/templates/{quote(template_name, safe='')}"
    data, error = await _ses_request("GET", path, region, auth_data)
    if error:
        return GetTemplateOutput(success=False, error=error)

    content = data.get("TemplateContent")
    content_data: dict[str, Any] = content if isinstance(content, dict) else {}
    return GetTemplateOutput(
        success=True,
        template_name=data.get("TemplateName", template_name),
        subject_part=content_data.get("Subject"),
        html_part=content_data.get("Html"),
        text_part=content_data.get("Text"),
    )


@tool(args_schema=ListTemplatesInput)
@serialize_pydantic_return
async def list_templates(
    auth_type: str,
    auth_data: dict[str, Any],
    region: str = _DEFAULT_REGION,
    page_size: int | None = None,
    next_token: str | None = None,
) -> ListTemplatesOutput:
    """List the email templates in the account."""
    query: list[tuple[str, str]] = []
    if page_size is not None:
        query.append(("PageSize", str(page_size)))
    if next_token:
        query.append(("NextToken", next_token))

    data, error = await _ses_request(
        "GET", "/v2/email/templates", region, auth_data, query=query
    )
    if error:
        return ListTemplatesOutput(success=False, error=error)

    raw_templates = data.get("TemplatesMetadata")
    templates = [
        TemplateSummary(
            template_name=item.get("TemplateName"),
            created_timestamp=item.get("CreatedTimestamp"),
        )
        for item in raw_templates
        if isinstance(item, dict)
    ] if isinstance(raw_templates, list) else []
    return ListTemplatesOutput(
        success=True,
        templates=templates,
        next_token=data.get("NextToken"),
        count=len(templates),
    )


@tool(args_schema=DeleteTemplateInput)
@serialize_pydantic_return
async def delete_template(
    auth_type: str,
    auth_data: dict[str, Any],
    template_name: str,
    region: str = _DEFAULT_REGION,
) -> DeleteTemplateOutput:
    """Delete an email template from the account."""
    path = f"/v2/email/templates/{quote(template_name, safe='')}"
    _, error = await _ses_request("DELETE", path, region, auth_data)
    if error:
        return DeleteTemplateOutput(success=False, error=error)
    return DeleteTemplateOutput(
        success=True,
        message=f"Template '{template_name}' deleted successfully.",
        template_name=template_name,
    )


@tool(args_schema=UpdateTemplateInput)
@serialize_pydantic_return
async def update_template(
    auth_type: str,
    auth_data: dict[str, Any],
    template_name: str,
    subject_part: str,
    region: str = _DEFAULT_REGION,
    html_part: str | None = None,
    text_part: str | None = None,
) -> UpdateTemplateOutput:
    """Update the subject, HTML, and text content of an email template."""
    content: dict[str, Any] = {"Subject": subject_part}
    if html_part:
        content["Html"] = html_part
    if text_part:
        content["Text"] = text_part

    path = f"/v2/email/templates/{quote(template_name, safe='')}"
    _, error = await _ses_request(
        "PUT", path, region, auth_data, body={"TemplateContent": content}
    )
    if error:
        return UpdateTemplateOutput(success=False, error=error)
    return UpdateTemplateOutput(
        success=True,
        message=f"Template '{template_name}' updated successfully.",
        template_name=template_name,
    )


@tool(args_schema=SendCustomVerificationEmailInput)
@serialize_pydantic_return
async def send_custom_verification_email(
    auth_type: str,
    auth_data: dict[str, Any],
    email_address: str,
    template_name: str,
    region: str = _DEFAULT_REGION,
    configuration_set_name: str | None = None,
) -> SendCustomVerificationEmailOutput:
    """Send a custom verification email to an address to verify it."""
    payload: dict[str, Any] = {
        "EmailAddress": email_address,
        "TemplateName": template_name,
    }
    if configuration_set_name:
        payload["ConfigurationSetName"] = configuration_set_name

    data, error = await _ses_request(
        "POST",
        "/v2/email/outbound-custom-verification-emails",
        region,
        auth_data,
        body=payload,
    )
    if error:
        return SendCustomVerificationEmailOutput(success=False, error=error)
    return SendCustomVerificationEmailOutput(success=True, message_id=data.get("MessageId"))


@tool(args_schema=CreateEmailIdentityInput)
@serialize_pydantic_return
async def create_email_identity(
    auth_type: str,
    auth_data: dict[str, Any],
    email_identity: str,
    region: str = _DEFAULT_REGION,
    dkim_signing_attributes: dict[str, Any] | None = None,
    tags: list[dict[str, Any]] | None = None,
    configuration_set_name: str | None = None,
) -> CreateEmailIdentityOutput:
    """Start verification of an email address or domain identity."""
    payload: dict[str, Any] = {"EmailIdentity": email_identity}
    dkim = _dkim_payload(dkim_signing_attributes)
    if dkim:
        payload["DkimSigningAttributes"] = dkim
    tag_payload = _tag_payload(tags)
    if tag_payload:
        payload["Tags"] = tag_payload
    if configuration_set_name:
        payload["ConfigurationSetName"] = configuration_set_name

    data, error = await _ses_request(
        "POST", "/v2/email/identities", region, auth_data, body=payload
    )
    if error:
        return CreateEmailIdentityOutput(success=False, error=error)
    return CreateEmailIdentityOutput(
        success=True,
        identity_type=data.get("IdentityType"),
        verified_for_sending_status=data.get("VerifiedForSendingStatus"),
        dkim_attributes=_parse_dkim(data.get("DkimAttributes")),
    )


@tool(args_schema=GetEmailIdentityInput)
@serialize_pydantic_return
async def get_email_identity(
    auth_type: str,
    auth_data: dict[str, Any],
    email_identity: str,
    region: str = _DEFAULT_REGION,
) -> GetEmailIdentityOutput:
    """Get verification, DKIM, and MAIL FROM details for an identity."""
    path = f"/v2/email/identities/{quote(email_identity, safe='')}"
    data, error = await _ses_request("GET", path, region, auth_data)
    if error:
        return GetEmailIdentityOutput(success=False, error=error)

    policies = data.get("Policies")
    policy_map = (
        {str(key): str(value) for key, value in policies.items()}
        if isinstance(policies, dict)
        else None
    )
    return GetEmailIdentityOutput(
        success=True,
        identity_type=data.get("IdentityType"),
        verified_for_sending_status=data.get("VerifiedForSendingStatus"),
        verification_status=data.get("VerificationStatus"),
        feedback_forwarding_status=data.get("FeedbackForwardingStatus"),
        configuration_set_name=data.get("ConfigurationSetName"),
        dkim_attributes=_parse_dkim(data.get("DkimAttributes")),
        mail_from_attributes=_parse_mail_from(data.get("MailFromAttributes")),
        policies=policy_map,
        tags=_parse_tags(data.get("Tags")),
        verification_info=_parse_verification_info(data.get("VerificationInfo")),
    )


@tool(args_schema=DeleteEmailIdentityInput)
@serialize_pydantic_return
async def delete_email_identity(
    auth_type: str,
    auth_data: dict[str, Any],
    email_identity: str,
    region: str = _DEFAULT_REGION,
) -> DeleteEmailIdentityOutput:
    """Delete an email address or domain identity from the account."""
    path = f"/v2/email/identities/{quote(email_identity, safe='')}"
    _, error = await _ses_request("DELETE", path, region, auth_data)
    if error:
        return DeleteEmailIdentityOutput(success=False, error=error)
    return DeleteEmailIdentityOutput(
        success=True,
        message=f"Identity '{email_identity}' deleted successfully.",
        email_identity=email_identity,
    )


@tool(args_schema=PutSuppressedDestinationInput)
@serialize_pydantic_return
async def put_suppressed_destination(
    auth_type: str,
    auth_data: dict[str, Any],
    email_address: str,
    region: str = _DEFAULT_REGION,
    reason: str = "BOUNCE",
) -> PutSuppressedDestinationOutput:
    """Add an email address to the account-level suppression list."""
    normalized_reason = (reason or "BOUNCE").strip().upper()
    _, error = await _ses_request(
        "PUT",
        "/v2/email/suppression/addresses",
        region,
        auth_data,
        body={"EmailAddress": email_address, "Reason": normalized_reason},
    )
    if error:
        return PutSuppressedDestinationOutput(success=False, error=error)
    return PutSuppressedDestinationOutput(
        success=True,
        message=f"'{email_address}' added to the suppression list ({normalized_reason}).",
        email_address=email_address,
        reason=normalized_reason,
    )


@tool(args_schema=GetSuppressedDestinationInput)
@serialize_pydantic_return
async def get_suppressed_destination(
    auth_type: str,
    auth_data: dict[str, Any],
    email_address: str,
    region: str = _DEFAULT_REGION,
) -> GetSuppressedDestinationOutput:
    """Look up a single address on the account-level suppression list."""
    path = f"/v2/email/suppression/addresses/{quote(email_address, safe='')}"
    data, error = await _ses_request("GET", path, region, auth_data)
    if error:
        return GetSuppressedDestinationOutput(success=False, error=error)

    destination = data.get("SuppressedDestination")
    destination_data: dict[str, Any] = destination if isinstance(destination, dict) else {}
    attributes = destination_data.get("Attributes")
    attributes_data: dict[str, Any] = attributes if isinstance(attributes, dict) else {}
    return GetSuppressedDestinationOutput(
        success=True,
        email_address=destination_data.get("EmailAddress", email_address),
        reason=destination_data.get("Reason"),
        last_update_time=destination_data.get("LastUpdateTime"),
        message_id=attributes_data.get("MessageId"),
        feedback_id=attributes_data.get("FeedbackId"),
    )


@tool(args_schema=ListSuppressedDestinationsInput)
@serialize_pydantic_return
async def list_suppressed_destinations(
    auth_type: str,
    auth_data: dict[str, Any],
    region: str = _DEFAULT_REGION,
    reasons: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    page_size: int | None = None,
    next_token: str | None = None,
) -> ListSuppressedDestinationsOutput:
    """List addresses on the account-level suppression list."""
    query: list[tuple[str, str]] = [("Reason", value) for value in _reason_list(reasons)]
    if start_date:
        query.append(("StartDate", start_date))
    if end_date:
        query.append(("EndDate", end_date))
    if page_size is not None:
        query.append(("PageSize", str(page_size)))
    if next_token:
        query.append(("NextToken", next_token))

    data, error = await _ses_request(
        "GET", "/v2/email/suppression/addresses", region, auth_data, query=query
    )
    if error:
        return ListSuppressedDestinationsOutput(success=False, error=error)

    raw_destinations = data.get("SuppressedDestinationSummaries")
    destinations = [
        SuppressedDestinationSummary(
            email_address=item.get("EmailAddress"),
            reason=item.get("Reason"),
            last_update_time=item.get("LastUpdateTime"),
        )
        for item in raw_destinations
        if isinstance(item, dict)
    ] if isinstance(raw_destinations, list) else []
    return ListSuppressedDestinationsOutput(
        success=True,
        destinations=destinations,
        next_token=data.get("NextToken"),
        count=len(destinations),
    )


@tool(args_schema=DeleteSuppressedDestinationInput)
@serialize_pydantic_return
async def delete_suppressed_destination(
    auth_type: str,
    auth_data: dict[str, Any],
    email_address: str,
    region: str = _DEFAULT_REGION,
) -> DeleteSuppressedDestinationOutput:
    """Remove an email address from the account-level suppression list."""
    path = f"/v2/email/suppression/addresses/{quote(email_address, safe='')}"
    _, error = await _ses_request("DELETE", path, region, auth_data)
    if error:
        return DeleteSuppressedDestinationOutput(success=False, error=error)
    return DeleteSuppressedDestinationOutput(
        success=True,
        message=f"'{email_address}' removed from the suppression list.",
        email_address=email_address,
    )


@tool(args_schema=CreateConfigurationSetInput)
@serialize_pydantic_return
async def create_configuration_set(
    auth_type: str,
    auth_data: dict[str, Any],
    configuration_set_name: str,
    region: str = _DEFAULT_REGION,
    custom_redirect_domain: str | None = None,
    https_policy: str | None = None,
    tls_policy: str | None = None,
    sending_pool_name: str | None = None,
    reputation_metrics_enabled: bool | None = None,
    sending_enabled: bool | None = None,
    suppressed_reasons: list[str] | None = None,
    tags: list[dict[str, Any]] | None = None,
) -> CreateConfigurationSetOutput:
    """Create a configuration set that groups sending rules for emails."""
    payload: dict[str, Any] = {"ConfigurationSetName": configuration_set_name}

    tracking: dict[str, Any] = {}
    if custom_redirect_domain:
        tracking["CustomRedirectDomain"] = custom_redirect_domain
    if https_policy:
        tracking["HttpsPolicy"] = https_policy.strip().upper()
    if tracking:
        payload["TrackingOptions"] = tracking

    delivery: dict[str, Any] = {}
    if tls_policy:
        delivery["TlsPolicy"] = tls_policy.strip().upper()
    if sending_pool_name:
        delivery["SendingPoolName"] = sending_pool_name
    if delivery:
        payload["DeliveryOptions"] = delivery

    if reputation_metrics_enabled is not None:
        payload["ReputationOptions"] = {"ReputationMetricsEnabled": reputation_metrics_enabled}
    if sending_enabled is not None:
        payload["SendingOptions"] = {"SendingEnabled": sending_enabled}

    reason_values = _reason_list(suppressed_reasons)
    if reason_values:
        payload["SuppressionOptions"] = {"SuppressedReasons": reason_values}
    tag_payload = _tag_payload(tags)
    if tag_payload:
        payload["Tags"] = tag_payload

    _, error = await _ses_request(
        "POST", "/v2/email/configuration-sets", region, auth_data, body=payload
    )
    if error:
        return CreateConfigurationSetOutput(success=False, error=error)
    return CreateConfigurationSetOutput(
        success=True,
        message=f"Configuration set '{configuration_set_name}' created successfully.",
        configuration_set_name=configuration_set_name,
    )
