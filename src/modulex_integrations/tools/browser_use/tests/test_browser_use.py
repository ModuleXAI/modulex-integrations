"""Happy-path tests for every browser_use @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.browser_use import (
    TOOLS,
    create_browser_session,
    create_profile,
    create_session,
    create_workspace,
    delete_profile,
    delete_session,
    delete_workspace,
    delete_workspace_file,
    get_account_billing,
    get_browser_session,
    get_profile,
    get_session,
    get_workspace,
    get_workspace_size,
    list_browser_sessions,
    list_profiles,
    list_session_messages,
    list_sessions,
    list_workspace_files,
    list_workspaces,
    manifest,
    stop_session,
    update_browser_session,
    update_profile,
    update_workspace,
    upload_workspace_files,
)
from modulex_integrations.tools.browser_use.outputs import (
    CreateBrowserSessionOutput,
    CreateProfileOutput,
    CreateSessionOutput,
    CreateWorkspaceOutput,
    DeleteProfileOutput,
    DeleteSessionOutput,
    DeleteWorkspaceFileOutput,
    DeleteWorkspaceOutput,
    GetAccountBillingOutput,
    GetBrowserSessionOutput,
    GetProfileOutput,
    GetSessionOutput,
    GetWorkspaceOutput,
    GetWorkspaceSizeOutput,
    ListBrowserSessionsOutput,
    ListProfilesOutput,
    ListSessionMessagesOutput,
    ListSessionsOutput,
    ListWorkspaceFilesOutput,
    ListWorkspacesOutput,
    StopSessionOutput,
    UpdateBrowserSessionOutput,
    UpdateProfileOutput,
    UpdateWorkspaceOutput,
    UploadWorkspaceFilesOutput,
)

API = "https://api.browser-use.com/api/v3"

_API_KEY = "fake-browser-use-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_25_actions(self) -> None:
        assert len(manifest.actions) == 25

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_session(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sessions",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "sess_123",
            "status": "running",
            "task": "Go to example.com",
            "liveUrl": "https://live.browser-use.com/sess_123",
        },
    )

    result_dict = await create_session.ainvoke(_args(task="Go to example.com"))

    assert isinstance(result_dict, dict)
    result = CreateSessionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "sess_123"


@pytest.mark.asyncio
async def test_get_session(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sessions/sess_123",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "sess_123",
            "status": "completed",
            "task": "Go to example.com",
            "output": "The page contains...",
            "liveUrl": "https://live.browser-use.com/sess_123",
            "screenshotUrl": "https://cdn.browser-use.com/ss/123.png",
            "cost": 0.05,
        },
    )

    result_dict = await get_session.ainvoke(_args(session_id="sess_123"))

    assert isinstance(result_dict, dict)
    result = GetSessionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_list_sessions(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sessions?page=1&page_size=20",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "sessions": [{"id": "sess_1"}, {"id": "sess_2"}],
            "total": 2,
        },
    )

    result_dict = await list_sessions.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListSessionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.sessions) == 2


@pytest.mark.asyncio
async def test_delete_session(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/sessions/sess_123",
        status_code=204,
    )

    result_dict = await delete_session.ainvoke(_args(session_id="sess_123"))

    assert isinstance(result_dict, dict)
    result = DeleteSessionOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_stop_session(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sessions/sess_123/stop",
        json={"status": "stopped"},
    )

    result_dict = await stop_session.ainvoke(_args(session_id="sess_123"))

    assert isinstance(result_dict, dict)
    result = StopSessionOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_session_messages(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sessions/sess_123/messages?limit=10",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "messages": [{"id": "msg_1", "role": "assistant", "content": "Navigating..."}],
        },
    )

    result_dict = await list_session_messages.ainvoke(_args(session_id="sess_123"))

    assert isinstance(result_dict, dict)
    result = ListSessionMessagesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.messages) == 1


@pytest.mark.asyncio
async def test_create_browser_session(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/browsers",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "bs_123",
            "status": "active",
            "liveUrl": "https://live.browser-use.com/bs_123",
            "cdpUrl": "wss://cdp.browser-use.com/bs_123",
        },
    )

    result_dict = await create_browser_session.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = CreateBrowserSessionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "bs_123"


@pytest.mark.asyncio
async def test_get_browser_session(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/browsers/bs_123",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "bs_123",
            "status": "active",
            "liveUrl": "https://live.browser-use.com/bs_123",
            "cdpUrl": "wss://cdp.browser-use.com/bs_123",
            "timeout": 60,
            "cost": 0.01,
        },
    )

    result_dict = await get_browser_session.ainvoke(_args(browser_session_id="bs_123"))

    assert isinstance(result_dict, dict)
    result = GetBrowserSessionOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "active"


@pytest.mark.asyncio
async def test_list_browser_sessions(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/browsers?page_size=20&page=1",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "items": [{"id": "bs_1"}, {"id": "bs_2"}],
            "totalItems": 2,
        },
    )

    result_dict = await list_browser_sessions.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListBrowserSessionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 2


@pytest.mark.asyncio
async def test_update_browser_session(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/browsers/bs_123",
        json={"status": "stopped"},
    )

    result_dict = await update_browser_session.ainvoke(_args(browser_session_id="bs_123", action="stop"))

    assert isinstance(result_dict, dict)
    result = UpdateBrowserSessionOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_create_profile(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/profiles",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "prof_123",
            "name": "My Profile",
        },
    )

    result_dict = await create_profile.ainvoke(_args(name="My Profile"))

    assert isinstance(result_dict, dict)
    result = CreateProfileOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "prof_123"


@pytest.mark.asyncio
async def test_get_profile(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/profiles/prof_123",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "prof_123",
            "name": "My Profile",
            "userId": "user_abc",
        },
    )

    result_dict = await get_profile.ainvoke(_args(profile_id="prof_123"))

    assert isinstance(result_dict, dict)
    result = GetProfileOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "My Profile"


@pytest.mark.asyncio
async def test_list_profiles(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/profiles?page_size=20&page=1",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "items": [{"id": "prof_1"}],
            "totalItems": 1,
        },
    )

    result_dict = await list_profiles.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListProfilesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_delete_profile(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/profiles/prof_123",
        status_code=204,
    )

    result_dict = await delete_profile.ainvoke(_args(profile_id="prof_123"))

    assert isinstance(result_dict, dict)
    result = DeleteProfileOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_profile(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/profiles/prof_123",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "prof_123",
            "name": "Updated Profile",
            "userId": "user_abc",
        },
    )

    result_dict = await update_profile.ainvoke(_args(profile_id="prof_123", name="Updated Profile"))

    assert isinstance(result_dict, dict)
    result = UpdateProfileOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "Updated Profile"


@pytest.mark.asyncio
async def test_create_workspace(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/workspaces",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "ws_123",
            "name": "My Workspace",
        },
    )

    result_dict = await create_workspace.ainvoke(_args(name="My Workspace"))

    assert isinstance(result_dict, dict)
    result = CreateWorkspaceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "ws_123"


@pytest.mark.asyncio
async def test_get_workspace(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/workspaces/ws_123",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "ws_123",
            "name": "My Workspace",
        },
    )

    result_dict = await get_workspace.ainvoke(_args(workspace_id="ws_123"))

    assert isinstance(result_dict, dict)
    result = GetWorkspaceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "My Workspace"


@pytest.mark.asyncio
async def test_list_workspaces(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/workspaces?page_size=20&page=1",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "items": [{"id": "ws_1"}],
            "totalItems": 1,
        },
    )

    result_dict = await list_workspaces.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListWorkspacesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_delete_workspace(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/workspaces/ws_123",
        status_code=204,
    )

    result_dict = await delete_workspace.ainvoke(_args(workspace_id="ws_123"))

    assert isinstance(result_dict, dict)
    result = DeleteWorkspaceOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_update_workspace(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/workspaces/ws_123",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "id": "ws_123",
            "name": "Updated Workspace",
        },
    )

    result_dict = await update_workspace.ainvoke(_args(workspace_id="ws_123", name="Updated Workspace"))

    assert isinstance(result_dict, dict)
    result = UpdateWorkspaceOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "Updated Workspace"


@pytest.mark.asyncio
async def test_get_workspace_size(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/workspaces/ws_123/size",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "sizeBytes": 1048576,
        },
    )

    result_dict = await get_workspace_size.ainvoke(_args(workspace_id="ws_123"))

    assert isinstance(result_dict, dict)
    result = GetWorkspaceSizeOutput.model_validate(result_dict)
    assert result.success is True
    assert result.size_bytes == 1048576


@pytest.mark.asyncio
async def test_list_workspace_files(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/workspaces/ws_123/files?limit=50&includeUrls=false&shallow=false",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "files": [{"name": "report.csv", "path": "reports/report.csv"}],
            "cursor": None,
        },
    )

    result_dict = await list_workspace_files.ainvoke(_args(workspace_id="ws_123"))

    assert isinstance(result_dict, dict)
    result = ListWorkspaceFilesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.files) == 1


@pytest.mark.asyncio
async def test_delete_workspace_file(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/workspaces/ws_123/files?path=reports%2Fdata.csv",
        status_code=204,
    )

    result_dict = await delete_workspace_file.ainvoke(_args(workspace_id="ws_123", path="reports/data.csv"))

    assert isinstance(result_dict, dict)
    result = DeleteWorkspaceFileOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_upload_workspace_files(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/workspaces/ws_123/files/upload",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "files": [{"name": "data.csv", "uploadUrl": "https://s3.amazonaws.com/...", "path": "data.csv"}],
        },
    )

    result_dict = await upload_workspace_files.ainvoke(
        _args(workspace_id="ws_123", files_json='[{"name": "data.csv"}]')
    )

    assert isinstance(result_dict, dict)
    result = UploadWorkspaceFilesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.files) == 1


@pytest.mark.asyncio
async def test_get_account_billing(httpx_mock) -> None:  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/billing/account",
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "plan": "pro",
            "credits_remaining": 100.0,
        },
    )

    result_dict = await get_account_billing.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetAccountBillingOutput.model_validate(result_dict)
    assert result.success is True


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_create_session_validates_empty_api_key() -> None:
    result_dict = await create_session.ainvoke({"api_key": ""})
    result = CreateSessionOutput.model_validate(result_dict)
    assert result.success is False
    assert "API key" in (result.error or "")
