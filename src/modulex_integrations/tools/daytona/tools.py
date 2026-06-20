"""Daytona LangChain ``@tool`` functions.

Twelve async tools wrapping the Daytona REST API and per-sandbox
toolbox API. The modulex ``ToolExecutor`` injects ``api_key: str``
directly (resolved from the user's credential); every function builds
``Authorization: Bearer <api_key>`` from it.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions — non-2xx does *not* raise.
"""
from __future__ import annotations

import base64
import json
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.daytona.outputs import (
    CreateSandboxOutput,
    DeleteSandboxOutput,
    DownloadFileOutput,
    ExecuteCommandOutput,
    FileInfo,
    GetSandboxOutput,
    GitCloneOutput,
    ListFilesOutput,
    ListSandboxesOutput,
    RunCodeOutput,
    SandboxSummary,
    StartSandboxOutput,
    StopSandboxOutput,
    UploadFileOutput,
)

__all__ = [
    "create_sandbox",
    "delete_sandbox",
    "download_file",
    "execute_command",
    "get_sandbox",
    "git_clone",
    "list_files",
    "list_sandboxes",
    "run_code",
    "start_sandbox",
    "stop_sandbox",
    "upload_file",
]

_API_BASE_URL = "https://app.daytona.io/api"
_TOOLBOX_BASE_URL = "https://proxy.app.daytona.io/toolbox"

_DEFAULT_TIMEOUT = 30.0
_LONG_TIMEOUT = 120.0

# Cap on the inline (base64) download payload, mirroring the upstream 100MB
# download limit on the raw bytes.
_MAX_DOWNLOAD_SIZE_BYTES = 100 * 1024 * 1024


# --- Auth + helpers --------------------------------------------------------


def _headers(api_key: str, *, json_body: bool = False) -> dict[str, str]:
    headers: dict[str, str] = {"Authorization": f"Bearer {api_key}"}
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def _encode_sandbox_id(sandbox_id: str) -> str:
    return quote(sandbox_id.strip(), safe="")


def _toolbox_url(sandbox_id: str, path: str) -> str:
    return f"{_TOOLBOX_BASE_URL}/{_encode_sandbox_id(sandbox_id)}{path}"


