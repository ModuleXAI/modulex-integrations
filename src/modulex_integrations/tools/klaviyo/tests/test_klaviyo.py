"""Tests for the Klaviyo integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.klaviyo import (
    TOOLS,
    add_members_to_list,
    create_list,
    get_list,
    get_lists,
    get_profiles,
    manifest,
)
from modulex_integrations.tools.klaviyo.outputs import (
    AddMembersToListOutput,
    CreateListOutput,
    GetListOutput,
    GetListsOutput,
    GetProfilesOutput,
)

API = "https://a.klaviyo.com/api"
_API_KEY = "klaviyo-fake-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


class TestManifest:
    def test_manifest_exposes_five_actions(self) -> None:
        assert len(manifest.actions) == 5

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert [a.auth_type for a in manifest.auth_schemas] == ["api_key"]


@pytest.mark.asyncio
async def test_get_lists_returns_collected_lists(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/lists?sort=-created",
        json={
            "data": [
                {
                    "id": "L1",
                    "attributes": {
                        "name": "Newsletter",
                        "created": "2026-01-01T00:00:00Z",
                        "updated": "2026-02-01T00:00:00Z",
                        "opt_in_process": "double_opt_in",
                    },
                },
                {
                    "id": "L2",
                    "attributes": {
                        "name": "Promotions",
                        "created": "2026-03-01T00:00:00Z",
                        "updated": "2026-03-02T00:00:00Z",
                        "opt_in_process": "single_opt_in",
                    },
                },
            ],
            "links": {"next": None},
        },
    )

    result_dict = await get_lists.ainvoke(_args(max_results=10))
    assert isinstance(result_dict, dict)
    result = GetListsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 2
    assert result.lists[0].name == "Newsletter"
    assert result.lists[1].id == "L2"


@pytest.mark.asyncio
async def test_get_lists_handles_api_error(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/lists?sort=-created",
        status_code=401,
        text="unauthorized",
    )
    result_dict = await get_lists.ainvoke(_args())
    result = GetListsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "401" in result.error


@pytest.mark.asyncio
async def test_get_list_success(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/lists/L1",
        json={
            "data": {
                "id": "L1",
                "attributes": {
                    "name": "Newsletter",
                    "created": "2026-01-01T00:00:00Z",
                    "updated": "2026-02-01T00:00:00Z",
                    "opt_in_process": "double_opt_in",
                },
            }
        },
    )

    result_dict = await get_list.ainvoke(_args(list_id="L1"))
    result = GetListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "Newsletter"
    assert result.opt_in_process == "double_opt_in"


@pytest.mark.asyncio
async def test_get_list_not_found(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/lists/missing", status_code=404, text="not found"
    )
    result_dict = await get_list.ainvoke(_args(list_id="missing"))
    result = GetListOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "missing" in result.error


@pytest.mark.asyncio
async def test_create_list(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/lists",
        status_code=201,
        json={
            "data": {
                "id": "L99",
                "attributes": {
                    "name": "VIP",
                    "created": "2026-05-16T12:00:00Z",
                    "updated": "2026-05-16T12:00:00Z",
                    "opt_in_process": "single_opt_in",
                },
            }
        },
    )

    result_dict = await create_list.ainvoke(_args(name="VIP"))
    result = CreateListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "L99"
    assert result.name == "VIP"


@pytest.mark.asyncio
async def test_get_profiles(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/profiles?sort=-created",
        json={
            "data": [
                {
                    "id": "P1",
                    "attributes": {
                        "email": "a@example.com",
                        "first_name": "Ada",
                        "last_name": "Lovelace",
                        "phone_number": "+10000000000",
                        "created": "2026-01-01T00:00:00Z",
                        "updated": "2026-02-01T00:00:00Z",
                    },
                }
            ],
            "links": {"next": None},
        },
    )

    result_dict = await get_profiles.ainvoke(_args(max_results=5))
    result = GetProfilesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.count == 1
    assert result.profiles[0].email == "a@example.com"


@pytest.mark.asyncio
async def test_add_members_to_list_success(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/lists/L1/relationships/profiles",
        status_code=204,
    )

    result_dict = await add_members_to_list.ainvoke(
        _args(list_id="L1", profile_ids=["P1", "P2"])
    )
    result = AddMembersToListOutput.model_validate(result_dict)
    assert result.success is True
    assert result.list_id == "L1"
    assert result.profiles_added == 2
    assert result.profile_ids == ["P1", "P2"]


@pytest.mark.asyncio
async def test_add_members_to_list_not_found(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/lists/missing/relationships/profiles",
        status_code=404,
        text="not found",
    )
    result_dict = await add_members_to_list.ainvoke(
        _args(list_id="missing", profile_ids=["P1"])
    )
    result = AddMembersToListOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "missing" in result.error


@pytest.mark.asyncio
async def test_empty_key_short_circuits() -> None:
    result_dict = await get_lists.ainvoke({"api_key": ""})
    result = GetListsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None and "Klaviyo API key" in result.error
