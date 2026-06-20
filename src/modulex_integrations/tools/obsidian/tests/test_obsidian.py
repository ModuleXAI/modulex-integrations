"""Happy-path tests per action + failure-path and empty-credential tests.

The Obsidian Local REST API does not raise on non-2xx; tools surface
errors as ``success=False`` + ``error``.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.obsidian import (
    TOOLS,
    append_active,
    append_note,
    append_periodic_note,
    create_note,
    delete_note,
    execute_command,
    get_active,
    get_note,
    get_periodic_note,
    list_commands,
    list_files,
    manifest,
    open_file,
    patch_active,
    patch_note,
    search,
)
from modulex_integrations.tools.obsidian.outputs import (
    AppendActiveOutput,
    AppendNoteOutput,
    AppendPeriodicNoteOutput,
    CreateNoteOutput,
    DeleteNoteOutput,
    ExecuteCommandOutput,
    GetActiveOutput,
    GetNoteOutput,
    GetPeriodicNoteOutput,
    ListCommandsOutput,
    ListFilesOutput,
    OpenFileOutput,
    PatchActiveOutput,
    PatchNoteOutput,
    SearchOutput,
)

BASE = "https://127.0.0.1:27124"
_API_KEY = "fake-api-key"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(base_url=BASE, api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_15_actions(self) -> None:
        assert len(manifest.actions) == 15

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_list_files(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/vault/",
        json={"files": ["Note.md", "Projects/"]},
    )
    result_dict = await list_files.ainvoke(_args())
    assert isinstance(result_dict, dict)
    result = ListFilesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.files[0].path == "Note.md"
    assert result.files[0].type == "file"
    assert result.files[1].type == "directory"
    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_list_files_with_path(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/vault/Projects/",
        json={"files": [{"path": "Projects/a.md", "type": "file"}]},
    )
    result_dict = await list_files.ainvoke(_args(path="Projects"))
    result = ListFilesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.files[0].path == "Projects/a.md"


@pytest.mark.asyncio
async def test_get_note(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/vault/folder/note.md",
        text="# Hello\n\nbody",
    )
    result_dict = await get_note.ainvoke(_args(filename="folder/note.md"))
    result = GetNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.content == "# Hello\n\nbody"
    assert result.filename == "folder/note.md"


@pytest.mark.asyncio
async def test_create_note(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PUT", url=f"{BASE}/vault/n.md", status_code=204)
    result_dict = await create_note.ainvoke(_args(filename="n.md", content="x"))
    result = CreateNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.created is True
    assert result.filename == "n.md"


@pytest.mark.asyncio
async def test_append_note(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{BASE}/vault/n.md", status_code=204)
    result_dict = await append_note.ainvoke(_args(filename="n.md", content="more"))
    result = AppendNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.appended is True


@pytest.mark.asyncio
async def test_patch_note(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PATCH", url=f"{BASE}/vault/n.md", status_code=200)
    result_dict = await patch_note.ainvoke(
        _args(
            filename="n.md",
            content="x",
            operation="append",
            target_type="heading",
            target="Today",
        )
    )
    result = PatchNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.patched is True
    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Operation"] == "append"
    assert sent.headers["Target-Type"] == "heading"
    assert sent.headers["Target"] == "Today"


@pytest.mark.asyncio
async def test_delete_note(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{BASE}/vault/n.md", status_code=204)
    result_dict = await delete_note.ainvoke(_args(filename="n.md"))
    result = DeleteNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True


@pytest.mark.asyncio
async def test_search(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/search/simple/?query=todo",
        json=[
            {
                "filename": "Tasks.md",
                "score": 0.8,
                "matches": [{"context": "a todo item"}],
            }
        ],
    )
    result_dict = await search.ainvoke(_args(query="todo"))
    result = SearchOutput.model_validate(result_dict)
    assert result.success is True
    assert result.results[0].filename == "Tasks.md"
    assert result.results[0].score == 0.8
    assert result.results[0].matches[0].context == "a todo item"


@pytest.mark.asyncio
async def test_get_active(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/active/",
        json={"content": "active body", "path": "Active.md"},
    )
    result_dict = await get_active.ainvoke(_args())
    result = GetActiveOutput.model_validate(result_dict)
    assert result.success is True
    assert result.content == "active body"
    assert result.filename == "Active.md"


@pytest.mark.asyncio
async def test_append_active(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{BASE}/active/", status_code=204)
    result_dict = await append_active.ainvoke(_args(content="line"))
    result = AppendActiveOutput.model_validate(result_dict)
    assert result.success is True
    assert result.appended is True


@pytest.mark.asyncio
async def test_patch_active(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="PATCH", url=f"{BASE}/active/", status_code=200)
    result_dict = await patch_active.ainvoke(
        _args(
            content="x",
            operation="prepend",
            target_type="block",
            target="abc123",
        )
    )
    result = PatchActiveOutput.model_validate(result_dict)
    assert result.success is True
    assert result.patched is True


@pytest.mark.asyncio
async def test_open_file(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{BASE}/open/n.md", status_code=200)
    result_dict = await open_file.ainvoke(_args(filename="n.md"))
    result = OpenFileOutput.model_validate(result_dict)
    assert result.success is True
    assert result.opened is True
    assert result.filename == "n.md"


@pytest.mark.asyncio
async def test_list_commands(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/commands/",
        json={"commands": [{"id": "daily-notes:open-today", "name": "Open today"}]},
    )
    result_dict = await list_commands.ainvoke(_args())
    result = ListCommandsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.commands[0].id == "daily-notes:open-today"
    assert result.commands[0].name == "Open today"


@pytest.mark.asyncio
async def test_execute_command(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE}/commands/daily-notes%3Aopen-today/",
        status_code=204,
    )
    result_dict = await execute_command.ainvoke(_args(command_id="daily-notes:open-today"))
    result = ExecuteCommandOutput.model_validate(result_dict)
    assert result.success is True
    assert result.executed is True
    assert result.command_id == "daily-notes:open-today"


@pytest.mark.asyncio
async def test_get_periodic_note(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/periodic/daily/",
        text="# Daily\n\nentry",
    )
    result_dict = await get_periodic_note.ainvoke(_args(period="daily"))
    result = GetPeriodicNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.content == "# Daily\n\nentry"
    assert result.period == "daily"


@pytest.mark.asyncio
async def test_append_periodic_note(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{BASE}/periodic/daily/", status_code=204)
    result_dict = await append_periodic_note.ainvoke(_args(period="daily", content="hi"))
    result = AppendPeriodicNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.appended is True
    assert result.period == "daily"


# --- Failure-path + empty-credential tests ---------------------------------


@pytest.mark.asyncio
async def test_get_note_http_error(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{BASE}/vault/missing.md",
        status_code=404,
        text="not found",
    )
    result_dict = await get_note.ainvoke(_args(filename="missing.md"))
    result = GetNoteOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "404" in result.error


@pytest.mark.asyncio
async def test_search_empty_api_key() -> None:
    result_dict = await search.ainvoke(
        {"base_url": BASE, "api_key": "", "query": "x"}
    )
    result = SearchOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_list_files_empty_base_url() -> None:
    result_dict = await list_files.ainvoke({"base_url": "", "api_key": _API_KEY})
    result = ListFilesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