def _map_sandbox(data: dict[str, Any]) -> SandboxSummary:
    return SandboxSummary(
        id=data.get("id"),
        name=data.get("name"),
        state=data.get("state"),
        snapshot=data.get("snapshot"),
        target=data.get("target"),
        cpu=data.get("cpu"),
        gpu=data.get("gpu"),
        memory=data.get("memory"),
        disk=data.get("disk"),
        labels=data.get("labels") or {},
        public=data.get("public"),
        error_reason=data.get("errorReason"),
        auto_stop_interval=data.get("autoStopInterval"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
    )


def _error_message(response: httpx.Response, fallback: str) -> str:
    try:
        data = response.json()
    except Exception:
        return f"{fallback} (status {response.status_code})"
    message = data.get("message") if isinstance(data, dict) else None
    if isinstance(message, str):
        return message
    if isinstance(message, list):
        return ", ".join(str(part) for part in message)
    err = data.get("error") if isinstance(data, dict) else None
    if isinstance(err, str):
        return err
    return f"{fallback} (status {response.status_code})"


def _parse_json(response: httpx.Response) -> dict[str, Any]:
    """Tolerate empty bodies from lifecycle endpoints (e.g. 200/204)."""
    text = response.text
    if not text:
        return {}
    try:
        parsed = response.json()
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


# --- Input schemas (args_schema for each @tool) ----------------------------


class CreateSandboxInput(BaseModel):
    api_key: str = Field(description="Daytona API key (provided by credential system)")
    snapshot: str | None = Field(
        default=None,
        description="ID or name of the snapshot to create the sandbox from (uses default if empty)",
    )
    name: str | None = Field(
        default=None, description="Name for the sandbox (defaults to the sandbox ID)"
    )
    target: str | None = Field(
        default=None, description="Region where the sandbox will be created (e.g., us, eu)"
    )
    user: str | None = Field(default=None, description="User associated with the sandbox")
    env: dict[str, Any] | None = Field(
        default=None, description="Environment variables to set in the sandbox as key-value pairs"
    )
    labels: dict[str, Any] | None = Field(
        default=None, description="Labels to attach to the sandbox as key-value pairs"
    )
    cpu: int | None = Field(default=None, description="CPU cores to allocate to the sandbox")
    memory: int | None = Field(
        default=None, description="Memory to allocate to the sandbox in GB"
    )
    disk: int | None = Field(
        default=None, description="Disk space to allocate to the sandbox in GB"
    )
    auto_stop_interval: int | None = Field(
        default=None, description="Auto-stop interval in minutes (0 disables auto-stop)"
    )
    auto_archive_interval: int | None = Field(
        default=None, description="Auto-archive interval in minutes (0 uses the maximum interval)"
    )
    auto_delete_interval: int | None = Field(
        default=None,
        description=(
            "Auto-delete interval in minutes (negative disables, 0 deletes immediately on stop)"
        ),
    )
    public: bool | None = Field(
        default=None, description="Whether the sandbox HTTP preview is publicly accessible"
    )


class ListSandboxesInput(BaseModel):
    api_key: str = Field(description="Daytona API key (provided by credential system)")
    limit: int | None = Field(
        default=None, description="Maximum number of sandboxes to return (1-200)"
    )
    name: str | None = Field(
        default=None, description="Filter sandboxes by name prefix (case-insensitive)"
    )
    labels: dict[str, Any] | None = Field(
        default=None, description="Filter sandboxes by labels as key-value pairs"
    )
    cursor: str | None = Field(
        default=None, description="Pagination cursor from a previous response"
    )


class GetSandboxInput(BaseModel):
    api_key: str = Field(description="Daytona API key (provided by credential system)")
    sandbox_id: str = Field(description="ID or name of the sandbox")


class StartSandboxInput(BaseModel):
    api_key: str = Field(description="Daytona API key (provided by credential system)")
    sandbox_id: str = Field(description="ID or name of the sandbox")


class StopSandboxInput(BaseModel):
    api_key: str = Field(description="Daytona API key (provided by credential system)")
    sandbox_id: str = Field(description="ID or name of the sandbox")


class DeleteSandboxInput(BaseModel):
    api_key: str = Field(description="Daytona API key (provided by credential system)")
    sandbox_id: str = Field(description="ID or name of the sandbox")


class ExecuteCommandInput(BaseModel):
    api_key: str = Field(description="Daytona API key (provided by credential system)")
    sandbox_id: str = Field(description="ID of the sandbox to execute the command in")
    command: str = Field(description="Shell command to execute")
    cwd: str | None = Field(
        default=None,
        description="Working directory for the command (defaults to the sandbox working directory)",
    )
    env: dict[str, Any] | None = Field(
        default=None, description="Environment variables to set for the command as key-value pairs"
    )
    timeout: int | None = Field(
        default=None, description="Timeout in seconds (defaults to 10 seconds)"
    )


class RunCodeInput(BaseModel):
    api_key: str = Field(description="Daytona API key (provided by credential system)")
    sandbox_id: str = Field(description="ID of the sandbox to run the code in")
    code: str = Field(description="Code to run")
    language: str = Field(
        description="Language of the code: python, javascript, or typescript"
    )
    env: dict[str, Any] | None = Field(
        default=None, description="Environment variables to set for the run as key-value pairs"
    )
    timeout: int | None = Field(
        default=None, description="Timeout in seconds (defaults to 10 seconds)"
    )


class UploadFileInput(BaseModel):
    api_key: str = Field(description="Daytona API key (provided by credential system)")
    sandbox_id: str = Field(description="ID of the sandbox to upload the file to")
    destination_path: str = Field(
        description=(
            "Destination path in the sandbox (a trailing slash uploads into that "
            "directory using the file name)"
        )
    )
    file_content_base64: str = Field(
        description="Base64-encoded content of the file to upload"
    )
    file_name: str | None = Field(default=None, description="Optional file name override")


class DownloadFileInput(BaseModel):
    api_key: str = Field(description="Daytona API key (provided by credential system)")
    sandbox_id: str = Field(description="ID of the sandbox to download the file from")
    file_path: str = Field(description="Path of the file in the sandbox")


class ListFilesInput(BaseModel):
    api_key: str = Field(description="Daytona API key (provided by credential system)")
    sandbox_id: str = Field(description="ID of the sandbox to list files in")
    path: str | None = Field(
        default=None,
        description="Directory path to list (defaults to the sandbox working directory)",
    )


class GitCloneInput(BaseModel):
    api_key: str = Field(description="Daytona API key (provided by credential system)")
    sandbox_id: str = Field(description="ID of the sandbox to clone the repository into")
    url: str = Field(description="URL of the Git repository to clone")
    path: str = Field(description="Path in the sandbox to clone the repository into")
    branch: str | None = Field(
        default=None, description="Branch to clone (defaults to the default branch)"
    )
    commit_id: str | None = Field(
        default=None, description="Specific commit to check out after cloning"
    )
    username: str | None = Field(
        default=None, description="Username for authenticating to private repositories"
    )
    password: str | None = Field(
        default=None, description="Password or personal access token for private repositories"
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=CreateSandboxInput)
@serialize_pydantic_return
async def create_sandbox(
    api_key: str,
    snapshot: str | None = None,
    name: str | None = None,
    target: str | None = None,
    user: str | None = None,
    env: dict[str, Any] | None = None,
    labels: dict[str, Any] | None = None,
    cpu: int | None = None,
    memory: int | None = None,
    disk: int | None = None,
    auto_stop_interval: int | None = None,
    auto_archive_interval: int | None = None,
    auto_delete_interval: int | None = None,
    public: bool | None = None,
) -> CreateSandboxOutput:
    """Create a new Daytona sandbox for running AI-generated code in isolation."""
    if not api_key or not api_key.strip():
        return CreateSandboxOutput(
            success=False,
            error="Daytona API key is empty. Please configure a valid Daytona credential.",
        )

    body: dict[str, Any] = {}
    if snapshot:
        body["snapshot"] = snapshot
    if name:
        body["name"] = name
    if target:
        body["target"] = target
    if user:
        body["user"] = user
    if env:
        body["env"] = env
    if labels:
        body["labels"] = labels
    if cpu is not None:
        body["cpu"] = cpu
    if memory is not None:
        body["memory"] = memory
    if disk is not None:
        body["disk"] = disk
    if auto_stop_interval is not None:
        body["autoStopInterval"] = auto_stop_interval
    if auto_archive_interval is not None:
        body["autoArchiveInterval"] = auto_archive_interval
    if auto_delete_interval is not None:
        body["autoDeleteInterval"] = auto_delete_interval
    if public is not None:
        body["public"] = public

    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE_URL}/sandbox",
                headers=_headers(api_key, json_body=True),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateSandboxOutput(
                success=False, error=_error_message(response, "Failed to create sandbox")
            )
        data = _parse_json(response)
    except httpx.TimeoutException:
        return CreateSandboxOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateSandboxOutput(success=False, error=f"Create sandbox failed: {exc}")

    return CreateSandboxOutput(success=True, sandbox=_map_sandbox(data))


