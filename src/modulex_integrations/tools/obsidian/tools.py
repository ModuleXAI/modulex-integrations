"""Obsidian LangChain ``@tool`` functions.

These tools call the Obsidian Local REST API plugin, which runs locally
inside the user's Obsidian app and is reachable at a user-supplied
``base_url`` (default ``https://127.0.0.1:27124``). The plugin presents a
self-signed TLS certificate, so the HTTP client intentionally does not
verify the certificate chain.

Auth convention: ``api_key`` is injected directly by the runtime
(key-based). Every request authenticates with
``Authorization: Bearer <api_key>``.

Error model: non-2xx responses and exceptions are caught and surface as
``success=False`` + ``error`` on the typed output (they do not raise).
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.obsidian.outputs import (
    AppendActiveOutput,
    AppendNoteOutput,
    AppendPeriodicNoteOutput,
    CommandItem,
    CreateNoteOutput,
    DeleteNoteOutput,
    ExecuteCommandOutput,
    FileEntry,
    GetActiveOutput,
    GetNoteOutput,
    GetPeriodicNoteOutput,
    ListCommandsOutput,
    ListFilesOutput,
    OpenFileOutput,
    PatchActiveOutput,
    PatchNoteOutput,
    SearchMatch,
    SearchOutput,
    SearchResultItem,
)

__all__ = [
    "append_active",
    "append_note",
    "append_periodic_note",
    "create_note",
    "delete_note",
    "execute_command",
    "get_active",
    "get_note",
    "get_periodic_note",
    "list_commands",
    "list_files",
    "open_file",
    "patch_active",
    "patch_note",
    "search",
]

_TIMEOUT = 30.0
_MISSING_KEY = "Obsidian Local REST API key is empty. Please configure a valid credential."
_MISSING_BASE = "base_url is required (e.g. https://127.0.0.1:27124)."


def _base(base_url: str) -> str:
    """Strip a single trailing slash from the base URL."""
    return base_url.rstrip("/")


def _encode_path(path: str) -> str:
    """Percent-encode each path segment, preserving the slash separators."""
    return "/".join(quote(seg, safe="") for seg in path.strip().split("/"))


def _headers(api_key: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    headers: dict[str, str] = {"Authorization": f"Bearer {api_key}"}
    if extra:
        headers.update(extra)
    return headers


# --- Input schemas (args_schema for each @tool) ----------------------------


class ListFilesInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    path: str | None = Field(
        default=None,
        description="Directory path relative to vault root. Leave empty to list the root.",
    )


class GetNoteInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    filename: str = Field(
        description='Path to the note relative to vault root (e.g. "folder/note.md")'
    )


class CreateNoteInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    filename: str = Field(
        description='Path for the note relative to vault root (e.g. "folder/note.md")'
    )
    content: str = Field(description="Markdown content for the note")


class AppendNoteInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    filename: str = Field(
        description='Path to the note relative to vault root (e.g. "folder/note.md")'
    )
    content: str = Field(description="Markdown content to append to the note")


class PatchNoteInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    filename: str = Field(
        description='Path to the note relative to vault root (e.g. "folder/note.md")'
    )
    content: str = Field(description="Content to insert at the target location")
    operation: str = Field(description="How to insert content: append, prepend, or replace")
    target_type: str = Field(description="Type of target: heading, block, or frontmatter")
    target: str = Field(
        description="Target identifier (heading text, block reference ID, or frontmatter field)"
    )
    target_delimiter: str | None = Field(
        default=None, description='Delimiter for nested headings (default: "::")'
    )
    trim_target_whitespace: bool | None = Field(
        default=None, description="Whether to trim whitespace from target before matching"
    )


class DeleteNoteInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    filename: str = Field(description="Path to the note to delete relative to vault root")


class SearchInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    query: str = Field(description="Text to search for across vault notes")
    context_length: int | None = Field(
        default=None, description="Number of characters of context around each match (default: 100)"
    )


class GetActiveInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")


class AppendActiveInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    content: str = Field(description="Markdown content to append to the active file")


class PatchActiveInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    content: str = Field(description="Content to insert at the target location")
    operation: str = Field(description="How to insert content: append, prepend, or replace")
    target_type: str = Field(description="Type of target: heading, block, or frontmatter")
    target: str = Field(
        description="Target identifier (heading text, block reference ID, or frontmatter field)"
    )
    target_delimiter: str | None = Field(
        default=None, description='Delimiter for nested headings (default: "::")'
    )
    trim_target_whitespace: bool | None = Field(
        default=None, description="Whether to trim whitespace from target before matching"
    )


class ListCommandsInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")


class ExecuteCommandInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    command_id: str = Field(
        description=(
            "ID of the command to execute (use list_commands to discover available commands)"
        )
    )


class OpenFileInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    filename: str = Field(description="Path to the file relative to vault root")
    new_leaf: bool | None = Field(
        default=None, description="Whether to open the file in a new leaf/tab"
    )


class GetPeriodicNoteInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    period: str = Field(
        description="Period type: daily, weekly, monthly, quarterly, or yearly"
    )


class AppendPeriodicNoteInput(BaseModel):
    base_url: str = Field(description="Base URL for the Obsidian Local REST API")
    api_key: str = Field(description="Obsidian Local REST API key (provided by credential system)")
    period: str = Field(
        description="Period type: daily, weekly, monthly, quarterly, or yearly"
    )
    content: str = Field(description="Markdown content to append to the periodic note")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=ListFilesInput)
@serialize_pydantic_return
async def list_files(
    base_url: str,
    api_key: str,
    path: str | None = None,
) -> ListFilesOutput:
    """List files and directories in your Obsidian vault."""
    if not base_url or not base_url.strip():
        return ListFilesOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return ListFilesOutput(success=False, error=_MISSING_KEY)

    suffix = f"/{_encode_path(path)}/" if path and path.strip() else "/"
    url = f"{_base(base_url)}/vault{suffix}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.get(
                url, headers=_headers(api_key, {"Accept": "application/json"})
            )
        if response.status_code != 200:
            return ListFilesOutput(
                success=False,
                error=f"Failed to list files ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListFilesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFilesOutput(success=False, error=f"List files failed: {exc}")

    entries: list[FileEntry] = []
    for item in data.get("files") or []:
        if isinstance(item, str):
            entries.append(
                FileEntry(path=item, type="directory" if item.endswith("/") else "file")
            )
        elif isinstance(item, dict):
            entries.append(FileEntry(path=item.get("path") or "", type=item.get("type") or "file"))
    return ListFilesOutput(success=True, files=entries)


@tool(args_schema=GetNoteInput)
@serialize_pydantic_return
async def get_note(
    base_url: str,
    api_key: str,
    filename: str,
) -> GetNoteOutput:
    """Retrieve the content of a note from your Obsidian vault."""
    if not base_url or not base_url.strip():
        return GetNoteOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return GetNoteOutput(success=False, error=_MISSING_KEY)

    url = f"{_base(base_url)}/vault/{_encode_path(filename)}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.get(
                url, headers=_headers(api_key, {"Accept": "text/markdown"})
            )
        if response.status_code != 200:
            return GetNoteOutput(
                success=False,
                error=f"Failed to get note ({response.status_code}): {response.text}",
            )
        content = response.text
    except httpx.TimeoutException:
        return GetNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetNoteOutput(success=False, error=f"Get note failed: {exc}")

    return GetNoteOutput(success=True, content=content, filename=filename)


@tool(args_schema=CreateNoteInput)
@serialize_pydantic_return
async def create_note(
    base_url: str,
    api_key: str,
    filename: str,
    content: str,
) -> CreateNoteOutput:
    """Create or replace a note in your Obsidian vault."""
    if not base_url or not base_url.strip():
        return CreateNoteOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return CreateNoteOutput(success=False, error=_MISSING_KEY)

    url = f"{_base(base_url)}/vault/{_encode_path(filename)}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.put(
                url,
                headers=_headers(api_key, {"Content-Type": "text/markdown"}),
                content=content,
            )
        if response.status_code not in (200, 201, 204):
            return CreateNoteOutput(
                success=False,
                error=f"Failed to create note ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return CreateNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateNoteOutput(success=False, error=f"Create note failed: {exc}")

    return CreateNoteOutput(success=True, filename=filename, created=True)


@tool(args_schema=AppendNoteInput)
@serialize_pydantic_return
async def append_note(
    base_url: str,
    api_key: str,
    filename: str,
    content: str,
) -> AppendNoteOutput:
    """Append content to an existing note in your Obsidian vault."""
    if not base_url or not base_url.strip():
        return AppendNoteOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return AppendNoteOutput(success=False, error=_MISSING_KEY)

    url = f"{_base(base_url)}/vault/{_encode_path(filename)}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.post(
                url,
                headers=_headers(api_key, {"Content-Type": "text/markdown"}),
                content=content,
            )
        if response.status_code not in (200, 201, 204):
            return AppendNoteOutput(
                success=False,
                error=f"Failed to append to note ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return AppendNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AppendNoteOutput(success=False, error=f"Append to note failed: {exc}")

    return AppendNoteOutput(success=True, filename=filename, appended=True)


def _patch_headers(
    api_key: str,
    operation: str,
    target_type: str,
    target: str,
    target_delimiter: str | None,
    trim_target_whitespace: bool | None,
) -> dict[str, str]:
    headers: dict[str, str] = {
        "Content-Type": "text/markdown",
        "Operation": operation,
        "Target-Type": target_type,
        "Target": quote(target, safe=""),
    }
    if target_delimiter:
        headers["Target-Delimiter"] = target_delimiter
    if trim_target_whitespace:
        headers["Trim-Target-Whitespace"] = "true"
    return _headers(api_key, headers)


@tool(args_schema=PatchNoteInput)
@serialize_pydantic_return
async def patch_note(
    base_url: str,
    api_key: str,
    filename: str,
    content: str,
    operation: str,
    target_type: str,
    target: str,
    target_delimiter: str | None = None,
    trim_target_whitespace: bool | None = None,
) -> PatchNoteOutput:
    """Insert or replace content at a heading, block reference, or frontmatter field in a note."""
    if not base_url or not base_url.strip():
        return PatchNoteOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return PatchNoteOutput(success=False, error=_MISSING_KEY)

    url = f"{_base(base_url)}/vault/{_encode_path(filename)}"
    headers = _patch_headers(
        api_key, operation, target_type, target, target_delimiter, trim_target_whitespace
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.patch(url, headers=headers, content=content)
        if response.status_code not in (200, 201, 204):
            return PatchNoteOutput(
                success=False,
                error=f"Failed to patch note ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return PatchNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PatchNoteOutput(success=False, error=f"Patch note failed: {exc}")

    return PatchNoteOutput(success=True, filename=filename, patched=True)


@tool(args_schema=DeleteNoteInput)
@serialize_pydantic_return
async def delete_note(
    base_url: str,
    api_key: str,
    filename: str,
) -> DeleteNoteOutput:
    """Delete a note from your Obsidian vault."""
    if not base_url or not base_url.strip():
        return DeleteNoteOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return DeleteNoteOutput(success=False, error=_MISSING_KEY)

    url = f"{_base(base_url)}/vault/{_encode_path(filename)}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.delete(url, headers=_headers(api_key))
        if response.status_code not in (200, 202, 204):
            return DeleteNoteOutput(
                success=False,
                error=f"Failed to delete note ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteNoteOutput(success=False, error=f"Delete note failed: {exc}")

    return DeleteNoteOutput(success=True, filename=filename, deleted=True)


@tool(args_schema=SearchInput)
@serialize_pydantic_return
async def search(
    base_url: str,
    api_key: str,
    query: str,
    context_length: int | None = None,
) -> SearchOutput:
    """Search for text across notes in your Obsidian vault."""
    if not base_url or not base_url.strip():
        return SearchOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return SearchOutput(success=False, error=_MISSING_KEY)

    params: dict[str, Any] = {"query": query}
    if context_length is not None:
        params["contextLength"] = context_length
    url = f"{_base(base_url)}/search/simple/"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.post(
                url, headers=_headers(api_key, {"Accept": "application/json"}), params=params
            )
        if response.status_code != 200:
            return SearchOutput(
                success=False,
                error=f"Search failed ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SearchOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchOutput(success=False, error=f"Search failed: {exc}")

    results: list[SearchResultItem] = []
    for item in data or []:
        if not isinstance(item, dict):
            continue
        results.append(
            SearchResultItem(
                filename=item.get("filename") or "",
                score=item.get("score") or 0,
                matches=[
                    SearchMatch(context=m.get("context") or "")
                    for m in item.get("matches") or []
                    if isinstance(m, dict)
                ],
            )
        )
    return SearchOutput(success=True, results=results)


@tool(args_schema=GetActiveInput)
@serialize_pydantic_return
async def get_active(
    base_url: str,
    api_key: str,
) -> GetActiveOutput:
    """Retrieve the content of the currently active file in Obsidian."""
    if not base_url or not base_url.strip():
        return GetActiveOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return GetActiveOutput(success=False, error=_MISSING_KEY)

    url = f"{_base(base_url)}/active/"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.get(
                url, headers=_headers(api_key, {"Accept": "application/vnd.olrapi.note+json"})
            )
        if response.status_code != 200:
            return GetActiveOutput(
                success=False,
                error=f"Failed to get active file ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetActiveOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetActiveOutput(success=False, error=f"Get active file failed: {exc}")

    return GetActiveOutput(
        success=True, content=data.get("content") or "", filename=data.get("path")
    )


@tool(args_schema=AppendActiveInput)
@serialize_pydantic_return
async def append_active(
    base_url: str,
    api_key: str,
    content: str,
) -> AppendActiveOutput:
    """Append content to the currently active file in Obsidian."""
    if not base_url or not base_url.strip():
        return AppendActiveOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return AppendActiveOutput(success=False, error=_MISSING_KEY)

    url = f"{_base(base_url)}/active/"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.post(
                url,
                headers=_headers(api_key, {"Content-Type": "text/markdown"}),
                content=content,
            )
        if response.status_code not in (200, 201, 204):
            return AppendActiveOutput(
                success=False,
                error=f"Failed to append to active file ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return AppendActiveOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AppendActiveOutput(success=False, error=f"Append to active file failed: {exc}")

    return AppendActiveOutput(success=True, appended=True)


@tool(args_schema=PatchActiveInput)
@serialize_pydantic_return
async def patch_active(
    base_url: str,
    api_key: str,
    content: str,
    operation: str,
    target_type: str,
    target: str,
    target_delimiter: str | None = None,
    trim_target_whitespace: bool | None = None,
) -> PatchActiveOutput:
    """Insert or replace content at a heading, block, or frontmatter field in the active file."""
    if not base_url or not base_url.strip():
        return PatchActiveOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return PatchActiveOutput(success=False, error=_MISSING_KEY)

    url = f"{_base(base_url)}/active/"
    headers = _patch_headers(
        api_key, operation, target_type, target, target_delimiter, trim_target_whitespace
    )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.patch(url, headers=headers, content=content)
        if response.status_code not in (200, 201, 204):
            return PatchActiveOutput(
                success=False,
                error=f"Failed to patch active file ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return PatchActiveOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PatchActiveOutput(success=False, error=f"Patch active file failed: {exc}")

    return PatchActiveOutput(success=True, patched=True)


@tool(args_schema=ListCommandsInput)
@serialize_pydantic_return
async def list_commands(
    base_url: str,
    api_key: str,
) -> ListCommandsOutput:
    """List all available commands in Obsidian."""
    if not base_url or not base_url.strip():
        return ListCommandsOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return ListCommandsOutput(success=False, error=_MISSING_KEY)

    url = f"{_base(base_url)}/commands/"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.get(
                url, headers=_headers(api_key, {"Accept": "application/json"})
            )
        if response.status_code != 200:
            return ListCommandsOutput(
                success=False,
                error=f"Failed to list commands ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListCommandsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCommandsOutput(success=False, error=f"List commands failed: {exc}")

    commands = [
        CommandItem(id=cmd.get("id") or "", name=cmd.get("name") or "")
        for cmd in data.get("commands") or []
        if isinstance(cmd, dict)
    ]
    return ListCommandsOutput(success=True, commands=commands)


@tool(args_schema=ExecuteCommandInput)
@serialize_pydantic_return
async def execute_command(
    base_url: str,
    api_key: str,
    command_id: str,
) -> ExecuteCommandOutput:
    """Execute a command in Obsidian (e.g. open daily note, toggle sidebar)."""
    if not base_url or not base_url.strip():
        return ExecuteCommandOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return ExecuteCommandOutput(success=False, error=_MISSING_KEY)

    url = f"{_base(base_url)}/commands/{quote(command_id.strip(), safe='')}/"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.post(url, headers=_headers(api_key))
        if response.status_code not in (200, 201, 204):
            return ExecuteCommandOutput(
                success=False,
                error=f"Failed to execute command ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return ExecuteCommandOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ExecuteCommandOutput(success=False, error=f"Execute command failed: {exc}")

    return ExecuteCommandOutput(success=True, command_id=command_id, executed=True)


@tool(args_schema=OpenFileInput)
@serialize_pydantic_return
async def open_file(
    base_url: str,
    api_key: str,
    filename: str,
    new_leaf: bool | None = None,
) -> OpenFileOutput:
    """Open a file in the Obsidian UI (creates the file if it does not exist)."""
    if not base_url or not base_url.strip():
        return OpenFileOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return OpenFileOutput(success=False, error=_MISSING_KEY)

    params: dict[str, Any] = {}
    if new_leaf:
        params["newLeaf"] = "true"
    url = f"{_base(base_url)}/open/{_encode_path(filename)}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.post(url, headers=_headers(api_key), params=params)
        if response.status_code not in (200, 201, 204):
            return OpenFileOutput(
                success=False,
                error=f"Failed to open file ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return OpenFileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return OpenFileOutput(success=False, error=f"Open file failed: {exc}")

    return OpenFileOutput(success=True, filename=filename, opened=True)


@tool(args_schema=GetPeriodicNoteInput)
@serialize_pydantic_return
async def get_periodic_note(
    base_url: str,
    api_key: str,
    period: str,
) -> GetPeriodicNoteOutput:
    """Retrieve the current periodic note (daily, weekly, monthly, quarterly, or yearly)."""
    if not base_url or not base_url.strip():
        return GetPeriodicNoteOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return GetPeriodicNoteOutput(success=False, error=_MISSING_KEY)

    url = f"{_base(base_url)}/periodic/{quote(period, safe='')}/"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.get(
                url, headers=_headers(api_key, {"Accept": "text/markdown"})
            )
        if response.status_code != 200:
            return GetPeriodicNoteOutput(
                success=False,
                error=f"Failed to get periodic note ({response.status_code}): {response.text}",
            )
        content = response.text
    except httpx.TimeoutException:
        return GetPeriodicNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetPeriodicNoteOutput(success=False, error=f"Get periodic note failed: {exc}")

    return GetPeriodicNoteOutput(success=True, content=content, period=period)


@tool(args_schema=AppendPeriodicNoteInput)
@serialize_pydantic_return
async def append_periodic_note(
    base_url: str,
    api_key: str,
    period: str,
    content: str,
) -> AppendPeriodicNoteOutput:
    """Append content to the current periodic note. Creates the note if it does not exist."""
    if not base_url or not base_url.strip():
        return AppendPeriodicNoteOutput(success=False, error=_MISSING_BASE)
    if not api_key or not api_key.strip():
        return AppendPeriodicNoteOutput(success=False, error=_MISSING_KEY)

    url = f"{_base(base_url)}/periodic/{quote(period, safe='')}/"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT, verify=False) as client:
            response = await client.post(
                url,
                headers=_headers(api_key, {"Content-Type": "text/markdown"}),
                content=content,
            )
        if response.status_code not in (200, 201, 204):
            return AppendPeriodicNoteOutput(
                success=False,
                error=(
                    f"Failed to append to periodic note "
                    f"({response.status_code}): {response.text}"
                ),
            )
    except httpx.TimeoutException:
        return AppendPeriodicNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AppendPeriodicNoteOutput(
            success=False, error=f"Append to periodic note failed: {exc}"
        )

    return AppendPeriodicNoteOutput(success=True, period=period, appended=True)
