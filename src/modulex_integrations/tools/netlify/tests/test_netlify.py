"""Happy-path tests for every netlify @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.netlify import (
    TOOLS,
    get_site,
    list_files,
    list_site_deploys,
    manifest,
    rollback_deploy,
)
from modulex_integrations.tools.netlify.outputs import (
    GetSiteOutput,
    ListFilesOutput,
    ListSiteDeploysOutput,
    RollbackDeployOutput,
)

API = "https://api.netlify.com/api/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity ----------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_4_actions(self) -> None:
        assert len(manifest.actions) == 4

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests ----------------------------------------------


@pytest.mark.asyncio
async def test_get_site(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sites/test-site-id",
        json={
            # TODO: fill in a representative response shape from the Netlify API docs
            "id": "test-site-id",
            "name": "my-site",
            "url": "https://my-site.netlify.app",
            "ssl_url": "https://my-site.netlify.app",
            "admin_url": "https://app.netlify.com/sites/my-site",
            "state": "ready",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-06-01T00:00:00Z",
            "default_domain": "my-site.netlify.app",
            "custom_domain": None,
        },
    )

    result_dict = await get_site.ainvoke(_args(site_id="test-site-id"))

    assert isinstance(result_dict, dict)
    result = GetSiteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "my-site"
    assert result.id == "test-site-id"


@pytest.mark.asyncio
async def test_list_files(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sites/test-site-id/files",
        json=[
            # TODO: fill in a representative response shape from the Netlify API docs
            {"id": "/index.html", "path": "/index.html", "size": 1234},
            {"id": "/style.css", "path": "/style.css", "size": 567},
        ],
    )

    result_dict = await list_files.ainvoke(_args(site_id="test-site-id"))

    assert isinstance(result_dict, dict)
    result = ListFilesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.files) == 2


@pytest.mark.asyncio
async def test_list_site_deploys(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sites/test-site-id/deploys?page=1&per_page=100",
        json=[
            # TODO: fill in a representative response shape from the Netlify API docs
            {"id": "deploy-1", "state": "ready", "created_at": "2023-06-01T00:00:00Z"},
            {"id": "deploy-2", "state": "ready", "created_at": "2023-05-01T00:00:00Z"},
        ],
    )

    result_dict = await list_site_deploys.ainvoke(_args(site_id="test-site-id"))

    assert isinstance(result_dict, dict)
    result = ListSiteDeploysOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.deploys) == 2


@pytest.mark.asyncio
async def test_rollback_deploy(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sites/test-site-id/deploys/deploy-1/restore",
        json={
            # TODO: fill in a representative response shape from the Netlify API docs
            "id": "deploy-1",
            "state": "ready",
            "name": "my-site",
            "url": "https://my-site.netlify.app",
            "ssl_url": "https://my-site.netlify.app",
            "created_at": "2023-06-01T00:00:00Z",
            "updated_at": "2023-06-01T12:00:00Z",
        },
    )

    result_dict = await rollback_deploy.ainvoke(
        _args(site_id="test-site-id", deploy_id="deploy-1")
    )

    assert isinstance(result_dict, dict)
    result = RollbackDeployOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "deploy-1"
    assert result.state == "ready"


# --- Failure-path tests --------------------------------------------------------


@pytest.mark.asyncio
async def test_get_site_empty_credentials() -> None:
    """Verify that empty credentials return a structured error, not a network call."""
    result_dict = await get_site.ainvoke(
        _args(auth_data={}, site_id="test-site-id")
    )
    assert isinstance(result_dict, dict)
    result = GetSiteOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error.lower()
