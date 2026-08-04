"""Flint LangChain ``@tool`` functions.

Three async tools wrapping the Flint Agent Tasks API
(``https://app.tryflint.com/api/v1``). The calling convention is
*key-based*: the modulex ``ToolExecutor`` injects an ``api_key: str``
directly (resolved from the user's credential), not an
``auth_type``/``auth_data`` pair. The key is sent as
``Authorization: Bearer <api_key>``.

Task model: ``create_task`` and ``generate_pages`` both start a
*background* agent task and return immediately with a ``task_id`` and a
``running`` status — they do not wait for the site changes to land. Poll
``get_task`` with that id until ``status`` becomes ``completed`` (page
URLs in ``pages_created`` / ``pages_modified`` / ``pages_deleted``) or
``failed`` (reason in ``error_message``). Alternatively pass
``callback_url`` and Flint POSTs the terminal result to that HTTPS
endpoint itself.

Error model: every call is guarded so non-2xx HTTP responses, timeouts,
and unexpected exceptions return the typed output with ``success=False``
+ ``error`` instead of raising. The API reports failures as
``{"error": "..."}``, which is unwrapped into the ``error`` string; a 2xx
body that carries no ``taskId`` is treated as a failure too. Successful
payloads are parsed permissively with ``.get()``.
"""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.flint.outputs import (
    CreateTaskOutput,
    GeneratePagesOutput,
    GetTaskOutput,
    TaskPage,
)

__all__ = ["create_task", "generate_pages", "get_task"]

_API_BASE = "https://app.tryflint.com/api/v1"
_TIMEOUT = 30.0
_MAX_ITEMS = 10
_EMPTY_KEY_ERROR = "Flint API key is empty. Please configure a valid Flint credential."
_NO_TASK_ID_ERROR = "Flint did not return a task ID"


# --- Shared helpers --------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }


def _ok(response: httpx.Response) -> bool:
    return 200 <= response.status_code < 300


def _error(response: httpx.Response) -> str:
    """Unwrap the API's ``{"error": ...}`` payload into a single string."""
    payload: Any = None
    try:
        payload = response.json()
    except Exception:
        payload = None

    detail: str | None = None
    if isinstance(payload, dict):
        raw = payload.get("error")
        if isinstance(raw, str) and raw:
            detail = raw

    return f"Flint API error ({response.status_code}): {detail or response.text}"


def _as_dict(payload: Any) -> dict[str, Any]:
    """Coerce a raw JSON value into a dict (a non-object body degrades to empty)."""
    return payload if isinstance(payload, dict) else {}


def _as_str(value: Any) -> str | None:
    """Coerce a raw JSON value into a string field (non-strings degrade to None)."""
    return value if isinstance(value, str) else None


