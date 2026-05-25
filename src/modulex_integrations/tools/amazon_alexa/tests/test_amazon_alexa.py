"""Happy-path tests for every amazon_alexa @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.amazon_alexa import (
    TOOLS,
    get_simulation_results,
    manifest,
    simulate_skill,
)
from modulex_integrations.tools.amazon_alexa.outputs import (
    GetSimulationResultsOutput,
    SimulateSkillOutput,
)

API = "https://api.amazonalexa.com/v2"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity ----------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_2_actions(self) -> None:
        assert len(manifest.actions) == 2

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests ----------------------------------------------


@pytest.mark.asyncio
async def test_simulate_skill(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/skills/amzn1.ask.skill.abc123/stages/development/simulations",
        json={
            # TODO: fill in a representative response shape from the upstream Alexa SMAPI docs
            "id": "sim-12345",
            "status": "IN_PROGRESS",
        },
    )

    result_dict = await simulate_skill.ainvoke(
        _args(
            skill_id="amzn1.ask.skill.abc123",
            stage="development",
            content="open my skill",
            locale="en-US",
        )
    )

    assert isinstance(result_dict, dict)
    result = SimulateSkillOutput.model_validate(result_dict)
    assert result.success is True
    assert result.simulation_id == "sim-12345"
    assert result.status == "IN_PROGRESS"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


@pytest.mark.asyncio
async def test_get_simulation_results(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/skills/amzn1.ask.skill.abc123/stages/development/simulations/sim-12345",
        json={
            # TODO: fill in a representative response shape from the upstream Alexa SMAPI docs
            "id": "sim-12345",
            "status": "SUCCESSFUL",
            "result": {
                "alexaExecutionInfo": {"alexaResponses": [{"type": "Speech", "content": {"caption": "Hello!"}}]},
            },
        },
    )

    result_dict = await get_simulation_results.ainvoke(
        _args(
            skill_id="amzn1.ask.skill.abc123",
            stage="development",
            simulation_id="sim-12345",
        )
    )

    assert isinstance(result_dict, dict)
    result = GetSimulationResultsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.simulation_id == "sim-12345"
    assert result.status == "SUCCESSFUL"
    assert result.result is not None

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == "Bearer fake_access_token"


# --- Failure-path tests -------------------------------------------------------


@pytest.mark.asyncio
async def test_simulate_skill_missing_token():  # type: ignore[no-untyped-def]
    """Empty access_token returns success=False without hitting the network."""
    result_dict = await simulate_skill.ainvoke(
        _args(auth_data={}, skill_id="fake", stage="development", content="hello")
    )
    assert isinstance(result_dict, dict)
    result = SimulateSkillOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