@tool(args_schema=ListSandboxesInput)
@serialize_pydantic_return
async def list_sandboxes(
    api_key: str,
    limit: int | None = None,
    name: str | None = None,
    labels: dict[str, Any] | None = None,
    cursor: str | None = None,
) -> ListSandboxesOutput:
    """List Daytona sandboxes in the organization."""
    if not api_key or not api_key.strip():
        return ListSandboxesOutput(
            success=False,
            error="Daytona API key is empty. Please configure a valid Daytona credential.",
        )

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = min(max(int(limit), 1), 200)
    if name:
        params["name"] = name
    if labels:
        params["labels"] = json.dumps(labels)
    if cursor:
        params["cursor"] = cursor

    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE_URL}/sandbox", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListSandboxesOutput(
                success=False, error=_error_message(response, "Failed to list sandboxes")
            )
        data = _parse_json(response)
    except httpx.TimeoutException:
        return ListSandboxesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListSandboxesOutput(success=False, error=f"List sandboxes failed: {exc}")

    items = data.get("items")
    items = items if isinstance(items, list) else []
    return ListSandboxesOutput(
        success=True,
        sandboxes=[_map_sandbox(item) for item in items if isinstance(item, dict)],
        next_cursor=data.get("nextCursor"),
    )


@tool(args_schema=GetSandboxInput)
@serialize_pydantic_return
async def get_sandbox(api_key: str, sandbox_id: str) -> GetSandboxOutput:
    """Get details of a Daytona sandbox."""
    if not api_key or not api_key.strip():
        return GetSandboxOutput(
            success=False,
            error="Daytona API key is empty. Please configure a valid Daytona credential.",
        )
    if not sandbox_id or not sandbox_id.strip():
        return GetSandboxOutput(success=False, error="Sandbox ID is required.")

    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE_URL}/sandbox/{_encode_sandbox_id(sandbox_id)}",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return GetSandboxOutput(
                success=False, error=_error_message(response, "Failed to get sandbox")
            )
        data = _parse_json(response)
    except httpx.TimeoutException:
        return GetSandboxOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSandboxOutput(success=False, error=f"Get sandbox failed: {exc}")

    return GetSandboxOutput(success=True, sandbox=_map_sandbox(data))


