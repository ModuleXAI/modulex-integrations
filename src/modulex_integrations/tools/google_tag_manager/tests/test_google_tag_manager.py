"""Happy-path tests for every google_tag_manager @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.schema import OAuth2AuthSchema
from modulex_integrations.tools.google_tag_manager import (
    TOOLS,
    get_tag,
    get_tags,
    list_account_id_options,
    manifest,
)
from modulex_integrations.tools.google_tag_manager.outputs import (
    GetTagOutput,
    GetTagsOutput,
    ListAccountIdOptionsOutput,
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
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}

    def test_manifest_requests_only_the_readonly_scope(self) -> None:
        oauth_schemas = [
            s for s in manifest.auth_schemas if isinstance(s, OAuth2AuthSchema)
        ]
        assert oauth_schemas
        for schema in oauth_schemas:
            assert schema.oauth_config.scopes == [
                "https://www.googleapis.com/auth/tagmanager.readonly",
            ]


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_get_tag(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/accounts/123/containers/456/workspaces/789/tags/1",
        json={
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
