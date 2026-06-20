"""Happy-path tests per action + failure-path and empty-credential tests.

New Relic POSTs to NerdGraph; non-2xx status, a GraphQL ``errors`` array,
and timeouts surface as ``success=False`` + ``error`` rather than raising.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.new_relic import (
    TOOLS,
    create_deployment_event,
    get_entity,
    manifest,
    nrql_query,
    search_entities,
)
from modulex_integrations.tools.new_relic.outputs import (
    CreateDeploymentEventOutput,
    GetEntityOutput,
    NrqlQueryOutput,
    SearchEntitiesOutput,
)

US = "https://api.newrelic.com/graphql"
EU = "https://api.eu.newrelic.com/graphql"
_API_KEY = "NRAK-fake-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo_is_themed(self) -> None:
        assert manifest.logo == "modulex:new_relic-themed"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_nrql_query(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=US,
        json={
            "data": {
                "actor": {
                    "account": {
                        "nrql": {"results": [{"count": 42}, {"count": 7}]}
                    }
                }
            }
        },
    )

    result_dict = await nrql_query.ainvoke(
        _args(account_id=1234567, nrql="SELECT count(*) FROM Transaction")
    )

    assert isinstance(result_dict, dict)
    result = NrqlQueryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.result_count == 2
    assert result.results[0]["count"] == 42

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["API-Key"] == _API_KEY


@pytest.mark.asyncio
async def test_nrql_query_eu_region(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=EU,
        json={"data": {"actor": {"account": {"nrql": {"results": []}}}}},
    )

    result_dict = await nrql_query.ainvoke(
        _args(account_id=1, nrql="SELECT 1", region="eu", timeout=30)
    )

    assert isinstance(result_dict, dict)
    result = NrqlQueryOutput.model_validate(result_dict)
    assert result.success is True
    assert result.result_count == 0
    assert str(httpx_mock.get_requests()[0].url) == EU


@pytest.mark.asyncio
async def test_search_entities(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=US,
        json={
            "data": {
                "actor": {
                    "entitySearch": {
                        "count": 1,
                        "query": "name like 'api'",
                        "results": {
                            "nextCursor": "cursor-2",
                            "entities": [
                                {
                                    "guid": "MXxBUE18QVBQTElDQVRJT058MQ",
                                    "name": "api-gateway",
                                    "entityType": "APM_APPLICATION_ENTITY",
                                }
                            ],
                        },
                    }
                }
            }
        },
    )

    result_dict = await search_entities.ainvoke(_args(query='name like "api"'))

    assert isinstance(result_dict, dict)
    result = SearchEntitiesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.entities[0].name == "api-gateway"
    assert result.entities[0].entity_type == "APM_APPLICATION_ENTITY"
    assert result.next_cursor == "cursor-2"


@pytest.mark.asyncio
async def test_get_entity(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=US,
        json={
            "data": {
                "actor": {
                    "entity": {
                        "name": "checkout-service",
                        "entityType": "APM_APPLICATION_ENTITY",
                    }
                }
            }
        },
    )

    result_dict = await get_entity.ainvoke(_args(guid="MXxBUE18QVBQTElDQVRJT058MQ"))

    assert isinstance(result_dict, dict)
    result = GetEntityOutput.model_validate(result_dict)
    assert result.success is True
    assert result.entity is not None
    assert result.entity.guid == "MXxBUE18QVBQTElDQVRJT058MQ"
    assert result.entity.name == "checkout-service"


@pytest.mark.asyncio
async def test_get_entity_not_found_returns_null_entity(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=US,
        json={"data": {"actor": {"entity": None}}},
    )

    result_dict = await get_entity.ainvoke(_args(guid="missing"))

    assert isinstance(result_dict, dict)
    result = GetEntityOutput.model_validate(result_dict)
    assert result.success is True
    assert result.entity is None


@pytest.mark.asyncio
async def test_create_deployment_event(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=US,
        json={
            "data": {
                "changeTrackingCreateEvent": {
                    "changeTrackingEvent": {
                        "category": "deployment",
                        "categoryAndType": "deployment-basic",
                        "changeTrackingId": "evt-001",
                        "customAttributes": {"isProduction": True},
                        "description": "Deploy 1.2.3",
                        "entity": {
                            "guid": "MXxBUE18QVBQTElDQVRJT058MQ",
                            "name": "checkout-service",
                        },
                        "groupId": "release-1",
                        "shortDescription": "Deploy version 1.2.3",
                        "timestamp": 1767225600000,
                        "type": "basic",
                        "user": "deploy-bot@example.com",
                    },
                    "messages": [],
                }
            }
        },
    )

    result_dict = await create_deployment_event.ainvoke(
        _args(
            entity_guid="MXxBUE18QVBQTElDQVRJT058MQ",
            version="1.2.3",
            short_description="Deploy version 1.2.3",
            custom_attributes={"isProduction": True},
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateDeploymentEventOutput.model_validate(result_dict)
    assert result.success is True
    assert result.event is not None
    assert result.event.change_tracking_id == "evt-001"
    assert result.event.entity is not None
    assert result.event.entity.name == "checkout-service"


# --- Failure paths ---------------------------------------------------------


@pytest.mark.asyncio
async def test_nrql_query_graphql_errors(httpx_mock):  # type: ignore[no-untyped-def]
    """A populated GraphQL ``errors`` array surfaces as success=False."""
    httpx_mock.add_response(
        method="POST",
        url=US,
        json={"errors": [{"message": "Invalid NRQL syntax"}]},
    )

    result_dict = await nrql_query.ainvoke(_args(account_id=1, nrql="BAD QUERY"))

    assert isinstance(result_dict, dict)
    result = NrqlQueryOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Invalid NRQL syntax" in result.error


@pytest.mark.asyncio
async def test_get_entity_returns_error_on_non_2xx(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=US,
        status_code=401,
        text="Invalid API key",
    )

    result_dict = await get_entity.ainvoke(_args(guid="anything"))

    assert isinstance(result_dict, dict)
    result = GetEntityOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "401" in result.error


@pytest.mark.asyncio
async def test_create_deployment_event_rejects_restricted_attribute() -> None:
    """A restricted custom-attribute name is rejected before the HTTP call."""
    result_dict = await create_deployment_event.ainvoke(
        _args(
            entity_guid="guid-1",
            version="1.0.0",
            custom_attributes={"timestamp": 1},
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateDeploymentEventOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "restricted" in result.error


# --- Empty credential ------------------------------------------------------


@pytest.mark.asyncio
async def test_nrql_query_validates_empty_api_key() -> None:
    """Empty / whitespace-only api_key short-circuits before the HTTP call."""
    result_dict = await nrql_query.ainvoke(
        {"account_id": 1, "nrql": "SELECT 1", "api_key": ""}
    )

    assert isinstance(result_dict, dict)
    result = NrqlQueryOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key" in result.error
