"""Happy-path tests for every google_tag_manager @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.google_tag_manager import (
    TOOLS,
    create_tag,
    get_tag,
    get_tags,
    list_account_id_options,
    manifest,
    update_tag,
    update_variable,
)
from modulex_integrations.tools.google_tag_manager.outputs import (
    CreateTagOutput,
    GetTagOutput,
    GetTagsOutput,
    ListAccountIdOptionsOutput,
    UpdateTagOutput,
    UpdateVariableOutput,
)

API = "https://www.googleapis.com/tagmanager/v2"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_6_actions(self) -> None:
        assert len(manifest.actions) == 6

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_tag(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/accounts/123/containers/456/workspaces/789/tags",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "tagId": "1",
            "name": "My Tag",
            "type": "html",
            "liveOnly": False,
            "parameter": [],
            "fingerprint": "abc",
            "tagManagerUrl": "https://tagmanager.google.com/#/container/accounts/123/containers/456/workspaces/789/tags/1",
            "path": "accounts/123/containers/456/workspaces/789/tags/1",
            "accountId": "123",
            "containerId": "456",
            "workspaceId": "789",
        },
    )

    result_dict = await create_tag.ainvoke(
        _args(
            account_id="123",
            container_id="456",
            workspace_id="789",
            name="My Tag",
            type="html",
            parameter='[{"type": "template", "key": "html", "value": "<script></script>"}]',
        )
    )

    assert isinstance(result_dict, dict)
    result = CreateTagOutput.model_validate(result_dict)
    assert result.success is True
    assert result.tag is not None
    assert result.tag.tag_id == "1"


@pytest.mark.asyncio
async def test_get_tag(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts/123/containers/456/workspaces/789/tags/1",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "tagId": "1",
            "name": "My Tag",
            "type": "html",
            "parameter": [],
            "path": "accounts/123/containers/456/workspaces/789/tags/1",
            "accountId": "123",
            "containerId": "456",
            "workspaceId": "789",
        },
    )

    result_dict = await get_tag.ainvoke(
        _args(
            account_id="123",
            container_id="456",
            workspace_id="789",
            tag_id="1",
        )
    )

    assert isinstance(result_dict, dict)
    result = GetTagOutput.model_validate(result_dict)
    assert result.success is True
    assert result.tag is not None
    assert result.tag.tag_id == "1"


@pytest.mark.asyncio
async def test_get_tags(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts/123/containers/456/workspaces/789/tags",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "tag": [
                {
                    "tagId": "1",
                    "name": "Tag A",
                    "type": "html",
                    "parameter": [],
                    "accountId": "123",
                    "containerId": "456",
                    "workspaceId": "789",
                },
            ],
        },
    )

    result_dict = await get_tags.ainvoke(
        _args(
            account_id="123",
            container_id="456",
            workspace_id="789",
        )
    )

    assert isinstance(result_dict, dict)
    result = GetTagsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.tags) == 1
    assert result.tags[0].tag_id == "1"


@pytest.mark.asyncio
async def test_list_account_id_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "account": [
                {
                    "accountId": "123",
                    "name": "My Account",
                    "shareData": False,
                    "fingerprint": "xyz",
                    "path": "accounts/123",
                    "tagManagerUrl": "https://tagmanager.google.com/#/container/accounts/123",
                },
            ],
        },
    )

    result_dict = await list_account_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListAccountIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.accounts) == 1
    assert result.accounts[0].account_id == "123"


@pytest.mark.asyncio
async def test_update_tag(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/accounts/123/containers/456/workspaces/789/tags/1",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "tagId": "1",
            "name": "Updated Tag",
            "type": "html",
            "parameter": [],
            "path": "accounts/123/containers/456/workspaces/789/tags/1",
            "accountId": "123",
            "containerId": "456",
            "workspaceId": "789",
        },
    )

    result_dict = await update_tag.ainvoke(
        _args(
            account_id="123",
            container_id="456",
            workspace_id="789",
            tag_id="1",
            type="html",
            parameter='[]',
            name="Updated Tag",
        )
    )

    assert isinstance(result_dict, dict)
    result = UpdateTagOutput.model_validate(result_dict)
    assert result.success is True
    assert result.tag is not None
    assert result.tag.name == "Updated Tag"


@pytest.mark.asyncio
async def test_update_variable(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/accounts/123/containers/456/workspaces/789/variables/10",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "variableId": "10",
            "name": "My Variable",
            "type": "jsm",
            "parameter": [],
            "path": "accounts/123/containers/456/workspaces/789/variables/10",
            "accountId": "123",
            "containerId": "456",
            "workspaceId": "789",
        },
    )

    result_dict = await update_variable.ainvoke(
        _args(
            account_id="123",
            container_id="456",
            workspace_id="789",
            variable_id="10",
            name="My Variable",
            type="jsm",
            parameter='[{"type": "template", "key": "javascript", "value": "function(){return 1;}"}]',
        )
    )

    assert isinstance(result_dict, dict)
    result = UpdateVariableOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data is not None