def _as_dicts(value: Any) -> list[dict[str, Any]]:
    """Coerce a raw JSON value into a list of dict rows."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _task_page(item: dict[str, Any]) -> TaskPage:
    return TaskPage(
        slug=_as_str(item.get("slug")),
        preview_url=_as_str(item.get("previewUrl")),
        edit_url=_as_str(item.get("editUrl")),
        published_url=_as_str(item.get("publishedUrl")),
    )


def _missing_task_id_error(data: dict[str, Any]) -> str:
    reported = data.get("error")
    if isinstance(reported, str) and reported:
        return reported
    return _NO_TASK_ID_ERROR


def _parse_items(
    raw: list[dict[str, Any]] | str,
) -> tuple[list[dict[str, str]] | None, str | None]:
    """Validate the ``items`` input and normalize it to the API's wire shape.

    Accepts either an already-structured array or a JSON string (agents
    frequently emit the latter). Returns ``(items, None)`` on success or
    ``(None, error_message)`` on any validation failure.
    """
    parsed: Any
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except Exception:
            return None, "Invalid JSON in items parameter."
    else:
        parsed = raw

    if not isinstance(parsed, list) or not parsed:
        return (
            None,
            "items must be a non-empty JSON array of "
            "{targetPageSlug, context} objects.",
        )
    if len(parsed) > _MAX_ITEMS:
        return None, f"items supports at most {_MAX_ITEMS} pages per task."

    normalized: list[dict[str, str]] = []
    for item in parsed:
        if not isinstance(item, dict):
            return None, "Each item must include string targetPageSlug and context fields."
        slug = item.get("targetPageSlug")
        if slug is None:
            slug = item.get("target_page_slug")
        context = item.get("context")
        if not isinstance(slug, str) or not isinstance(context, str):
            return None, "Each item must include string targetPageSlug and context fields."
        normalized.append({"targetPageSlug": slug, "context": context})

    return normalized, None


# --- Input schemas (args_schema for each @tool) ----------------------------


class CreateTaskInput(BaseModel):
    api_key: str = Field(description="Flint API key (provided by credential system)")
    site_id: str = Field(description="ID (UUID) of the Flint site the agent should modify")
    prompt: str = Field(
        description=(
            "Natural-language instructions for the agent "
            '(e.g. "Add a new About page with a team section")'
        )
    )
    callback_url: str | None = Field(
        default=None,
        description=(
            "HTTPS webhook URL that Flint POSTs to when the task completes or "
            "fails. Private/internal addresses are rejected by Flint."
        ),
    )
    publish: bool | None = Field(
        default=None,
        description=(
            "Whether to automatically publish the changes when the task completes. "
            "Omit to keep Flint's own default."
        ),
    )


class GeneratePagesInput(BaseModel):
    api_key: str = Field(description="Flint API key (provided by credential system)")
    site_id: str = Field(description="ID (UUID) of the Flint site the agent should modify")
    template_page_slug: str = Field(
        description=(
            "Slug of the existing template page to generate from "
            "(e.g. /case-studies/template)"
        )
    )
    items: list[dict[str, Any]] | str = Field(
        description=(
            "Array of 1-10 pages to generate. Each item requires targetPageSlug "
            "(slug for the new page, e.g. /case-studies/acme-corp) and context "
            "(content details the agent should use to fill in the template). "
            "May also be supplied as a JSON string."
        )
    )
    callback_url: str | None = Field(
        default=None,
        description=(
            "HTTPS webhook URL that Flint POSTs to when the task completes or "
            "fails. Private/internal addresses are rejected by Flint."
        ),
    )
    publish: bool | None = Field(
        default=None,
        description=(
            "Whether to automatically publish the generated pages when the task "
            "completes. Omit to keep Flint's own default."
        ),
    )


class GetTaskInput(BaseModel):
    api_key: str = Field(description="Flint API key (provided by credential system)")
    task_id: str = Field(
        description="Identifier of the task returned when it was created (e.g. bg-...)"
    )


# --- Task actions ----------------------------------------------------------


@tool(args_schema=CreateTaskInput)
@serialize_pydantic_return
async def create_task(
    api_key: str,
    site_id: str,
    prompt: str,
    callback_url: str | None = None,
    publish: bool | None = None,
) -> CreateTaskOutput:
    """Start a background Flint agent task that modifies a site from a prompt."""
    if not api_key or not api_key.strip():
        return CreateTaskOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"siteId": site_id, "prompt": prompt}
    if callback_url:
        body["callbackUrl"] = callback_url
    if publish is not None:
        body["publish"] = publish

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/agent/tasks", headers=_headers(api_key), json=body
            )
        if not _ok(response):
            return CreateTaskOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return CreateTaskOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateTaskOutput(success=False, error=f"Create task failed: {exc}")

    task_id = _as_str(data.get("taskId"))
    if not task_id:
        return CreateTaskOutput(success=False, error=_missing_task_id_error(data))

    return CreateTaskOutput(
        success=True,
        task_id=task_id,
        status=_as_str(data.get("status")),
        created_at=_as_str(data.get("createdAt")),
    )


@tool(args_schema=GeneratePagesInput)
@serialize_pydantic_return
async def generate_pages(
    api_key: str,
    site_id: str,
    template_page_slug: str,
    items: list[dict[str, Any]] | str,
    callback_url: str | None = None,
    publish: bool | None = None,
) -> GeneratePagesOutput:
    """Start a background Flint agent task that generates up to 10 pages from a template."""
    if not api_key or not api_key.strip():
        return GeneratePagesOutput(success=False, error=_EMPTY_KEY_ERROR)

    parsed_items, items_error = _parse_items(items)
    if parsed_items is None:
        return GeneratePagesOutput(success=False, error=items_error)

    body: dict[str, Any] = {
        "siteId": site_id,
        "command": "generate_pages",
        "templatePageSlug": template_page_slug,
        "items": parsed_items,
    }
    if callback_url:
        body["callbackUrl"] = callback_url
    if publish is not None:
        body["publish"] = publish

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/agent/tasks", headers=_headers(api_key), json=body
            )
        if not _ok(response):
            return GeneratePagesOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return GeneratePagesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GeneratePagesOutput(success=False, error=f"Generate pages failed: {exc}")

    task_id = _as_str(data.get("taskId"))
    if not task_id:
        return GeneratePagesOutput(success=False, error=_missing_task_id_error(data))

    return GeneratePagesOutput(
        success=True,
        task_id=task_id,
        status=_as_str(data.get("status")),
        created_at=_as_str(data.get("createdAt")),
    )


@tool(args_schema=GetTaskInput)
@serialize_pydantic_return
async def get_task(api_key: str, task_id: str) -> GetTaskOutput:
    """Get the status and results of a background Flint agent task."""
    if not api_key or not api_key.strip():
        return GetTaskOutput(success=False, error=_EMPTY_KEY_ERROR)

    resolved_id = quote(task_id.strip(), safe="")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/agent/tasks/{resolved_id}", headers=_headers(api_key)
            )
        if not _ok(response):
            return GetTaskOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return GetTaskOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetTaskOutput(success=False, error=f"Get task failed: {exc}")

    returned_id = _as_str(data.get("taskId"))
    if not returned_id:
        return GetTaskOutput(success=False, error=_missing_task_id_error(data))

    output = _as_dict(data.get("output"))

    return GetTaskOutput(
        success=True,
        task_id=returned_id,
        status=_as_str(data.get("status")),
        pages_created=[_task_page(item) for item in _as_dicts(output.get("pagesCreated"))],
        pages_modified=[_task_page(item) for item in _as_dicts(output.get("pagesModified"))],
        pages_deleted=[_task_page(item) for item in _as_dicts(output.get("pagesDeleted"))],
        error_message=_as_str(data.get("errorMessage")),
    )
