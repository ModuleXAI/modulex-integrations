"""Tests for the Gmail integration."""
from __future__ import annotations

import base64
from typing import Any

import pytest

from modulex_integrations.tools.gmail import (
    TOOLS,
    list_labels,
    manifest,
    send_message,
)
from modulex_integrations.tools.gmail.outputs import (
    ListLabelsOutput,
    SendMessageOutput,
)

API = "https://www.googleapis.com/gmail/v1"

_OAUTH_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "gmail-oauth-token"},
}
_PAT_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "gmail-pat-token"},
}


def _args(auth: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return dict(auth, **extra)


class TestManifest:
    def test_manifest_exposes_two_actions(self) -> None:
        assert len(manifest.actions) == 2

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_and_bearer_token_auth(self) -> None:
        types = {a.auth_type for a in manifest.auth_schemas}
        assert types == {"oauth2", "bearer_token"}

    def test_oauth_config_carries_two_gmail_scopes(self) -> None:
        oauth = next(a for a in manifest.auth_schemas if a.auth_type == "oauth2")
        assert len(oauth.oauth_config.scopes) == 2
        assert "https://www.googleapis.com/auth/gmail.send" in oauth.oauth_config.scopes
        assert "https://www.googleapis.com/auth/gmail.labels" in oauth.oauth_config.scopes


@pytest.mark.asyncio
async def test_send_message_oauth(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json
        captured.update(json.loads(request.content.decode()))
        from httpx import Response
        return Response(
            200,
            json={"id": "M1", "threadId": "T1", "labelIds": ["SENT"]},
        )

    httpx_mock.add_callback(
        _capture, method="POST", url=f"{API}/users/me/messages/send"
    )
    result = SendMessageOutput.model_validate(
        await send_message.ainvoke(
            _args(_OAUTH_AUTH, to="x@y.io", subject="Hi", body="Hello")
        )
    )
    assert result.success is True
    assert result.id == "M1"
    # The raw field is base64url-encoded MIME bytes that include "Hello".
    decoded = base64.urlsafe_b64decode(captured["raw"]).decode("utf-8")
    assert "Hello" in decoded
    assert "to: x@y.io" in decoded
    assert "subject: Hi" in decoded


@pytest.mark.asyncio
async def test_send_message_bearer(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/me/messages/send",
        json={"id": "M1", "threadId": "T1", "labelIds": ["SENT"]},
    )
    result = SendMessageOutput.model_validate(
        await send_message.ainvoke(
            _args(_PAT_AUTH, to="x@y.io", subject="Hi", body="Hi")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_send_message_validates_missing_token() -> None:
    bad = {"auth_type": "oauth2", "auth_data": {}}
    result = SendMessageOutput.model_validate(
        await send_message.ainvoke(
            dict(bad, to="x@y.io", subject="Hi", body="Hi")
        )
    )
    assert result.success is False
    assert result.error is not None and "access token" in result.error


@pytest.mark.asyncio
async def test_list_labels(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me/labels",
        json={
            "labels": [
                {"id": "INBOX", "name": "INBOX", "type": "system"},
                {"id": "L1", "name": "My Label", "type": "user"},
            ]
        },
    )
    result = ListLabelsOutput.model_validate(
        await list_labels.ainvoke(_args(_OAUTH_AUTH))
    )
    assert result.success is True
    assert result.total == 2
