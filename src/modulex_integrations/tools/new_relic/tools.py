"""New Relic LangChain ``@tool`` functions.

Four async tools wrapping the New Relic NerdGraph GraphQL API. The
calling convention is the modulex ``api_key`` injection: the runtime
passes ``api_key: str`` directly (resolved from the user's API key
credential), not an ``auth_type``/``auth_data`` pair.

Error model: every call is wrapped in try/except. A non-2xx HTTP
status, a GraphQL ``errors`` array, a timeout, or an unexpected
exception is returned as the typed output with ``success=False`` +
``error`` rather than raising.
"""
from __future__ import annotations

import json
import re
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.new_relic.outputs import (
    ChangeTrackingEntity,
    ChangeTrackingEvent,
    CreateDeploymentEventOutput,
    Entity,
    GetEntityOutput,
    NrqlQueryOutput,
    SearchEntitiesOutput,
)

__all__ = [
    "create_deployment_event",
    "get_entity",
    "nrql_query",
    "search_entities",
]

_US_ENDPOINT = "https://api.newrelic.com/graphql"
_EU_ENDPOINT = "https://api.eu.newrelic.com/graphql"
_TIMEOUT = 90.0

_DEPLOYMENT_TYPES = ("basic", "blue green", "canary", "rolling", "shadow")
_CUSTOM_ATTRIBUTE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_RESTRICTED_CUSTOM_ATTRIBUTE_NAMES = frozenset(
    {
        "accountId",
        "ago",
        "and",
        "appID",
        "as",
        "auto",
        "begin",
        "begintime",
        "category",
        "categoryType",
        "changeTrackingId",
        "compare",
        "customAttributes",
        "customType",
        "day",
        "days",
        "description",
        "end",
        "endtime",
        "explain",
        "entityGuid",
        "entityName",
        "eventType",
        "facet",
        "from",
        "groupId",
        "hostname",
        "hour",
        "hours",
        "in",
        "is",
        "like",
        "limit",
        "log",
        "minute",
        "minutes",
        "month",
        "months",
        "not",
        "null",
        "offset",
        "or",
        "raw",
        "second",
        "seconds",
        "select",
        "since",
        "timeseries",
        "timestamp",
        "type",
        "until",
        "user",
        "week",
        "weeks",
        "where",
        "with",
    }
)


# --- Helpers ----------------------------------------------------------------


def _endpoint(region: str | None) -> str:
    return _EU_ENDPOINT if (region or "us").lower() == "eu" else _US_ENDPOINT


def _headers(api_key: str) -> dict[str, str]:
    return {"API-Key": api_key, "Content-Type": "application/json"}


def _gql_string(value: str) -> str:
    """Serialize a Python string as a GraphQL string literal (JSON-quoted)."""
    return json.dumps(value)


def _gql_literal(value: str | int | float | bool) -> str:
    if isinstance(value, str):
        return _gql_string(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _graphql_errors(payload: dict[str, Any]) -> str | None:
    """Join any GraphQL ``errors[].message`` into a single string, else None."""
    errors = payload.get("errors") or []
    messages = [
        str(e["message"]) for e in errors if isinstance(e, dict) and e.get("message")
    ]
    return "; ".join(messages) if messages else None


# --- Input schemas (args_schema for each @tool) ----------------------------


class NrqlQueryInput(BaseModel):
    account_id: int = Field(description="New Relic account ID to query")
    nrql: str = Field(description="NRQL query to execute")
    api_key: str = Field(description="New Relic user API key (provided by credential system)")
    region: str = Field(default="us", description="New Relic data center region: 'us' or 'eu'")
    timeout: int | None = Field(default=None, description="Optional query timeout in seconds")


class SearchEntitiesInput(BaseModel):
    query: str = Field(
        description=(
            'Entity search query, e.g. name like "api" or domainType = "APM-APPLICATION"'
        )
    )
    api_key: str = Field(description="New Relic user API key (provided by credential system)")
    region: str = Field(default="us", description="New Relic data center region: 'us' or 'eu'")
    cursor: str | None = Field(
        default=None, description="Pagination cursor from a previous entity search"
    )


class GetEntityInput(BaseModel):
    guid: str = Field(description="Entity GUID")
    api_key: str = Field(description="New Relic user API key (provided by credential system)")
    region: str = Field(default="us", description="New Relic data center region: 'us' or 'eu'")


class CreateDeploymentEventInput(BaseModel):
    entity_guid: str = Field(description="GUID of the entity associated with the deployment")
    version: str = Field(description="Deployment version, release name, or commit SHA")
    api_key: str = Field(description="New Relic user API key (provided by credential system)")
    region: str = Field(default="us", description="New Relic data center region: 'us' or 'eu'")
    short_description: str | None = Field(
        default=None, description="Short description of the deployment"
    )
    description: str | None = Field(default=None, description="Longer deployment description")
    changelog: str | None = Field(default=None, description="Deployment changelog text or URL")
    commit: str | None = Field(
        default=None, description="Commit SHA or identifier associated with the deployment"
    )
    deep_link: str | None = Field(
        default=None, description="URL to the deployment, build, or release details"
    )
    user: str | None = Field(
        default=None, description="User or automation that performed the deployment"
    )
    group_id: str | None = Field(
        default=None, description="Optional group ID to correlate related changes"
    )
    custom_attributes: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Custom change event metadata as key-value pairs with string, number, "
            "or boolean values"
        ),
    )
    deployment_type: str = Field(
        default="basic",
        description="Deployment type: 'basic', 'blue green', 'canary', 'rolling', or 'shadow'",
    )
    timestamp: int | None = Field(
        default=None, description="Event timestamp in milliseconds since Unix epoch"
    )


