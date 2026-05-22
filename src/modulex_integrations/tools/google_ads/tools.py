"""Google Ads LangChain @tool functions."""
from __future__ import annotations

import hashlib
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_ads.outputs import (
    AccessibleCustomer,
    AddContactToListByEmailOutput,
    CreateAdGroupReportOutput,
    CreateAdReportOutput,
    CreateCampaignReportOutput,
    CreateCustomerListOutput,
    CreateCustomerReportOutput,
    CreateReportOutput,
    GenerateKeywordIdeasOutput,
    ListAccountIdOptionsOutput,
    SendOfflineConversionOutput,
)

__all__ = [
    "add_contact_to_list_by_email",
    "create_ad_group_report",
    "create_ad_report",
    "create_campaign_report",
    "create_customer_list",
    "create_customer_report",
    "create_report",
    "generate_keyword_ideas",
    "list_account_id_options",
    "send_offline_conversion",
]

_BASE_URL = "https://googleads.googleapis.com"
_API_VERSION = "v21"
_KEYWORD_IDEAS_VERSION = "v22"
_TIMEOUT = 30.0

_CORE_DATE_SEGMENTS = (
    "segments.date",
    "segments.week",
    "segments.month",
    "segments.quarter",
    "segments.year",
)

_DATE_RANGE_CONSTANTS = (
    "CUSTOM",
    "TODAY",
    "YESTERDAY",
    "LAST_7_DAYS",
    "LAST_BUSINESS_WEEK",
    "THIS_MONTH",
    "LAST_MONTH",
    "LAST_14_DAYS",
    "LAST_30_DAYS",
    "THIS_WEEK_SUN_TODAY",
    "THIS_WEEK_MON_TODAY",
    "LAST_WEEK_SUN_SAT",
    "LAST_WEEK_MON_SUN",
)


def _get_auth_headers(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str | None = None,
) -> dict[str, str]:
    """Build Google Ads API headers.

    Google Ads requires three pieces:
      - Authorization: Bearer <access_token>
      - developer-token: <pre-approved developer token>
      - login-customer-id: <manager account id> (when calling under a manager)
    """
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    developer_token = auth_data.get("developer_token") or auth_data.get(
        "GOOGLE_ADS_DEVELOPER_TOKEN"
    )
    if developer_token:
        headers["developer-token"] = developer_token
    if account_id:
        headers["login-customer-id"] = str(account_id).replace("-", "")
    return headers


def _missing_credentials_error(auth_type: str, auth_data: dict[str, Any]) -> str | None:
    if auth_type != "oauth2":
        return (
            f"Unsupported auth_type {auth_type!r}; google_ads only supports oauth2."
        )
    if not auth_data.get("access_token"):
        return "OAuth access_token is missing from auth_data."
    if not (
        auth_data.get("developer_token") or auth_data.get("GOOGLE_ADS_DEVELOPER_TOKEN")
    ):
        return (
            "Google Ads developer token is missing. Configure "
            "GOOGLE_ADS_DEVELOPER_TOKEN in the credential."
        )
    return None


def _resolve_client_id(
    account_id: str, customer_client_id: str | None
) -> str:
    """Return the customer client ID to embed in the URL path."""
    cid = customer_client_id or account_id
    return str(cid).replace("-", "")


def _check_prefix(values: list[str] | None, prefix: str) -> list[str]:
    """Prepend ``prefix.`` to each value if not already present."""
    if not values:
        return []
    out: list[str] = []
    for v in values:
        if not v:
            continue
        s = str(v)
        out.append(s if s.startswith(f"{prefix}.") else f"{prefix}.{s}")
    return out


