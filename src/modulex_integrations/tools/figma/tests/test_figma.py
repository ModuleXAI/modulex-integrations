"""Happy-path tests for every figma @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.figma import (
    TOOLS,
    delete_comment,
    list_comments,
    manifest,
    post_a_comment,
)
from modulex_integrations.tools.figma.outputs import (
    DeleteCommentOutput,
    ListCommentsOutput,
    PostACommentOutput,
)

API = "https://api.figma.com"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_list_comments(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/v1/files/ABC123/comments",
        json={
            "comments": [
                {
                    "id": "101",
                    "file_key": "ABC123",
                    "parent_id": None,
                    "user": {
                        "handle": "Alice",
                        "img_url": "https://img.example.com/a.png",
                        "id": "1",
                    },
                    "created_at": "2024-01-15T10:00:00Z",
                    "resolved_at": None,
                    "message": "Looks great!",
                    "order_id": "1",
                },
            ],
        },
    )

    result_dict = await list_comments.ainvoke(_args(file_id="ABC123"))

    assert isinstance(result_dict, dict)
    result = ListCommentsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.comments) == 1
    assert result.comments[0].message == "Looks great!"
    assert result.comments[0].user is not None
    assert result.comments[0].user.handle == "Alice"


@pytest.mark.asyncio
async def test_delete_comment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/v1/files/ABC123/comments/101",
        json={},
    )

    result_dict = await delete_comment.ainvoke(_args(file_id="ABC123", comment_id="101"))

    assert isinstance(result_dict, dict)
    result = DeleteCommentOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_post_a_comment(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/v1/files/ABC123/comments",
        json={
            "id": "202",
            "file_key": "ABC123",
            "parent_id": None,
            "user": {"handle": "Bob", "img_url": "https://img.example.com/b.png", "id": "2"},
            "created_at": "2024-01-16T12:00:00Z",
            "resolved_at": None,
            "message": "Nice work!",
            "order_id": "2",
        },
    )

    result_dict = await post_a_comment.ainvoke(_args(file_id="ABC123", message="Nice work!"))

    assert isinstance(result_dict, dict)
    result = PostACommentOutput.model_validate(result_dict)
    assert result.success is True
    assert result.comment is not None
    assert result.comment.id == "202"
    assert result.comment.message == "Nice work!"


# --- Failure-path test (empty credential) -----------------------------------


@pytest.mark.asyncio
async def test_list_comments_empty_credential():  # type: ignore[no-untyped-def]
    """Tool returns error when access_token is missing."""
    result_dict = await list_comments.ainvoke(
        {"auth_type": "oauth2", "auth_data": {}, "file_id": "ABC123"}
    )
    assert isinstance(result_dict, dict)
    result = ListCommentsOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error