# --- Deployment mutation builder -------------------------------------------


def _normalize_deployment_type(value: str | None) -> str:
    normalized = (value or "basic").lower().replace("_", " ").replace("-", " ")
    return normalized if normalized in _DEPLOYMENT_TYPES else "basic"


def _build_custom_attributes(custom_attributes: dict[str, Any] | None) -> str | None:
    """Render validated custom attributes as a GraphQL object fragment, or None."""
    if not custom_attributes:
        return None
    entries = list(custom_attributes.items())
    if not entries:
        return None

    for key, value in entries:
        if not _CUSTOM_ATTRIBUTE_NAME_PATTERN.match(key):
            raise ValueError(
                f'Invalid New Relic custom attribute name "{key}". Use letters, numbers, '
                "and underscores, and do not start with a number."
            )
        if key in _RESTRICTED_CUSTOM_ATTRIBUTE_NAMES or "." in key:
            raise ValueError(f'New Relic custom attribute name "{key}" is restricted')
        if not isinstance(value, (str, int, float, bool)):
            raise ValueError(
                f'Invalid value for New Relic custom attribute "{key}". Use a string, '
                "number, or boolean."
            )
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            raise ValueError(f'Invalid numeric value for New Relic custom attribute "{key}"')

    fields = ", ".join(f"{key}: {_gql_literal(value)}" for key, value in entries)
    return f"customAttributes: {{ {fields} }}"