def _build_gaql(
    *,
    resource: str,
    fields: list[str] | None,
    segments: list[str] | None,
    metrics: list[str] | None,
    object_filter: list[str] | None,
    date_range: str | None,
    start_date: str | None,
    end_date: str | None,
    order_by: str | None,
    direction: str | None,
    limit: int | None,
) -> tuple[str | None, str | None]:
    """Build a GAQL SELECT query string. Returns (query, error)."""
    if date_range and date_range not in _DATE_RANGE_CONSTANTS:
        return None, (
            f"date_range {date_range!r} is not a recognized Google Ads "
            f"DATE_RANGE constant."
        )
    if date_range == "CUSTOM" and (not start_date or not end_date):
        return None, "date_range=CUSTOM requires both start_date and end_date."
    filtered_segments = (
        segments
        if date_range
        else [s for s in (segments or []) if s not in _CORE_DATE_SEGMENTS]
    )
    selection = [
        *_check_prefix(fields, resource),
        *_check_prefix(filtered_segments, "segments"),
        *_check_prefix(metrics, "metrics"),
    ]
    if not selection:
        return None, "Select at least one field, segment, or metric."
    if (
        not date_range
        and order_by
        and order_by in _CORE_DATE_SEGMENTS
    ):
        return None, (
            f"Cannot order by {order_by!r} without a date_range. Either set "
            f"a date_range or choose a different order_by field."
        )

    query = f"SELECT {', '.join(selection)} FROM {resource}"
    where_clauses: list[str] = []
    if object_filter:
        filter_field = (
            "ad_group_ad.ad" if resource == "ad_group_ad" else resource
        )
        ids = ", ".join(str(i) for i in object_filter)
        where_clauses.append(f"{filter_field}.id IN ({ids})")
    if date_range:
        if date_range == "CUSTOM":
            where_clauses.append(
                f"segments.date BETWEEN '{start_date}' AND '{end_date}'"
            )
        else:
            where_clauses.append(f"segments.date DURING {date_range}")
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    if order_by and direction:
        query += f" ORDER BY {order_by} {direction}"
    if limit:
        query += f" LIMIT {limit}"
    return query, None


async def _search(
    *,
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    customer_client_id: str | None,
    query: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """POST GoogleAdsService.search. Returns (response_json, error)."""
    cid = _resolve_client_id(account_id, customer_client_id)
    url = f"{_BASE_URL}/{_API_VERSION}/customers/{cid}/googleAds:search"
    headers = _get_auth_headers(auth_type, auth_data, account_id)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                url, headers=headers, json={"query": query}
            )
        if response.status_code != 200:
            return None, (
                f"Google Ads API error ({response.status_code}): {response.text}"
            )
        return response.json(), None
    except httpx.TimeoutException:
        return None, "Request to Google Ads API timed out."
    except Exception as exc:
        return None, f"Call failed: {exc}"


async def _post(
    *,
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    path: str,
    payload: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    headers = _get_auth_headers(auth_type, auth_data, account_id)
    url = f"{_BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(url, headers=headers, json=payload)
        if response.status_code not in (200, 201):
            return None, (
                f"Google Ads API error ({response.status_code}): {response.text}"
            )
        return response.json(), None
    except httpx.TimeoutException:
        return None, "Request to Google Ads API timed out."
    except Exception as exc:
        return None, f"Call failed: {exc}"


async def _get(
    *,
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str | None,
    path: str,
) -> tuple[dict[str, Any] | None, str | None]:
    headers = _get_auth_headers(auth_type, auth_data, account_id)
    url = f"{_BASE_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            return None, (
                f"Google Ads API error ({response.status_code}): {response.text}"
            )
        return response.json(), None
    except httpx.TimeoutException:
        return None, "Request to Google Ads API timed out."
    except Exception as exc:
        return None, f"Call failed: {exc}"


# --- Input schemas --------------------------------------------------------


class AddContactToListByEmailInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing access_token + developer_token"
    )
    account_id: str = Field(description="Login customer ID")
    user_list_id: str = Field(description="ID of the customer match user list")
    contact_email: str = Field(description="Email to add to the list")
    customer_client_id: str | None = Field(
        default=None, description="Managed customer ID (defaults to account_id)"
    )


class ReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing access_token + developer_token"
    )
    account_id: str = Field(description="Login customer ID")
    fields: list[str] | None = Field(
        default=None, description="Resource field names to SELECT"
    )
    segments: list[str] | None = Field(
        default=None, description="Segment field names"
    )
    metrics: list[str] | None = Field(
        default=None, description="Metric field names"
    )
    object_filter: list[str] | None = Field(
        default=None, description="Resource IDs to filter by"
    )
    date_range: str | None = Field(default=None, description="Date range constant")
    start_date: str | None = Field(
        default=None, description="Custom range start (YYYY-MM-DD)"
    )
    end_date: str | None = Field(
        default=None, description="Custom range end (YYYY-MM-DD)"
    )
    order_by: str | None = Field(default=None, description="Order-by field")
    direction: str = Field(default="ASC", description="Order direction (ASC/DESC)")
    limit: int | None = Field(default=None, description="Result cap")
    customer_client_id: str | None = Field(
        default=None, description="Managed customer ID (defaults to account_id)"
    )


class CreateAdGroupReportInput(ReportInput):
    pass


class CreateAdReportInput(ReportInput):
    pass


class CreateCampaignReportInput(ReportInput):
    pass


class CreateCustomerReportInput(ReportInput):
    pass


class CreateReportInput(ReportInput):
    resource: str = Field(description="Resource name for the FROM clause")


class CreateCustomerListInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing access_token + developer_token"
    )
    account_id: str = Field(description="Login customer ID")
    name: str = Field(description="UserList name")
    list_type: str = Field(
        description=(
            "UserList variant key (e.g. crmBasedUserList, ruleBasedUserList, "
            "logicalUserList, basicUserList, lookalikeUserList)."
        )
    )
    list_type_data: dict[str, Any] = Field(
        default_factory=dict, description="Variant-specific payload"
    )
    description: str | None = Field(
        default=None, description="Optional UserList description"
    )
    additional_fields: dict[str, Any] = Field(
        default_factory=dict, description="Additional UserList top-level fields"
    )
    customer_client_id: str | None = Field(
        default=None, description="Managed customer ID (defaults to account_id)"
    )


class GenerateKeywordIdeasInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing access_token + developer_token"
    )
    account_id: str = Field(description="Login customer ID")
    customer_client_id: str = Field(description="Managed customer ID (required)")
    additional_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="GenerateKeywordIdeasRequest body fields",
    )


class ListAccountIdOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing access_token + developer_token"
    )


class SendOfflineConversionInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing access_token + developer_token"
    )
    account_id: str = Field(description="Login customer ID")
    name: str = Field(description="Conversion action name")
    type: str = Field(description="ConversionActionType enum value")
    additional_fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional ConversionAction fields",
    )
    customer_client_id: str | None = Field(
        default=None, description="Managed customer ID (defaults to account_id)"
    )


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AddContactToListByEmailInput)
@serialize_pydantic_return
async def add_contact_to_list_by_email(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    user_list_id: str,
    contact_email: str,
    customer_client_id: str | None = None,
) -> AddContactToListByEmailOutput:
    """Add a contact to a Google Ads Customer Match user list by email."""
    err = _missing_credentials_error(auth_type, auth_data)
    if err:
        return AddContactToListByEmailOutput(success=False, error=err)
    cid = _resolve_client_id(account_id, customer_client_id)

    # Step 1: create an OfflineUserDataJob bound to the user list.
    job_payload = {
        "job": {
            "type": "CUSTOMER_MATCH_USER_LIST",
            "customerMatchUserListMetadata": {
                "userList": f"customers/{cid}/userLists/{user_list_id}",
            },
        }
    }
    job_response, err = await _post(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=account_id,
        path=f"/{_API_VERSION}/customers/{cid}/offlineUserDataJobs:create",
        payload=job_payload,
    )
    if err or not job_response:
        return AddContactToListByEmailOutput(success=False, error=err or "no job response")
    job_resource_name: str | None = job_response.get("resourceName")
    if not job_resource_name:
        return AddContactToListByEmailOutput(
            success=False, error="offlineUserDataJobs:create did not return resourceName."
        )

    # Step 2: addOperations — hash the email and upload as a userIdentifier.
    hashed_email = hashlib.sha256(contact_email.strip().lower().encode("utf-8")).hexdigest()
    ops_payload = {
        "operations": [
            {
                "create": {
                    "userIdentifiers": [{"hashedEmail": hashed_email}],
                }
            }
        ]
    }
    _, err = await _post(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=account_id,
        path=f"/{_API_VERSION}/{job_resource_name}:addOperations",
        payload=ops_payload,
    )
    if err:
        return AddContactToListByEmailOutput(
            success=False,
            error=err,
            offline_user_data_job_resource_name=job_resource_name,
        )

    # Step 3: run the job.
    run_response, err = await _post(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=account_id,
        path=f"/{_API_VERSION}/{job_resource_name}:run",
        payload={},
    )
    if err:
        return AddContactToListByEmailOutput(
            success=False,
            error=err,
            offline_user_data_job_resource_name=job_resource_name,
        )
    operation_resource_name = (
        (run_response or {}).get("name") if isinstance(run_response, dict) else None
    )
    return AddContactToListByEmailOutput(
        success=True,
        offline_user_data_job_resource_name=job_resource_name,
        operation_resource_name=operation_resource_name,
    )


