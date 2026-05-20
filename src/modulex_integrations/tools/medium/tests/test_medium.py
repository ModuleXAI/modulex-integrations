"""Happy-path tests for every medium @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.medium import (
    TOOLS,
    create_post,
    manifest,
)
from modulex_integrations.tools.medium.outputs import (
    CreatePostOutput,
)

API = "https://api.medium.com/v1"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token", "oauth_uid": "fake_user_id"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_1_action(self) -> None:
        assert len(manifest.actions) == 1

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_post(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/fake_user_id/posts",
        json={
            "data": {
                "id": "post-123",
                "title": "My Test Post",
                "authorId": "fake_user_id",
                "url": "https://medium.com/@user/my-test-post-abc123",
                "canonicalUrl": "",
                "publishStatus": "public",
                "publishedAt": 1716000000000,
                "license": "all-rights-reserved",
                "licenseUrl": "https://policy.medium.com/medium-terms-of-service-9db0094a1e0f",
                "tags": ["test", "automation"],
            },
        },
    )

    result_dict = await create_post.ainvoke(
        _args(
            title="My Test Post",
            content_format="markdown",
            content="# My Test Post\n\nHello world.",
        )
    )

    assert isinstance(result_dict, dict)
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "post-123"
    assert result.title == "My Test Post"
    assert result.url == "https://medium.com/@user/my-test-post-abc123"
    assert result.tags == ["test", "automation"]

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


# --- Failure-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_create_post_missing_credentials() -> None:
    """Empty access_token should return success=False without hitting the wire."""
    result_dict = await create_post.ainvoke(
        _args(
            auth_data={"access_token": "", "oauth_uid": ""},
            title="Should Fail",
            content_format="markdown",
            content="# Nope",
        )
    )
    assert isinstance(result_dict, dict)
    result = CreatePostOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