@tool(args_schema=StartSandboxInput)
@serialize_pydantic_return
async def start_sandbox(api_key: str, sandbox_id: str) -> StartSandboxOutput:
    """Start a stopped Daytona sandbox."""
    if not api_key or not api_key.strip():
        return StartSandboxOutput(
            success=False,
            error="Daytona API key is empty. Please configure a valid Daytona credential.",
        )
    if not sandbox_id or not sandbox_id.strip():
        return StartSandboxOutput(success=False, error="Sandbox ID is required.")

    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE_URL}/sandbox/{_encode_sandbox_id(sandbox_id)}/start",
                headers=_headers(api_key),
            )
        if response.status_code not in (200, 201):
            return StartSandboxOutput(
                success=False, error=_error_message(response, "Failed to start sandbox")
            )
        data = _parse_json(response)
    except httpx.TimeoutException:
        return StartSandboxOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return StartSandboxOutput(success=False, error=f"Start sandbox failed: {exc}")

    sandbox = _map_sandbox(data)
    if not sandbox.id:
        sandbox.id = sandbox_id.strip()
    return StartSandboxOutput(success=True, sandbox=sandbox)


@tool(args_schema=StopSandboxInput)
@serialize_pydantic_return
async def stop_sandbox(api_key: str, sandbox_id: str) -> StopSandboxOutput:
    """Stop a running Daytona sandbox."""
    if not api_key or not api_key.strip():
        return StopSandboxOutput(
            success=False,
            error="Daytona API key is empty. Please configure a valid Daytona credential.",
        )
    if not sandbox_id or not sandbox_id.strip():
        return StopSandboxOutput(success=False, error="Sandbox ID is required.")

    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE_URL}/sandbox/{_encode_sandbox_id(sandbox_id)}/stop",
                headers=_headers(api_key),
            )
        if response.status_code not in (200, 201):
            return StopSandboxOutput(
                success=False, error=_error_message(response, "Failed to stop sandbox")
            )
        data = _parse_json(response)
    except httpx.TimeoutException:
        return StopSandboxOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return StopSandboxOutput(success=False, error=f"Stop sandbox failed: {exc}")

    sandbox = _map_sandbox(data)
    if not sandbox.id:
        sandbox.id = sandbox_id.strip()
    return StopSandboxOutput(success=True, sandbox=sandbox)


@tool(args_schema=DeleteSandboxInput)
@serialize_pydantic_return
async def delete_sandbox(api_key: str, sandbox_id: str) -> DeleteSandboxOutput:
    """Delete a Daytona sandbox."""
    if not api_key or not api_key.strip():
        return DeleteSandboxOutput(
            success=False,
            error="Daytona API key is empty. Please configure a valid Daytona credential.",
        )
    if not sandbox_id or not sandbox_id.strip():
        return DeleteSandboxOutput(success=False, error="Sandbox ID is required.")

    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            response = await client.delete(
                f"{_API_BASE_URL}/sandbox/{_encode_sandbox_id(sandbox_id)}",
                headers=_headers(api_key),
            )
        if response.status_code not in (200, 204):
            return DeleteSandboxOutput(
                success=False, error=_error_message(response, "Failed to delete sandbox")
            )
        data = _parse_json(response)
    except httpx.TimeoutException:
        return DeleteSandboxOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteSandboxOutput(success=False, error=f"Delete sandbox failed: {exc}")

    sandbox = _map_sandbox(data)
    if not sandbox.id:
        sandbox.id = sandbox_id.strip()
    return DeleteSandboxOutput(success=True, sandbox=sandbox)