async def _run_resource_report(
    *,
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    customer_client_id: str | None,
    resource: str,
    fields: list[str] | None,
    segments: list[str] | None,
    metrics: list[str] | None,
    object_filter: list[str] | None,
    date_range: str | None,
    start_date: str | None,
    end_date: str | None,
    order_by: str | None,
    direction: str | None,
    limit: int | None,
) -> tuple[str | None, dict[str, Any] | None, str | None]:
    """Shared body for the create_*_report family. Returns (query, response, error)."""
    err = _missing_credentials_error(auth_type, auth_data)
    if err:
        return None, None, err
    query, err = _build_gaql(
        resource=resource,
        fields=fields,
        segments=segments,
        metrics=metrics,
        object_filter=object_filter,
        date_range=date_range,
        start_date=start_date,
        end_date=end_date,
        order_by=order_by,
        direction=direction,
        limit=limit,
    )
    if err or query is None:
        return None, None, err
    response, err = await _search(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=account_id,
        customer_client_id=customer_client_id,
        query=query,
    )
    return query, response, err


@tool(args_schema=CreateAdGroupReportInput)
@serialize_pydantic_return
async def create_ad_group_report(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    fields: list[str] | None = None,
    segments: list[str] | None = None,
    metrics: list[str] | None = None,
    object_filter: list[str] | None = None,
    date_range: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    order_by: str | None = None,
    direction: str = "ASC",
    limit: int | None = None,
    customer_client_id: str | None = None,
) -> CreateAdGroupReportOutput:
    """Run a GAQL search report against the ad_group resource."""
    query, response, err = await _run_resource_report(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=account_id,
        customer_client_id=customer_client_id,
        resource="ad_group",
        fields=fields,
        segments=segments,
        metrics=metrics,
        object_filter=object_filter,
        date_range=date_range,
        start_date=start_date,
        end_date=end_date,
        order_by=order_by,
        direction=direction,
        limit=limit,
    )
    if err or response is None:
        return CreateAdGroupReportOutput(success=False, error=err, query=query)
    return CreateAdGroupReportOutput(
        success=True,
        query=query,
        results=response.get("results", []) or [],
        field_mask=response.get("fieldMask"),
        request_id=response.get("requestId"),
    )


@tool(args_schema=CreateAdReportInput)
@serialize_pydantic_return
async def create_ad_report(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    fields: list[str] | None = None,
    segments: list[str] | None = None,
    metrics: list[str] | None = None,
    object_filter: list[str] | None = None,
    date_range: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    order_by: str | None = None,
    direction: str = "ASC",
    limit: int | None = None,
    customer_client_id: str | None = None,
) -> CreateAdReportOutput:
    """Run a GAQL search report against the ad_group_ad resource."""
    query, response, err = await _run_resource_report(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=account_id,
        customer_client_id=customer_client_id,
        resource="ad_group_ad",
        fields=fields,
        segments=segments,
        metrics=metrics,
        object_filter=object_filter,
        date_range=date_range,
        start_date=start_date,
        end_date=end_date,
        order_by=order_by,
        direction=direction,
        limit=limit,
    )
    if err or response is None:
        return CreateAdReportOutput(success=False, error=err, query=query)
    return CreateAdReportOutput(
        success=True,
        query=query,
        results=response.get("results", []) or [],
        field_mask=response.get("fieldMask"),
        request_id=response.get("requestId"),
    )


