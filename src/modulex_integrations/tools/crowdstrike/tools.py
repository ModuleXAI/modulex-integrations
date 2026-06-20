"""CrowdStrike Falcon Identity Protection LangChain ``@tool`` functions.

Three async tools wrapping the CrowdStrike Falcon Identity Protection
REST API. The modulex ``ToolExecutor`` injects an ``api_key: str``
directly (the Falcon API **client secret**); the Falcon **client ID**
and **cloud region** are ordinary action parameters supplied by the
caller.

Each call is a two-step flow:

1. Exchange an OAuth2 client-credentials token at
   ``POST https://api.{cloud}.crowdstrike.com/oauth2/token`` with the
   form-encoded ``client_id`` + ``client_secret``; the response carries
   a short-lived ``access_token``.
2. Call the Identity Protection endpoint with
   ``Authorization: Bearer <access_token>``.

Error model: non-2xx responses, timeouts, and unexpected exceptions are
caught and returned as the typed output with ``success=False`` +
``error`` — nothing raises out of a ``@tool``.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.crowdstrike.outputs import (
    AggregateBucket,
    AggregateResult,
    GetSensorAggregatesOutput,
    GetSensorDetailsOutput,
    Pagination,
    QuerySensorsOutput,
    Sensor,
)

__all__ = ["get_sensor_aggregates", "get_sensor_details", "query_sensors"]

_TIMEOUT = 30.0

# Falcon cloud region -> API base host.
# Verified against CrowdStrike Falcon API docs (api.crowdstrike.com is the
# US-1 default; region-specific hosts for US-2/EU-1/GovCloud).
_CLOUD_HOSTS: dict[str, str] = {
    "us-1": "https://api.crowdstrike.com",
    "us-2": "https://api.us-2.crowdstrike.com",
    "eu-1": "https://api.eu-1.crowdstrike.com",
    "us-gov-1": "https://api.laggar.gcw.crowdstrike.com",
    "us-gov-2": "https://api.us-gov-2.crowdstrike.us",
}

_QUERY_SENSORS_PATH = "/identity-protection/queries/devices/v1"
_SENSOR_DETAILS_PATH = "/identity-protection/entities/devices/GET/v1"
_SENSOR_AGGREGATES_PATH = "/identity-protection/aggregates/devices/GET/v1"


# --- Auth helpers ----------------------------------------------------------


def _base_url(cloud: str) -> str | None:
    return _CLOUD_HOSTS.get((cloud or "").strip().lower())


async def _get_access_token(
    client: httpx.AsyncClient,
    base_url: str,
    client_id: str,
    client_secret: str,
) -> tuple[str | None, str | None]:
    """Exchange client credentials for a Falcon OAuth2 access token.

    Returns ``(access_token, error)`` — exactly one is non-None.
    """
    response = await client.post(
        f"{base_url}/oauth2/token",
        data={"client_id": client_id, "client_secret": client_secret},
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    if response.status_code not in (200, 201):
        return None, f"CrowdStrike auth error ({response.status_code}): {response.text}"
    token = response.json().get("access_token")
    if not token:
        return None, "CrowdStrike auth response did not contain an access_token."
    return token, None


def _bearer_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _parse_pagination(meta: dict[str, Any]) -> Pagination | None:
    pagination = meta.get("pagination")
    if not isinstance(pagination, dict):
        return None
    return Pagination(
        limit=pagination.get("limit"),
        offset=pagination.get("offset"),
        total=pagination.get("total"),
    )


def _parse_sensor(item: dict[str, Any]) -> Sensor:
    """Map an upstream device record into a ``Sensor``.

    Both camelCase and snake_case key spellings are attempted because the
    documented field-name casing for the Identity Protection device
    resource is not fully published; the complete record is always kept
    in ``raw``.
    """

    return Sensor(
        agent_version=_pick(item, "agentVersion", "agent_version"),
        cid=_pick(item, "cid"),
        device_id=_pick(item, "deviceId", "device_id", "id"),
        heartbeat_time=_pick(item, "heartbeatTime", "heartbeat_time", "last_seen"),
        hostname=_pick(item, "hostname"),
        idp_policy_id=_pick(item, "idpPolicyId", "idp_policy_id"),
        idp_policy_name=_pick(item, "idpPolicyName", "idp_policy_name"),
        ip_address=_pick(item, "ipAddress", "ip_address", "local_ip"),
        kerberos_config=_pick(item, "kerberosConfig", "kerberos_config"),
        ldap_config=_pick(item, "ldapConfig", "ldap_config"),
        ldaps_config=_pick(item, "ldapsConfig", "ldaps_config"),
        machine_domain=_pick(item, "machineDomain", "machine_domain"),
        ntlm_config=_pick(item, "ntlmConfig", "ntlm_config"),
        os_version=_pick(item, "osVersion", "os_version"),
        rdp_to_dc_config=_pick(item, "rdpToDcConfig", "rdp_to_dc_config"),
        smb_to_dc_config=_pick(item, "smbToDcConfig", "smb_to_dc_config"),
        status=_pick(item, "status"),
        status_causes=_pick(item, "statusCauses", "status_causes") or [],
        ti_enabled=_pick(item, "tiEnabled", "ti_enabled"),
        raw=item,
    )


def _pick(item: dict[str, Any], *keys: str) -> Any:
    """Return the first present, non-None value among ``keys``.

    Unlike chained ``or``, this does not discard falsy-but-valid values
    such as ``0`` or ``""``.
    """
    for key in keys:
        if key in item and item[key] is not None:
            return item[key]
    return None


def _parse_aggregate(item: dict[str, Any]) -> AggregateResult:
    buckets_raw = item.get("buckets") or []
    buckets = [
        AggregateBucket(
            count=_pick(bucket, "count"),
            from_=_pick(bucket, "from"),
            key=_pick(bucket, "key"),
            key_as_string=_pick(bucket, "keyAsString", "key_as_string"),
            label=_pick(bucket, "label"),
            string_from=_pick(bucket, "stringFrom", "string_from"),
            string_to=_pick(bucket, "stringTo", "string_to"),
            sub_aggregates=_pick(bucket, "subAggregates", "sub_aggregates") or [],
            to=_pick(bucket, "to"),
            value=_pick(bucket, "value"),
            value_as_string=_pick(bucket, "valueAsString", "value_as_string"),
        )
        for bucket in buckets_raw
        if isinstance(bucket, dict)
    ]
    return AggregateResult(
        name=_pick(item, "name"),
        buckets=buckets,
        doc_count_error_upper_bound=_pick(
            item, "docCountErrorUpperBound", "doc_count_error_upper_bound"
        ),
        sum_other_doc_count=_pick(item, "sumOtherDocCount", "sum_other_doc_count"),
    )


# --- Input schemas (args_schema for each @tool) ----------------------------


class QuerySensorsInput(BaseModel):
    client_id: str = Field(description="CrowdStrike Falcon API client ID")
    cloud: str = Field(
        description=(
            "CrowdStrike Falcon cloud region: one of 'us-1', 'us-2', 'eu-1', "
            "'us-gov-1', 'us-gov-2'"
        )
    )
    api_key: str = Field(
        description="CrowdStrike Falcon API client secret (provided by credential system)"
    )
    filter: str | None = Field(
        default=None,
        description="Falcon Query Language (FQL) filter for identity sensor search",
    )
    limit: int | None = Field(
        default=None, description="Maximum number of sensor records to return (1-200)"
    )
    offset: int | None = Field(
        default=None, description="Pagination offset for the identity sensor query"
    )
    sort: str | None = Field(
        default=None, description="Sort expression, e.g. 'status.asc'"
    )


class GetSensorDetailsInput(BaseModel):
    client_id: str = Field(description="CrowdStrike Falcon API client ID")
    cloud: str = Field(
        description=(
            "CrowdStrike Falcon cloud region: one of 'us-1', 'us-2', 'eu-1', "
            "'us-gov-1', 'us-gov-2'"
        )
    )
    api_key: str = Field(
        description="CrowdStrike Falcon API client secret (provided by credential system)"
    )
    ids: list[str] = Field(description="List of CrowdStrike sensor device IDs (max 5000)")


class GetSensorAggregatesInput(BaseModel):
    client_id: str = Field(description="CrowdStrike Falcon API client ID")
    cloud: str = Field(
        description=(
            "CrowdStrike Falcon cloud region: one of 'us-1', 'us-2', 'eu-1', "
            "'us-gov-1', 'us-gov-2'"
        )
    )
    api_key: str = Field(
        description="CrowdStrike Falcon API client secret (provided by credential system)"
    )
    aggregate_query: dict[str, Any] = Field(
        description=(
            "Aggregate query body documented by CrowdStrike (fields such as "
            "field, filter, name, size, sort, type, date_ranges, ranges, "
            "extended_bounds, sub_aggregates)"
        )
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=QuerySensorsInput)
@serialize_pydantic_return
async def query_sensors(
    client_id: str,
    cloud: str,
    api_key: str,
    filter: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    sort: str | None = None,
) -> QuerySensorsOutput:
    """Search CrowdStrike Identity Protection sensors by hostname, IP, or related fields."""
    if not api_key or not api_key.strip():
        return QuerySensorsOutput(
            success=False,
            error="CrowdStrike client secret is empty. Please configure a valid credential.",
        )
    if not client_id or not client_id.strip():
        return QuerySensorsOutput(success=False, error="CrowdStrike client ID is required.")
    base_url = _base_url(cloud)
    if base_url is None:
        return QuerySensorsOutput(
            success=False,
            error=(
                f"Unknown CrowdStrike cloud region '{cloud}'. Expected one of: "
                f"{', '.join(sorted(_CLOUD_HOSTS))}."
            ),
        )

    params: dict[str, Any] = {}
    if filter:
        params["filter"] = filter
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if sort:
        params["sort"] = sort

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, auth_error = await _get_access_token(
                client, base_url, client_id, api_key
            )
            if auth_error is not None:
                return QuerySensorsOutput(success=False, error=auth_error)
            assert token is not None
            response = await client.get(
                f"{base_url}{_QUERY_SENSORS_PATH}",
                headers=_bearer_headers(token),
                params=params,
            )
        if response.status_code != 200:
            return QuerySensorsOutput(
                success=False,
                error=f"CrowdStrike API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return QuerySensorsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return QuerySensorsOutput(success=False, error=f"Query sensors failed: {exc}")

    # The query endpoint returns device IDs in ``resources``. When the
    # upstream returns full records (objects), surface them as sensors too.
    resources = data.get("resources") or []
    device_ids = [r for r in resources if isinstance(r, str)]
    sensors = [_parse_sensor(r) for r in resources if isinstance(r, dict)]
    pagination = _parse_pagination(data.get("meta") or {})
    count = len(resources)

    return QuerySensorsOutput(
        success=True,
        sensors=sensors,
        device_ids=device_ids,
        count=count,
        pagination=pagination,
    )


@tool(args_schema=GetSensorDetailsInput)
@serialize_pydantic_return
async def get_sensor_details(
    client_id: str,
    cloud: str,
    api_key: str,
    ids: list[str],
) -> GetSensorDetailsOutput:
    """Get CrowdStrike Identity Protection sensor details for one or more device IDs."""
    if not api_key or not api_key.strip():
        return GetSensorDetailsOutput(
            success=False,
            error="CrowdStrike client secret is empty. Please configure a valid credential.",
        )
    if not client_id or not client_id.strip():
        return GetSensorDetailsOutput(success=False, error="CrowdStrike client ID is required.")
    if not ids:
        return GetSensorDetailsOutput(success=False, error="No device IDs provided.")
    base_url = _base_url(cloud)
    if base_url is None:
        return GetSensorDetailsOutput(
            success=False,
            error=(
                f"Unknown CrowdStrike cloud region '{cloud}'. Expected one of: "
                f"{', '.join(sorted(_CLOUD_HOSTS))}."
            ),
        )

    body: dict[str, Any] = {"ids": ids}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, auth_error = await _get_access_token(
                client, base_url, client_id, api_key
            )
            if auth_error is not None:
                return GetSensorDetailsOutput(success=False, error=auth_error)
            assert token is not None
            response = await client.post(
                f"{base_url}{_SENSOR_DETAILS_PATH}",
                headers=_bearer_headers(token),
                json=body,
            )
        if response.status_code != 200:
            return GetSensorDetailsOutput(
                success=False,
                error=f"CrowdStrike API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetSensorDetailsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSensorDetailsOutput(success=False, error=f"Get sensor details failed: {exc}")

    resources = data.get("resources") or []
    sensors = [_parse_sensor(r) for r in resources if isinstance(r, dict)]
    pagination = _parse_pagination(data.get("meta") or {})

    return GetSensorDetailsOutput(
        success=True,
        sensors=sensors,
        count=len(sensors),
        pagination=pagination,
    )


@tool(args_schema=GetSensorAggregatesInput)
@serialize_pydantic_return
async def get_sensor_aggregates(
    client_id: str,
    cloud: str,
    api_key: str,
    aggregate_query: dict[str, Any],
) -> GetSensorAggregatesOutput:
    """Get CrowdStrike Identity Protection sensor aggregates from a JSON aggregate query body."""
    if not api_key or not api_key.strip():
        return GetSensorAggregatesOutput(
            success=False,
            error="CrowdStrike client secret is empty. Please configure a valid credential.",
        )
    if not client_id or not client_id.strip():
        return GetSensorAggregatesOutput(
            success=False, error="CrowdStrike client ID is required."
        )
    if not aggregate_query:
        return GetSensorAggregatesOutput(
            success=False, error="An aggregate query body is required."
        )
    base_url = _base_url(cloud)
    if base_url is None:
        return GetSensorAggregatesOutput(
            success=False,
            error=(
                f"Unknown CrowdStrike cloud region '{cloud}'. Expected one of: "
                f"{', '.join(sorted(_CLOUD_HOSTS))}."
            ),
        )

    # The aggregates endpoint accepts a JSON array of aggregate query
    # objects in the request body.
    body: list[dict[str, Any]] = [aggregate_query]

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            token, auth_error = await _get_access_token(
                client, base_url, client_id, api_key
            )
            if auth_error is not None:
                return GetSensorAggregatesOutput(success=False, error=auth_error)
            assert token is not None
            response = await client.post(
                f"{base_url}{_SENSOR_AGGREGATES_PATH}",
                headers=_bearer_headers(token),
                json=body,
            )
        if response.status_code != 200:
            return GetSensorAggregatesOutput(
                success=False,
                error=f"CrowdStrike API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetSensorAggregatesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSensorAggregatesOutput(
            success=False, error=f"Get sensor aggregates failed: {exc}"
        )

    resources = data.get("resources") or []
    aggregates = [_parse_aggregate(r) for r in resources if isinstance(r, dict)]

    return GetSensorAggregatesOutput(
        success=True,
        aggregates=aggregates,
        count=len(aggregates),
    )