@tool(args_schema=ExecuteCommandInput)
@serialize_pydantic_return
async def execute_command(
    api_key: str,
    sandbox_id: str,
    command: str,
    cwd: str | None = None,
    env: dict[str, Any] | None = None,
    timeout: int | None = None,
) -> ExecuteCommandOutput:
    """Execute a shell command inside a Daytona sandbox."""
    if not api_key or not api_key.strip():
        return ExecuteCommandOutput(
            success=False,
            error="Daytona API key is empty. Please configure a valid Daytona credential.",
        )
    if not sandbox_id or not sandbox_id.strip():
        return ExecuteCommandOutput(success=False, error="Sandbox ID is required.")

    body: dict[str, Any] = {"command": command}
    if cwd:
        body["cwd"] = cwd
    if env:
        body["envs"] = env
    if timeout is not None:
        body["timeout"] = timeout

    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            response = await client.post(
                _toolbox_url(sandbox_id, "/process/execute"),
                headers=_headers(api_key, json_body=True),
                json=body,
            )
        if response.status_code != 200:
            return ExecuteCommandOutput(
                success=False, error=_error_message(response, "Failed to execute command")
            )
        data = _parse_json(response)
    except httpx.TimeoutException:
        return ExecuteCommandOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ExecuteCommandOutput(success=False, error=f"Execute command failed: {exc}")

    return ExecuteCommandOutput(
        success=True,
        exit_code=data.get("exitCode") if data.get("exitCode") is not None else -1,
        result=data.get("result") or "",
    )


@tool(args_schema=RunCodeInput)
@serialize_pydantic_return
async def run_code(
    api_key: str,
    sandbox_id: str,
    code: str,
    language: str,
    env: dict[str, Any] | None = None,
    timeout: int | None = None,
) -> RunCodeOutput:
    """Run Python, JavaScript, or TypeScript code inside a Daytona sandbox."""
    if not api_key or not api_key.strip():
        return RunCodeOutput(
            success=False,
            error="Daytona API key is empty. Please configure a valid Daytona credential.",
        )
    if not sandbox_id or not sandbox_id.strip():
        return RunCodeOutput(success=False, error="Sandbox ID is required.")

    body: dict[str, Any] = {"code": code, "language": language}
    if env:
        body["envs"] = env
    if timeout is not None:
        body["timeout"] = timeout

    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            response = await client.post(
                _toolbox_url(sandbox_id, "/process/code-run"),
                headers=_headers(api_key, json_body=True),
                json=body,
            )
        if response.status_code != 200:
            return RunCodeOutput(
                success=False, error=_error_message(response, "Failed to run code")
            )
        data = _parse_json(response)
    except httpx.TimeoutException:
        return RunCodeOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RunCodeOutput(success=False, error=f"Run code failed: {exc}")

    return RunCodeOutput(
        success=True,
        exit_code=data.get("exitCode") if data.get("exitCode") is not None else -1,
        result=data.get("result") or "",
        artifacts=data.get("artifacts"),
    )


@tool(args_schema=UploadFileInput)
@serialize_pydantic_return
async def upload_file(
    api_key: str,
    sandbox_id: str,
    destination_path: str,
    file_content_base64: str,
    file_name: str | None = None,
) -> UploadFileOutput:
    """Upload a file to a Daytona sandbox."""
    if not api_key or not api_key.strip():
        return UploadFileOutput(
            success=False,
            error="Daytona API key is empty. Please configure a valid Daytona credential.",
        )
    if not sandbox_id or not sandbox_id.strip():
        return UploadFileOutput(success=False, error="Sandbox ID is required.")

    try:
        raw = base64.b64decode(file_content_base64)
    except Exception as exc:
        return UploadFileOutput(
            success=False, error=f"file_content_base64 is not valid base64: {exc}"
        )

    dest = destination_path.strip()
    upload_name = file_name or (dest.rstrip("/").split("/")[-1] or "upload")
    target_path = dest if not dest.endswith("/") else f"{dest}{upload_name}"

    # TODO (unverified): the Daytona toolbox file-upload route and its
    # multipart field name ("file") are not fully documented publicly; the
    # path query param and multipart upload are inferred from the toolbox
    # files API per https://www.daytona.io/docs (Toolbox / File System).
    url = _toolbox_url(sandbox_id, f"/files/upload?path={quote(target_path, safe='')}")
    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            response = await client.post(
                url,
                headers=_headers(api_key),
                files={"file": (upload_name, raw)},
            )
        if response.status_code not in (200, 201):
            return UploadFileOutput(
                success=False, error=_error_message(response, "Failed to upload file")
            )
    except httpx.TimeoutException:
        return UploadFileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UploadFileOutput(success=False, error=f"Upload file failed: {exc}")

    return UploadFileOutput(
        success=True,
        uploaded_path=target_path,
        name=upload_name,
        size=len(raw),
    )