@tool(args_schema=CreateCampaignReportInput)
@serialize_pydantic_return
async def create_campaign_report(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    fields: list[str] | None = None,
    segments: list[str] | None = None,
    metrics: list[str] | None = None,
    object_filter: list[str] | None = None,
    date_range: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    order_by: str | None = None,
    direction: str = "ASC",
    limit: int | None = None,
    customer_client_id: str | None = None,
) -> CreateCampaignReportOutput:
    """Run a GAQL search report against the campaign resource."""
    query, response, err = await _run_resource_report(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=account_id,
        customer_client_id=customer_client_id,
        resource="campaign",
        fields=fields,
        segments=segments,
        metrics=metrics,
        object_filter=object_filter,
        date_range=date_range,
        start_date=start_date,
        end_date=end_date,
        order_by=order_by,
        direction=direction,
        limit=limit,
    )
    if err or response is None:
        return CreateCampaignReportOutput(success=False, error=err, query=query)
    return CreateCampaignReportOutput(
        success=True,
        query=query,
        results=response.get("results", []) or [],
        field_mask=response.get("fieldMask"),
        request_id=response.get("requestId"),
    )


@tool(args_schema=CreateCustomerListInput)
@serialize_pydantic_return
async def create_customer_list(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    name: str,
    list_type: str,
    list_type_data: dict[str, Any] | None = None,
    description: str | None = None,
    additional_fields: dict[str, Any] | None = None,
    customer_client_id: str | None = None,
) -> CreateCustomerListOutput:
    """Create a Google Ads UserList."""
    err = _missing_credentials_error(auth_type, auth_data)
    if err:
        return CreateCustomerListOutput(success=False, error=err)
    cid = _resolve_client_id(account_id, customer_client_id)
    create_body: dict[str, Any] = {
        "name": name,
        list_type: list_type_data or {},
    }
    if description is not None:
        create_body["description"] = description
    if additional_fields:
        create_body.update(additional_fields)

    payload = {"operations": [{"create": create_body}]}
    response, err = await _post(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=account_id,
        path=f"/{_API_VERSION}/customers/{cid}/userLists:mutate",
        payload=payload,
    )
    if err or response is None:
        return CreateCustomerListOutput(success=False, error=err)
    results = response.get("results") or []
    first = results[0] if results else {}
    resource_name: str | None = first.get("resourceName")
    new_id: str | None = (
        resource_name.split("/")[-1] if resource_name else None
    )
    return CreateCustomerListOutput(
        success=True, id=new_id, resource_name=resource_name
    )


@tool(args_schema=CreateCustomerReportInput)
@serialize_pydantic_return
async def create_customer_report(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    fields: list[str] | None = None,
    segments: list[str] | None = None,
    metrics: list[str] | None = None,
    object_filter: list[str] | None = None,
    date_range: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    order_by: str | None = None,
    direction: str = "ASC",
    limit: int | None = None,
    customer_client_id: str | None = None,
) -> CreateCustomerReportOutput:
    """Run a GAQL search report against the customer resource."""
    query, response, err = await _run_resource_report(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=account_id,
        customer_client_id=customer_client_id,
        resource="customer",
        fields=fields,
        segments=segments,
        metrics=metrics,
        object_filter=object_filter,
        date_range=date_range,
        start_date=start_date,
        end_date=end_date,
        order_by=order_by,
        direction=direction,
        limit=limit,
    )
    if err or response is None:
        return CreateCustomerReportOutput(success=False, error=err, query=query)
    return CreateCustomerReportOutput(
        success=True,
        query=query,
        results=response.get("results", []) or [],
        field_mask=response.get("fieldMask"),
        request_id=response.get("requestId"),
    )


