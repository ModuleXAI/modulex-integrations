"""Tests for the Flint integration.

One happy-path test per action (3), plus failure-path tests for the
non-2xx -> success=False branch, the 2xx-without-taskId branch, the
local ``items`` validation, and an empty-credential test (the API key
guard short-circuits before any HTTP call).
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from modulex_integrations.tools.flint import (
    TOOLS,
    create_task,
    generate_pages,
    get_task,
    manifest,
)
from modulex_integrations.tools.flint.outputs import (
    CreateTaskOutput,
    GeneratePagesOutput,
    GetTaskOutput,
)

API = "https://app.tryflint.com/api/v1"
_API_KEY = "ak_fake_key"
_TASK_ID = "bg-550e8400-e29b-41d4-a716-446655440000-a1b2c3d4"

_CREATED = {
    "taskId": _TASK_ID,
    "status": "running",
    "createdAt": "2026-03-11T12:00:00.000Z",
}

_PAGE = {
    "slug": "/about",
    "previewUrl": "https://your-site-abc123.vercel.app/about",
    "editUrl": "https://app.tryflint.com/app/edit?siteId=site_1&page=about",
    "publishedUrl": "https://yourdomain.com/about",
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest ---------------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}


# --- Happy paths ------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_task(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/agent/tasks",
        json=_CREATED,
    )

    result_dict = await create_task.ainvoke(
        _args(
            site_id="550e8400-e29b-41d4-a716-446655440000",
            prompt="Add a new About page with a team section",
            callback_url="https://your-server.com/webhooks/flint",
            publish=False,
        )
    )
    assert isinstance(result_dict, dict)
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task_id == _TASK_ID
    assert result.status == "running"
    assert result.created_at == "2026-03-11T12:00:00.000Z"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"
    body = json.loads(sent.content)
    assert body == {
        "siteId": "550e8400-e29b-41d4-a716-446655440000",
        "prompt": "Add a new About page with a team section",
        "callbackUrl": "https://your-server.com/webhooks/flint",
        # an explicit false must survive, not be dropped as falsy
        "publish": False,
    }


@pytest.mark.asyncio
async def test_create_task_omits_unset_optionals(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/agent/tasks", json=_CREATED)

    result_dict = await create_task.ainvoke(_args(site_id="site_1", prompt="Refresh copy"))
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is True

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {"siteId": "site_1", "prompt": "Refresh copy"}


@pytest.mark.asyncio
async def test_generate_pages(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/agent/tasks", json=_CREATED)

    result_dict = await generate_pages.ainvoke(
        _args(
            site_id="site_1",
            template_page_slug="/case-studies/template",
            items=[
                {
                    "targetPageSlug": "/case-studies/acme-corp",
                    "context": "Company: Acme Corp. Industry: Manufacturing.",
                }
            ],
            publish=True,
        )
    )
    assert isinstance(result_dict, dict)
    result = GeneratePagesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task_id == _TASK_ID
    assert result.status == "running"

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body == {
        "siteId": "site_1",
        "command": "generate_pages",
        "templatePageSlug": "/case-studies/template",
        "items": [
            {
                "targetPageSlug": "/case-studies/acme-corp",
                "context": "Company: Acme Corp. Industry: Manufacturing.",
            }
        ],
        "publish": True,
    }


@pytest.mark.asyncio
async def test_generate_pages_accepts_json_string_items(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/agent/tasks", json=_CREATED)

    result_dict = await generate_pages.ainvoke(
        _args(
            site_id="site_1",
            template_page_slug="/case-studies/template",
            items=json.dumps(
                [{"target_page_slug": "/case-studies/beta", "context": "Beta Inc."}]
            ),
        )
    )
    result = GeneratePagesOutput.model_validate(result_dict)
    assert result.success is True

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["items"] == [
        {"targetPageSlug": "/case-studies/beta", "context": "Beta Inc."}
    ]


@pytest.mark.asyncio
async def test_get_task_completed(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/agent/tasks/{_TASK_ID}",
        json={
            "taskId": _TASK_ID,
            "status": "completed",
            "output": {
                "pagesCreated": [_PAGE],
                "pagesModified": [],
                "pagesDeleted": [],
            },
        },
    )

    result_dict = await get_task.ainvoke(_args(task_id=f" {_TASK_ID} "))
    assert isinstance(result_dict, dict)
    result = GetTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.task_id == _TASK_ID
    assert result.status == "completed"
    assert len(result.pages_created) == 1
    assert result.pages_created[0].slug == "/about"
    assert result.pages_created[0].preview_url == _PAGE["previewUrl"]
    assert result.pages_created[0].edit_url == _PAGE["editUrl"]
    assert result.pages_created[0].published_url == _PAGE["publishedUrl"]
    assert result.pages_modified == []
    assert result.pages_deleted == []
    assert result.error_message is None


@pytest.mark.asyncio
async def test_get_task_running_has_no_output_block(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/agent/tasks/{_TASK_ID}",
        json={"taskId": _TASK_ID, "status": "running"},
    )

    result_dict = await get_task.ainvoke(_args(task_id=_TASK_ID))
    result = GetTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.status == "running"
    assert result.pages_created == []


@pytest.mark.asyncio
async def test_get_task_failed_exposes_error_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/agent/tasks/{_TASK_ID}",
        json={
            "taskId": _TASK_ID,
            "status": "failed",
            "errorMessage": "Failed to generate page content",
        },
    )

    result_dict = await get_task.ainvoke(_args(task_id=_TASK_ID))
    result = GetTaskOutput.model_validate(result_dict)
    # A failed *task* is still a successful API read.
    assert result.success is True
    assert result.status == "failed"
    assert result.error_message == "Failed to generate page content"


# --- Failure paths ----------------------------------------------------------


@pytest.mark.asyncio
async def test_get_task_not_found_unwraps_error(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/agent/tasks/missing",
        status_code=404,
        json={"error": "Task not found"},
    )

    result_dict = await get_task.ainvoke(_args(task_id="missing"))
    result = GetTaskOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "404" in result.error
    assert "Task not found" in result.error
    assert result.task_id is None


@pytest.mark.asyncio
async def test_create_task_site_not_found(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/agent/tasks",
        status_code=404,
        json={"error": "Site not found"},
    )

    result_dict = await create_task.ainvoke(_args(site_id="nope", prompt="Do a thing"))
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "Site not found" in result.error


@pytest.mark.asyncio
async def test_create_task_2xx_without_task_id(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/agent/tasks", json={"status": "running"})

    result_dict = await create_task.ainvoke(_args(site_id="site_1", prompt="Do a thing"))
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "Flint did not return a task ID"


@pytest.mark.asyncio
async def test_get_task_non_object_body_degrades(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/agent/tasks/{_TASK_ID}",
        json=["unexpected"],
    )

    result_dict = await get_task.ainvoke(_args(task_id=_TASK_ID))
    result = GetTaskOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "Flint did not return a task ID"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("items", "expected"),
    [
        ("not json", "Invalid JSON in items parameter."),
        ([], "items must be a non-empty JSON array"),
        (
            [{"targetPageSlug": "/a", "context": "c"}] * 11,
            "at most 10 pages per task",
        ),
        ([{"targetPageSlug": "/a"}], "string targetPageSlug and context"),
    ],
)
async def test_generate_pages_rejects_bad_items(  # type: ignore[no-untyped-def]
    httpx_mock, items: Any, expected: str
) -> None:
    result_dict = await generate_pages.ainvoke(
        _args(site_id="site_1", template_page_slug="/t", items=items)
    )
    result = GeneratePagesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert expected in result.error
    assert httpx_mock.get_requests() == []


# --- Empty-credential guard -------------------------------------------------


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await create_task.ainvoke(
        {"api_key": "   ", "site_id": "site_1", "prompt": "Do a thing"}
    )
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error
    assert httpx_mock.get_requests() == []


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits_get_task(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await get_task.ainvoke({"api_key": "", "task_id": _TASK_ID})
    result = GetTaskOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error
    assert httpx_mock.get_requests() == []


# --- Type-confused 2xx bodies ------------------------------------------------


@pytest.mark.asyncio
async def test_get_task_type_confused_body_degrades(httpx_mock):  # type: ignore[no-untyped-def]
    """A 200 whose fields carry the wrong JSON type must not raise past @tool."""
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/agent/tasks/{_TASK_ID}",
        json={
            "taskId": _TASK_ID,
            "status": "completed",
            "errorMessage": {"nested": "object"},
            "output": {"pagesCreated": [{"slug": 7, "previewUrl": None}]},
        },
    )

    result_dict = await get_task.ainvoke(_args(task_id=_TASK_ID))
    assert isinstance(result_dict, dict)
    result = GetTaskOutput.model_validate(result_dict)
    assert result.success is True
    assert result.error_message is None
    assert result.pages_created[0].slug is None


@pytest.mark.asyncio
async def test_create_task_non_string_task_id_degrades(httpx_mock):  # type: ignore[no-untyped-def]
    """A non-string taskId is treated as "no task id", not a ValidationError."""
    httpx_mock.add_response(method="POST", url=f"{API}/agent/tasks", json={"taskId": 12345})

    result_dict = await create_task.ainvoke(_args(site_id="site_1", prompt="Do a thing"))
    result = CreateTaskOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error == "Flint did not return a task ID"
