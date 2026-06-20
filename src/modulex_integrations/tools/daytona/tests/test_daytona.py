"""Happy-path tests per action + failure-path and empty-credential tests.

Daytona wraps every call in try/except, so non-2xx responses surface as
``success=False`` rather than raising.
"""
from __future__ import annotations

import base64
from typing import Any

import pytest

from modulex_integrations.tools.daytona import (
    TOOLS,
    create_sandbox,
    delete_sandbox,
    download_file,
    execute_command,
    get_sandbox,
    git_clone,
    list_files,
    list_sandboxes,
    manifest,
    run_code,
    start_sandbox,
    stop_sandbox,
    upload_file,
)
from modulex_integrations.tools.daytona.outputs import (
    CreateSandboxOutput,
    DeleteSandboxOutput,
    DownloadFileOutput,
    ExecuteCommandOutput,
    GetSandboxOutput,
    GitCloneOutput,
    ListFilesOutput,
    ListSandboxesOutput,
    RunCodeOutput,
    StartSandboxOutput,
    StopSandboxOutput,
    UploadFileOutput,
)

API = "https://app.daytona.io/api"
TOOLBOX = "https://proxy.app.daytona.io/toolbox"
_API_KEY = "fake-api-key"
_SANDBOX = "sb-123"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_12_actions(self) -> None:
        assert len(manifest.actions) == 12

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo(self) -> None:
        assert manifest.logo == "modulex:daytona-themed"


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_create_sandbox(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sandbox",
        json={"id": "sb-123", "name": "my-box", "state": "started", "cpu": 2},
    )

    result_dict = await create_sandbox.ainvoke(_args(name="my-box", cpu=2))

    assert isinstance(result_dict, dict)
    result = CreateSandboxOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sandbox is not None
    assert result.sandbox.id == "sb-123"
    assert result.sandbox.state == "started"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_list_sandboxes(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sandbox?limit=1",
        json={"items": [{"id": "sb-1", "name": "a"}], "nextCursor": "cur-2"},
    )

    result_dict = await list_sandboxes.ainvoke(_args(limit=1))

    result = ListSandboxesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sandboxes[0].id == "sb-1"
    assert result.next_cursor == "cur-2"


@pytest.mark.asyncio
async def test_get_sandbox(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/sandbox/{_SANDBOX}",
        json={"id": _SANDBOX, "state": "stopped"},
    )

    result_dict = await get_sandbox.ainvoke(_args(sandbox_id=_SANDBOX))

    result = GetSandboxOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sandbox is not None
    assert result.sandbox.state == "stopped"


@pytest.mark.asyncio
async def test_start_sandbox(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/sandbox/{_SANDBOX}/start", text="")

    result_dict = await start_sandbox.ainvoke(_args(sandbox_id=_SANDBOX))

    result = StartSandboxOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sandbox is not None
    assert result.sandbox.id == _SANDBOX  # falls back to the requested id


@pytest.mark.asyncio
async def test_stop_sandbox(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/sandbox/{_SANDBOX}/stop", text="")

    result_dict = await stop_sandbox.ainvoke(_args(sandbox_id=_SANDBOX))

    result = StopSandboxOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sandbox is not None
    assert result.sandbox.id == _SANDBOX


@pytest.mark.asyncio
async def test_delete_sandbox(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/sandbox/{_SANDBOX}", status_code=204, text=""
    )

    result_dict = await delete_sandbox.ainvoke(_args(sandbox_id=_SANDBOX))

    result = DeleteSandboxOutput.model_validate(result_dict)
    assert result.success is True
    assert result.sandbox is not None
    assert result.sandbox.id == _SANDBOX


@pytest.mark.asyncio
async def test_execute_command(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{TOOLBOX}/{_SANDBOX}/process/execute",
        json={"exitCode": 0, "result": "hello\n"},
    )

    result_dict = await execute_command.ainvoke(
        _args(sandbox_id=_SANDBOX, command="echo hello")
    )

    result = ExecuteCommandOutput.model_validate(result_dict)
    assert result.success is True
    assert result.exit_code == 0
    assert result.result == "hello\n"


@pytest.mark.asyncio
async def test_run_code(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{TOOLBOX}/{_SANDBOX}/process/code-run",
        json={"exitCode": 0, "result": "42\n", "artifacts": {"charts": []}},
    )

    result_dict = await run_code.ainvoke(
        _args(sandbox_id=_SANDBOX, code="print(42)", language="python")
    )

    result = RunCodeOutput.model_validate(result_dict)
    assert result.success is True
    assert result.exit_code == 0
    assert result.result == "42\n"
    assert result.artifacts == {"charts": []}


@pytest.mark.asyncio
async def test_upload_file(httpx_mock):  # type: ignore[no-untyped-def]
    content = base64.b64encode(b"hello world").decode("ascii")
    httpx_mock.add_response(
        method="POST",
        url=f"{TOOLBOX}/{_SANDBOX}/files/upload?path=%2Fhome%2Fdaytona%2Fdata.txt",
        json={},
    )

    result_dict = await upload_file.ainvoke(
        _args(
            sandbox_id=_SANDBOX,
            destination_path="/home/daytona/data.txt",
            file_content_base64=content,
        )
    )

    result = UploadFileOutput.model_validate(result_dict)
    assert result.success is True
    assert result.uploaded_path == "/home/daytona/data.txt"
    assert result.name == "data.txt"
    assert result.size == len(b"hello world")


@pytest.mark.asyncio
async def test_download_file(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{TOOLBOX}/{_SANDBOX}/files/download?path=%2Fhome%2Fdaytona%2Fout.txt",
        content=b"result bytes",
        headers={"content-type": "text/plain"},
    )

    result_dict = await download_file.ainvoke(
        _args(sandbox_id=_SANDBOX, file_path="/home/daytona/out.txt")
    )

    result = DownloadFileOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "out.txt"
    assert result.mime_type == "text/plain"
    assert result.size == len(b"result bytes")
    assert result.content_base64 is not None
    assert base64.b64decode(result.content_base64) == b"result bytes"


@pytest.mark.asyncio
async def test_list_files(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{TOOLBOX}/{_SANDBOX}/files?path=%2Fhome%2Fdaytona",
        json=[
            {"name": "data.csv", "isDir": False, "size": 10, "permissions": "rw-r--r--"}
        ],
    )

    result_dict = await list_files.ainvoke(
        _args(sandbox_id=_SANDBOX, path="/home/daytona")
    )

    result = ListFilesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.files[0].name == "data.csv"
    assert result.files[0].is_dir is False


@pytest.mark.asyncio
async def test_git_clone(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST", url=f"{TOOLBOX}/{_SANDBOX}/git/clone", json={}
    )

    result_dict = await git_clone.ainvoke(
        _args(
            sandbox_id=_SANDBOX,
            url="https://github.com/org/repo.git",
            path="/home/daytona/repo",
        )
    )

    result = GitCloneOutput.model_validate(result_dict)
    assert result.success is True
    assert result.repo_url == "https://github.com/org/repo.git"
    assert result.clone_path == "/home/daytona/repo"


# --- Failure-path + empty-credential tests ---------------------------------


@pytest.mark.asyncio
async def test_create_sandbox_non_2xx_returns_error(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/sandbox",
        status_code=402,
        json={"message": "Quota exceeded"},
    )

    result_dict = await create_sandbox.ainvoke(_args(name="x"))

    result = CreateSandboxOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "Quota exceeded"
    assert result.sandbox is None


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits() -> None:
    result_dict = await get_sandbox.ainvoke({"api_key": "", "sandbox_id": _SANDBOX})

    result = GetSandboxOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error