@tool(args_schema=CreateReportInput)
@serialize_pydantic_return
async def create_report(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    resource: str,
    fields: list[str] | None = None,
    segments: list[str] | None = None,
    metrics: list[str] | None = None,
    object_filter: list[str] | None = None,
    date_range: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    order_by: str | None = None,
    direction: str = "ASC",
    limit: int | None = None,
    customer_client_id: str | None = None,
) -> CreateReportOutput:
    """Run a GAQL search report against an arbitrary resource."""
    query, response, err = await _run_resource_report(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=account_id,
        customer_client_id=customer_client_id,
        resource=resource,
        fields=fields,
        segments=segments,
        metrics=metrics,
        object_filter=object_filter,
        date_range=date_range,
        start_date=start_date,
        end_date=end_date,
        order_by=order_by,
        direction=direction,
        limit=limit,
    )
    if err or response is None:
        return CreateReportOutput(success=False, error=err, query=query)
    return CreateReportOutput(
        success=True,
        query=query,
        results=response.get("results", []) or [],
        field_mask=response.get("fieldMask"),
        request_id=response.get("requestId"),
    )


@tool(args_schema=GenerateKeywordIdeasInput)
@serialize_pydantic_return
async def generate_keyword_ideas(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    customer_client_id: str,
    additional_fields: dict[str, Any] | None = None,
) -> GenerateKeywordIdeasOutput:
    """Generate keyword ideas via KeywordPlanIdeaService.generateKeywordIdeas."""
    err = _missing_credentials_error(auth_type, auth_data)
    if err:
        return GenerateKeywordIdeasOutput(success=False, error=err)
    cid = _resolve_client_id(account_id, customer_client_id)
    path = (
        f"/{_KEYWORD_IDEAS_VERSION}/customers/{cid}:generateKeywordIdeas"
    )
    response, err = await _post(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=account_id,
        path=path,
        payload=additional_fields or {},
    )
    if err or response is None:
        return GenerateKeywordIdeasOutput(success=False, error=err)
    return GenerateKeywordIdeasOutput(
        success=True,
        results=response.get("results", []) or [],
        total_size=response.get("totalSize"),
        next_page_token=response.get("nextPageToken"),
    )


@tool(args_schema=ListAccountIdOptionsInput)
@serialize_pydantic_return
async def list_account_id_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListAccountIdOptionsOutput:
    """List customers directly accessible by the authenticated user."""
    err = _missing_credentials_error(auth_type, auth_data)
    if err:
        return ListAccountIdOptionsOutput(success=False, error=err)
    response, err = await _get(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=None,
        path=f"/{_API_VERSION}/customers:listAccessibleCustomers",
    )
    if err or response is None:
        return ListAccountIdOptionsOutput(success=False, error=err)
    resource_names: list[str] = response.get("resourceNames") or []
    customers = [
        AccessibleCustomer(
            resource_name=r,
            customer_id=r.split("/")[-1] if r else None,
        )
        for r in resource_names
    ]
    return ListAccountIdOptionsOutput(success=True, customers=customers)


@tool(args_schema=SendOfflineConversionInput)
@serialize_pydantic_return
async def send_offline_conversion(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    name: str,
    type: str,
    additional_fields: dict[str, Any] | None = None,
    customer_client_id: str | None = None,
) -> SendOfflineConversionOutput:
    """Create a ConversionAction via ConversionActionService.mutate."""
    err = _missing_credentials_error(auth_type, auth_data)
    if err:
        return SendOfflineConversionOutput(success=False, error=err)
    cid = _resolve_client_id(account_id, customer_client_id)
    create_body: dict[str, Any] = {"name": name, "type": type}
    if additional_fields:
        create_body.update(additional_fields)
    payload = {"operations": [{"create": create_body}]}
    response, err = await _post(
        auth_type=auth_type,
        auth_data=auth_data,
        account_id=account_id,
        path=f"/{_API_VERSION}/customers/{cid}/conversionActions:mutate",
        payload=payload,
    )
    if err or response is None:
        return SendOfflineConversionOutput(success=False, error=err)
    results = response.get("results") or []
    first = results[0] if results else {}
    resource_name: str | None = first.get("resourceName")
    new_id: str | None = (
        resource_name.split("/")[-1] if resource_name else None
    )
    return SendOfflineConversionOutput(
        success=True, id=new_id, resource_name=resource_name
    )