def _clean_optional(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _build_deployment_mutation(
    entity_guid: str,
    version: str,
    short_description: str | None,
    description: str | None,
    changelog: str | None,
    commit: str | None,
    deep_link: str | None,
    user: str | None,
    group_id: str | None,
    custom_attributes: dict[str, Any] | None,
    deployment_type: str,
    timestamp: int | None,
) -> str:
    resolved_type = _normalize_deployment_type(deployment_type)
    guid = entity_guid.strip()
    if not guid or "'" in guid:
        raise ValueError("Invalid entity GUID: value must not be empty or contain single quotes")
    clean_version = version.strip()

    def _string_field(name: str, value: str | None) -> str | None:
        cleaned = _clean_optional(value)
        return f"{name}: {_gql_string(cleaned)}" if cleaned else None

    deployment_parts = [
        f"version: {_gql_string(clean_version)}",
        _string_field("changelog", changelog),
        _string_field("commit", commit),
        _string_field("deepLink", deep_link),
    ]
    deployment_fields = ", ".join(p for p in deployment_parts if p)

    optional_parts = [
        _string_field("shortDescription", short_description),
        _string_field("description", description),
        _string_field("user", user),
        _string_field("groupId", group_id),
        _build_custom_attributes(custom_attributes),
        f"timestamp: {int(timestamp)}" if timestamp else None,
    ]
    optional_fields = "\n          ".join(p for p in optional_parts if p)

    return f"""mutation {{
  changeTrackingCreateEvent(
    changeTrackingEvent: {{
      categoryAndTypeData: {{
        categoryFields: {{ deployment: {{ {deployment_fields} }} }}
        kind: {{ category: "deployment", type: {_gql_string(resolved_type)} }}
      }}
      entitySearch: {{ query: {_gql_string(f"id = '{guid}'")} }}
      {optional_fields}
    }}
  ) {{
    changeTrackingEvent {{
      category
      categoryAndType
      changeTrackingId
      customAttributes
      description
      entity {{
        guid
        name
      }}
      groupId
      shortDescription
      timestamp
      type
      user
    }}
    messages
  }}
}}"""


# --- @tool functions -------------------------------------------------------


@tool(args_schema=NrqlQueryInput)
@serialize_pydantic_return
async def nrql_query(
    account_id: int,
    nrql: str,
    api_key: str,
    region: str = "us",
    timeout: int | None = None,
) -> NrqlQueryOutput:
    """Run a NRQL query against a New Relic account using NerdGraph."""
    if not api_key or not api_key.strip():
        return NrqlQueryOutput(
            success=False,
            error="New Relic API key is empty. Please configure a valid New Relic credential.",
        )

    timeout_clause = f", timeout: {int(timeout)}" if timeout else ""
    query = (
        "{\n  actor {\n    account(id: "
        f"{int(account_id)}"
        ") {\n      nrql(query: "
        f"{_gql_string(nrql)}{timeout_clause}"
        ") {\n        results\n      }\n    }\n  }\n}"
    )
    body: dict[str, Any] = {"query": query}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(_endpoint(region), headers=_headers(api_key), json=body)
        if response.status_code != 200:
            return NrqlQueryOutput(
                success=False,
                error=f"New Relic API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return NrqlQueryOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return NrqlQueryOutput(success=False, error=f"NRQL query failed: {exc}")

    gql_error = _graphql_errors(data)
    if gql_error:
        return NrqlQueryOutput(success=False, error=gql_error)

    nrql_node = (
        ((data.get("data") or {}).get("actor") or {}).get("account") or {}
    ).get("nrql")
    if not nrql_node:
        return NrqlQueryOutput(
            success=False,
            error="New Relic did not return NRQL data for the requested account.",
        )
    results = nrql_node.get("results") or []
    return NrqlQueryOutput(success=True, results=results, result_count=len(results))


@tool(args_schema=SearchEntitiesInput)
@serialize_pydantic_return
async def search_entities(
    query: str,
    api_key: str,
    region: str = "us",
    cursor: str | None = None,
) -> SearchEntitiesOutput:
    """Search New Relic entities by name, GUID, domain type, tags, or reporting state."""
    if not api_key or not api_key.strip():
        return SearchEntitiesOutput(
            success=False,
            error="New Relic API key is empty. Please configure a valid New Relic credential.",
        )

    gql = (
        "query($query: String!, $cursor: String) {\n"
        "  actor {\n"
        "    entitySearch(query: $query) {\n"
        "      count\n"
        "      query\n"
        "      results(cursor: $cursor) {\n"
        "        nextCursor\n"
        "        entities {\n"
        "          guid\n"
        "          name\n"
        "          entityType\n"
        "        }\n"
        "      }\n"
        "    }\n"
        "  }\n"
        "}"
    )
    body: dict[str, Any] = {
        "query": gql,
        "variables": {"query": query, "cursor": cursor or None},
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(_endpoint(region), headers=_headers(api_key), json=body)
        if response.status_code != 200:
            return SearchEntitiesOutput(
                success=False,
                error=f"New Relic API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchEntitiesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchEntitiesOutput(success=False, error=f"Entity search failed: {exc}")

    gql_error = _graphql_errors(data)
    if gql_error:
        return SearchEntitiesOutput(success=False, error=gql_error)

    entity_search = ((data.get("data") or {}).get("actor") or {}).get("entitySearch")
    if not entity_search:
        return SearchEntitiesOutput(
            success=False, error="New Relic did not return entity search data."
        )
    results_node = entity_search.get("results") or {}
    raw_entities = results_node.get("entities") or []
    entities = [
        Entity(
            guid=item.get("guid"),
            name=item.get("name"),
            entity_type=item.get("entityType"),
        )
        for item in raw_entities
    ]
    raw_count = entity_search.get("count")
    return SearchEntitiesOutput(
        success=True,
        count=raw_count if raw_count is not None else len(entities),
        query=entity_search.get("query") or "",
        entities=entities,
        next_cursor=results_node.get("nextCursor"),
    )


@tool(args_schema=GetEntityInput)
@serialize_pydantic_return
async def get_entity(
    guid: str,
    api_key: str,
    region: str = "us",
) -> GetEntityOutput:
    """Fetch a New Relic entity by GUID."""
    if not api_key or not api_key.strip():
        return GetEntityOutput(
            success=False,
            error="New Relic API key is empty. Please configure a valid New Relic credential.",
        )

    gql = (
        "{\n  actor {\n    entity(guid: "
        f"{_gql_string(guid.strip())}"
        ") {\n      name\n      entityType\n    }\n  }\n}"
    )
    body: dict[str, Any] = {"query": gql}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(_endpoint(region), headers=_headers(api_key), json=body)
        if response.status_code != 200:
            return GetEntityOutput(
                success=False,
                error=f"New Relic API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetEntityOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetEntityOutput(success=False, error=f"Get entity failed: {exc}")

    gql_error = _graphql_errors(data)
    if gql_error:
        return GetEntityOutput(success=False, error=gql_error)

    entity_node = ((data.get("data") or {}).get("actor") or {}).get("entity")
    entity = (
        Entity(
            guid=guid,
            name=entity_node.get("name"),
            entity_type=entity_node.get("entityType"),
        )
        if entity_node
        else None
    )
    return GetEntityOutput(success=True, entity=entity)


@tool(args_schema=CreateDeploymentEventInput)
@serialize_pydantic_return
async def create_deployment_event(
    entity_guid: str,
    version: str,
    api_key: str,
    region: str = "us",
    short_description: str | None = None,
    description: str | None = None,
    changelog: str | None = None,
    commit: str | None = None,
    deep_link: str | None = None,
    user: str | None = None,
    group_id: str | None = None,
    custom_attributes: dict[str, Any] | None = None,
    deployment_type: str = "basic",
    timestamp: int | None = None,
) -> CreateDeploymentEventOutput:
    """Record a deployment change event in New Relic change tracking."""
    if not api_key or not api_key.strip():
        return CreateDeploymentEventOutput(
            success=False,
            error="New Relic API key is empty. Please configure a valid New Relic credential.",
        )

    try:
        mutation = _build_deployment_mutation(
            entity_guid=entity_guid,
            version=version,
            short_description=short_description,
            description=description,
            changelog=changelog,
            commit=commit,
            deep_link=deep_link,
            user=user,
            group_id=group_id,
            custom_attributes=custom_attributes,
            deployment_type=deployment_type,
            timestamp=timestamp,
        )
    except ValueError as exc:
        return CreateDeploymentEventOutput(success=False, error=str(exc))

    body: dict[str, Any] = {"query": mutation}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(_endpoint(region), headers=_headers(api_key), json=body)
        if response.status_code != 200:
            return CreateDeploymentEventOutput(
                success=False,
                error=f"New Relic API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateDeploymentEventOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDeploymentEventOutput(
            success=False, error=f"Create deployment event failed: {exc}"
        )

    gql_error = _graphql_errors(data)
    if gql_error:
        return CreateDeploymentEventOutput(success=False, error=gql_error)

    result = (data.get("data") or {}).get("changeTrackingCreateEvent")
    if not result:
        return CreateDeploymentEventOutput(
            success=False,
            error="New Relic did not return a deployment change tracking result.",
        )

    raw_event = result.get("changeTrackingEvent")
    messages = result.get("messages") or []
    if not raw_event:
        return CreateDeploymentEventOutput(
            success=False,
            error="; ".join(messages)
            if messages
            else "New Relic did not create a deployment change tracking event.",
            messages=messages,
        )

    raw_entity = raw_event.get("entity")
    event = ChangeTrackingEvent(
        category=raw_event.get("category"),
        category_and_type=raw_event.get("categoryAndType"),
        change_tracking_id=raw_event.get("changeTrackingId"),
        custom_attributes=raw_event.get("customAttributes"),
        description=raw_event.get("description"),
        group_id=raw_event.get("groupId"),
        short_description=raw_event.get("shortDescription"),
        timestamp=raw_event.get("timestamp"),
        type=raw_event.get("type"),
        user=raw_event.get("user"),
        entity=(
            ChangeTrackingEntity(guid=raw_entity.get("guid"), name=raw_entity.get("name"))
            if raw_entity
            else None
        ),
    )
    return CreateDeploymentEventOutput(success=True, event=event, messages=messages)