@tool(args_schema=DownloadFileInput)
@serialize_pydantic_return
async def download_file(
    api_key: str, sandbox_id: str, file_path: str
) -> DownloadFileOutput:
    """Download a file from a Daytona sandbox (returned base64-encoded inline)."""
    if not api_key or not api_key.strip():
        return DownloadFileOutput(
            success=False,
            error="Daytona API key is empty. Please configure a valid Daytona credential.",
        )
    if not sandbox_id or not sandbox_id.strip():
        return DownloadFileOutput(success=False, error="Sandbox ID is required.")

    path = file_path.strip()
    url = _toolbox_url(sandbox_id, f"/files/download?path={quote(path, safe='')}")
    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            response = await client.get(url, headers=_headers(api_key))
        if response.status_code != 200:
            return DownloadFileOutput(
                success=False, error=_error_message(response, "Failed to download file")
            )
        raw = response.content
    except httpx.TimeoutException:
        return DownloadFileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DownloadFileOutput(success=False, error=f"Download file failed: {exc}")

    if len(raw) > _MAX_DOWNLOAD_SIZE_BYTES:
        size_mb = len(raw) / (1024 * 1024)
        return DownloadFileOutput(
            success=False,
            error=f"File size ({size_mb:.2f}MB) exceeds download limit of 100MB",
        )

    mime_type = response.headers.get("content-type") or "application/octet-stream"
    file_name = next((p for p in reversed(path.split("/")) if p), "download")
    return DownloadFileOutput(
        success=True,
        name=file_name,
        mime_type=mime_type,
        size=len(raw),
        content_base64=base64.b64encode(raw).decode("ascii"),
    )


@tool(args_schema=ListFilesInput)
@serialize_pydantic_return
async def list_files(
    api_key: str, sandbox_id: str, path: str | None = None
) -> ListFilesOutput:
    """List files in a directory of a Daytona sandbox."""
    if not api_key or not api_key.strip():
        return ListFilesOutput(
            success=False,
            error="Daytona API key is empty. Please configure a valid Daytona credential.",
        )
    if not sandbox_id or not sandbox_id.strip():
        return ListFilesOutput(success=False, error="Sandbox ID is required.")

    query = f"?path={quote(path.strip(), safe='')}" if path else ""
    url = _toolbox_url(sandbox_id, f"/files{query}")
    try:
        async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
            response = await client.get(url, headers=_headers(api_key))
        if response.status_code != 200:
            return ListFilesOutput(
                success=False, error=_error_message(response, "Failed to list files")
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListFilesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListFilesOutput(success=False, error=f"List files failed: {exc}")

    entries = data if isinstance(data, list) else []
    return ListFilesOutput(
        success=True,
        files=[
            FileInfo(
                name=entry.get("name"),
                is_dir=entry.get("isDir"),
                size=entry.get("size"),
                mode=entry.get("mode"),
                permissions=entry.get("permissions"),
                owner=entry.get("owner"),
                group=entry.get("group"),
                modified_at=entry.get("modifiedAt"),
            )
            for entry in entries
            if isinstance(entry, dict)
        ],
    )


@tool(args_schema=GitCloneInput)
@serialize_pydantic_return
async def git_clone(
    api_key: str,
    sandbox_id: str,
    url: str,
    path: str,
    branch: str | None = None,
    commit_id: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> GitCloneOutput:
    """Clone a Git repository into a Daytona sandbox."""
    if not api_key or not api_key.strip():
        return GitCloneOutput(
            success=False,
            error="Daytona API key is empty. Please configure a valid Daytona credential.",
        )
    if not sandbox_id or not sandbox_id.strip():
        return GitCloneOutput(success=False, error="Sandbox ID is required.")

    body: dict[str, Any] = {"url": url, "path": path}
    if branch:
        body["branch"] = branch
    if commit_id:
        body["commit_id"] = commit_id
    if username:
        body["username"] = username
    if password:
        body["password"] = password

    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            response = await client.post(
                _toolbox_url(sandbox_id, "/git/clone"),
                headers=_headers(api_key, json_body=True),
                json=body,
            )
        if response.status_code != 200:
            return GitCloneOutput(
                success=False, error=_error_message(response, "Failed to clone repository")
            )
    except httpx.TimeoutException:
        return GitCloneOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GitCloneOutput(success=False, error=f"Git clone failed: {exc}")

    return GitCloneOutput(success=True, repo_url=url, clone_path=path)
