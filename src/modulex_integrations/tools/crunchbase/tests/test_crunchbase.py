"""Happy-path tests for every crunchbase @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.crunchbase import (
    TOOLS,
    get_organization,
    manifest,
    search_organizations,
)
from modulex_integrations.tools.crunchbase.outputs import (
    GetOrganizationOutput,
    SearchOrganizationsOutput,
)

API = "https://api.crunchbase.com/v4/data"

_API_KEY = "fake-user-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(user_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_2_actions(self) -> None:
        assert len(manifest.actions) == 2

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_get_organization(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/entities/organizations/crunchbase",
        json={
            # TODO: fill in a representative response shape from the Crunchbase API docs
            "properties": {"name": "Crunchbase", "short_description": "Business data platform"},
            "cards": {},
        },
    )

    result_dict = await get_organization.ainvoke(_args(entity_id="crunchbase"))

    assert isinstance(result_dict, dict)
    result = GetOrganizationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-cb-user-key"] == _API_KEY


@pytest.mark.asyncio
async def test_search_organizations(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/searches/organizations",
        json={
            # TODO: fill in a representative response shape from the Crunchbase API docs
            "entities": [
                {"properties": {"name": "Acme Corp", "short_description": "A company"}},
            ],
            "count": 1,
        },
    )

    result_dict = await search_organizations.ainvoke(
        _args(field_ids=["name", "short_description"])
    )

    assert isinstance(result_dict, dict)
    result = SearchOrganizationsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.entities) == 1
    assert result.total_count == 1

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["x-cb-user-key"] == _API_KEY


@pytest.mark.asyncio
async def test_get_organization_validates_empty_key() -> None:
    result_dict = await get_organization.ainvoke({"entity_id": "x", "user_key": ""})
    result = GetOrganizationOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")


@pytest.mark.asyncio
async def test_search_organizations_validates_empty_key() -> None:
    result_dict = await search_organizations.ainvoke({"field_ids": ["name"], "user_key": ""})
    result = SearchOrganizationsOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")
