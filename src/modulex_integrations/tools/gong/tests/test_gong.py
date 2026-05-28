"""Happy-path tests for every gong @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.gong import (
    TOOLS,
    add_new_call,
    get_extensive_data,
    list_calls,
    list_workspace_id_options,
    manifest,
    retrieve_transcripts_of_calls,
)
from modulex_integrations.tools.gong.outputs import (
    AddNewCallOutput,
    GetExtensiveDataOutput,
    ListCallsOutput,
    ListWorkspaceIdOptionsOutput,
    RetrieveTranscriptsOfCallsOutput,
)

API = "https://us-66463.api.gong.io/v2"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a .ainvoke() input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_5_actions(self) -> None:
        assert len(manifest.actions) == 5

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_new_call(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/calls",
        json={
            # TODO: fill in a representative response shape from the Gong API docs
            "requestId": "req-123",
            "callId": "call-456",
        },
    )

    result_dict = await add_new_call.ainvoke(
        _args(
            client_unique_id="unique-id-123",
            actual_start="2024-01-15T10:00:00Z",
            direction="Outbound",
            primary_user="user-789",
            parties=[{"emailAddress": "test@example.com", "name": "Test User"}],
        )
    )

    assert isinstance(result_dict, dict)
    result = AddNewCallOutput.model_validate(result_dict)
    assert result.success is True
    assert result.request_id == "req-123"
    assert result.call_id == "call-456"


@pytest.mark.asyncio
async def test_get_extensive_data(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/calls/extensive",
        json={
            # TODO: fill in a representative response shape from the Gong API docs
            "requestId": "req-abc",
            "records": {"cursor": None, "totalRecords": 1},
            "calls": [{"metaData": {"id": "call-1", "title": "Demo Call"}}],
        },
    )

    result_dict = await get_extensive_data.ainvoke(
        _args(from_date_time="2024-01-01T00:00:00Z", to_date_time="2024-01-31T23:59:59Z")
    )

    assert isinstance(result_dict, dict)
    result = GetExtensiveDataOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.calls) == 1


@pytest.mark.asyncio
async def test_list_calls(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calls",
        json={
            # TODO: fill in a representative response shape from the Gong API docs
            "requestId": "req-xyz",
            "records": {"cursor": "next-page", "totalRecords": 2},
            "calls": [
                {"id": "call-1", "title": "Call A"},
                {"id": "call-2", "title": "Call B"},
            ],
        },
    )

    result_dict = await list_calls.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListCallsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.calls) == 2
    assert result.request_id == "req-xyz"


@pytest.mark.asyncio
async def test_list_workspace_id_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/workspaces",
        json={
            # TODO: fill in a representative response shape from the Gong API docs
            "workspaces": [
                {"id": "ws-1", "name": "Default Workspace"},
                {"id": "ws-2", "name": "Sales Team"},
            ],
        },
    )

    result_dict = await list_workspace_id_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListWorkspaceIdOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.workspaces) == 2
    assert result.workspaces[0].name == "Default Workspace"


@pytest.mark.asyncio
async def test_retrieve_transcripts_of_calls(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/calls/transcript",
        json={
            # TODO: fill in a representative response shape from the Gong API docs
            "requestId": "req-tr-1",
            "callTranscripts": [
                {
                    "callId": "call-1",
                    "transcript": [
                        {"speakerId": "s1", "topic": "Introduction", "sentences": []}
                    ],
                }
            ],
        },
    )

    result_dict = await retrieve_transcripts_of_calls.ainvoke(
        _args(call_ids=["call-1"])
    )

    assert isinstance(result_dict, dict)
    result = RetrieveTranscriptsOfCallsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.call_transcripts) == 1


# --- Failure-path tests (credential short-circuit) -------------------------


@pytest.mark.asyncio
async def test_list_calls_empty_credential() -> None:
    """list_calls must fail immediately when access_token is missing/empty."""
    result_dict = await list_calls.ainvoke(
        {"auth_type": "oauth2", "auth_data": {"access_token": ""}}
    )

    assert isinstance(result_dict, dict)
    result = ListCallsOutput.model_validate(result_dict)
    assert result.success is False
    assert "access_token" in (result.error or "")
