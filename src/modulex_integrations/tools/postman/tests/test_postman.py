"""Happy-path tests for every postman @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.postman import (
    TOOLS,
    create_environment,
    list_workspace_id_options,
    manifest,
    run_monitor,
    update_variable,
)
from modulex_integrations.tools.postman.outputs import (
    CreateEnvironmentOutput,
    ListWorkspaceIdOptionsOutput,
    RunMonitorOutput,
    UpdateVariableOutput,
)

API = "https://api.getpostman.com"

_API_KEY = "fake-postman-api-key"


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


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_environment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/environments",
        json={
            # TODO: fill in a representative response shape from Postman API docs
            "environment": {"id": "env-123", "name": "staging"},
        },
    )

    result_dict = await create_environment.ainvoke(
        _args(environment_name="staging")
    )

    assert isinstance(result_dict, dict)
    result = CreateEnvironmentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.environment_id == "env-123"


@pytest.mark.asyncio
async def test_list_workspace_id_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/workspaces",
        json={
            # TODO: fill in a representative response shape from Postman API docs
            "workspaces": [
                {"id": "ws-1", "name": "My Workspace", "type": "personal"},
            ],
        },
    )

    result_dict = await list_workspace_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListWorkspaceIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.workspaces) == 1
    assert result.workspaces[0].id == "ws-1"


@pytest.mark.asyncio
async def test_run_monitor(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/monitors/mon-123/run",
        json={
            # TODO: fill in a representative response shape from Postman API docs
            "run": {"info": {"status": "success", "name": "My Monitor"}},
        },
    )

    result_dict = await run_monitor.ainvoke(_args(monitor_id="mon-123"))

    assert isinstance(result_dict, dict)
    result = RunMonitorOutput.model_validate(result_dict)
    assert result.success is True
    assert result.run is not None


@pytest.mark.asyncio
async def test_update_variable(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/environments/env-456",
        json={
            "environment": {
                "id": "env-456",
                "name": "production",
                "values": [
                    {"key": "BASE_URL", "value": "https://old.example.com", "enabled": True, "type": "default"},
                ],
            },
        },
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/environments/env-456",
        json={
            # TODO: fill in a representative response shape from Postman API docs
            "environment": {"id": "env-456", "name": "production"},
        },
    )

    result_dict = await update_variable.ainvoke(
        _args(
            environment_id="env-456",
            variable="BASE_URL",
            variable_value="https://new.example.com",
        )
    )

    assert isinstance(result_dict, dict)
    result = UpdateVariableOutput.model_validate(result_dict)
    assert result.success is True
    assert result.environment_id == "env-456"


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_create_environment_empty_credential() -> None:
    """Empty API key should short-circuit without hitting the network."""
    result_dict = await create_environment.ainvoke(
        {"environment_name": "test-env", "api_key": ""}
    )
    assert isinstance(result_dict, dict)
    result = CreateEnvironmentOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
