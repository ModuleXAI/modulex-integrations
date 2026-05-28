"""Happy-path tests for every product_hunt @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.product_hunt import (
    TOOLS,
    list_topic_options,
    manifest,
)
from modulex_integrations.tools.product_hunt.outputs import (
    ListTopicOptionsOutput,
)

API = "https://api.producthunt.com/v2/api/graphql"

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
async def test_list_topic_options(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=API,
        json={
            # TODO: fill in a representative response shape from the upstream API docs
            "data": {
                "topics": {
                    "edges": [
                        {"node": {"name": "Artificial Intelligence",
                                  "slug": "artificial-intelligence"}},
                        {"node": {"name": "Developer Tools",
                                  "slug": "developer-tools"}},
                    ]
                }
            }
        },
    )

    result_dict = await list_topic_options.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListTopicOptionsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.topics) == 2
    assert result.topics[0].value == "artificial-intelligence"
    assert result.topics[0].label == "Artificial Intelligence"
