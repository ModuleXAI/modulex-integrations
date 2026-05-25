"""Happy-path tests for every heroku @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.heroku import (
    TOOLS,
    list_apps,
    manifest,
)
from modulex_integrations.tools.heroku.outputs import (
    ListAppsOutput,
)

API = "https://api.heroku.com"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
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
async def test_list_apps(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/apps",
        json=[
            {
                "id": "01234567-89ab-cdef-0123-456789abcdef",
                "name": "my-app",
                "web_url": "https://my-app.herokuapp.com/",
                "region": {"id": "us", "name": "us"},
                "stack": {"id": "heroku-22", "name": "heroku-22"},
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-06-15T12:00:00Z",
            },
        ],
    )

    result_dict = await list_apps.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListAppsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.apps) == 1
    assert result.apps[0].name == "my-app"
    assert result.apps[0].id == "01234567-89ab-cdef-0123-456789abcdef"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"
